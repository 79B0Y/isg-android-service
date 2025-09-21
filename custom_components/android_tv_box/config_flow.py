"""Config flow for Android TV Box integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .adb_manager import ADBManager
from .const import (
    CONF_DEVICE_NAME,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(CONF_DEVICE_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    device_name = data[CONF_DEVICE_NAME]

    _LOGGER.info("Validating ADB connection to %s:%s", host, port)
    
    # Increase timeout for initial connection
    adb_manager = ADBManager(host, port, timeout=30)
    
    try:
        # Perform comprehensive connection test
        connection_test = await adb_manager.test_adb_connection()
        
        _LOGGER.info("Connection test result: %s", connection_test)
        
        if not connection_test["connected"]:
            error_details = connection_test.get("error", "Unknown connection error")
            connection_details = connection_test.get("connection_details", {})
            
            # Provide specific error messages based on the failure type
            if "timeout" in error_details.lower():
                raise ConnectionError(f"Connection timeout after 30 seconds. Device may be unreachable or ADB not enabled. Details: {error_details}")
            elif "refused" in error_details.lower():
                raise ConnectionError(f"Connection refused by device. Check if ADB debugging is enabled and port {port} is accessible. Details: {error_details}")
            elif "network" in error_details.lower():
                raise ConnectionError(f"Network error. Check if device IP {host} is correct and reachable. Details: {error_details}")
            else:
                raise ConnectionError(f"ADB connection failed: {error_details}. Connection details: {connection_details}")
        
        # Get device info to create a unique identifier
        device_info = connection_test.get("device_info", {})
        device_model = device_info.get("model", "Unknown")
        android_version = device_info.get("android_version", "Unknown")
        
        _LOGGER.info("Successfully validated ADB connection. Device: %s (Android %s)", device_model, android_version)
        
        return {
            "title": device_name,
            "host": host,
            "port": port,
            "device_name": device_name,
            "device_model": device_model,
            "android_version": android_version,
        }
        
    except ConnectionError:
        # Re-raise connection errors with original message
        raise
    except asyncio.TimeoutError:
        raise ConnectionError("Connection timeout after 30 seconds - device may be unreachable or ADB service not running")
    except Exception as e:
        error_msg = f"Unexpected error during validation: {str(e)} (Type: {type(e).__name__})"
        _LOGGER.error(error_msg)
        raise ConnectionError(error_msg)
    finally:
        # Always cleanup
        try:
            await adb_manager.disconnect()
        except Exception as cleanup_error:
            _LOGGER.warning("Error during cleanup: %s", cleanup_error)


class AndroidTVBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Android TV Box."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except ConnectionError as e:
            error_str = str(e).lower()
            _LOGGER.error("Connection error during setup: %s", e)
            
            if "timeout" in error_str:
                errors["base"] = "timeout"
            elif "refused" in error_str or "unreachable" in error_str:
                errors["base"] = "cannot_connect" 
            elif "network" in error_str:
                errors["base"] = "cannot_connect"
            elif "adb" in error_str and "not enabled" in error_str:
                errors["base"] = "adb_not_enabled"
            else:
                errors["base"] = "cannot_connect"
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception during setup: %s", e)
            errors["base"] = "unknown"
        else:
            # Create unique ID based on host:port
            unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, user_input: Dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(user_input)


class AndroidTVBoxOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Android TV Box."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DEVICE_NAME,
                        default=self.config_entry.options.get(
                            CONF_DEVICE_NAME, 
                            self.config_entry.data.get(CONF_DEVICE_NAME, DEFAULT_NAME)
                        ),
                    ): cv.string,
                }
            ),
        )