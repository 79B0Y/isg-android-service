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

    adb_manager = ADBManager(host, port)
    
    # Test connection
    try:
        connected = await adb_manager.connect()
        if not connected:
            raise ConnectionError("Failed to establish ADB connection")
        
        # Get device information for validation
        connection_test = await adb_manager.test_adb_connection()
        
        if not connection_test["connected"]:
            error_msg = connection_test.get("error", "Unknown connection error")
            raise ConnectionError(f"ADB connection test failed: {error_msg}")
        
        # Get device info to create a unique identifier
        device_info = connection_test.get("device_info", {})
        device_model = device_info.get("model", "Unknown")
        android_version = device_info.get("android_version", "Unknown")
        
        await adb_manager.disconnect()
        
        return {
            "title": device_name,
            "host": host,
            "port": port,
            "device_name": device_name,
            "device_model": device_model,
            "android_version": android_version,
        }
        
    except asyncio.TimeoutError:
        raise ConnectionError("Connection timeout - device may be unreachable")
    except Exception as e:
        _LOGGER.error("Validation error: %s", e)
        raise ConnectionError(f"Failed to connect: {str(e)}")
    finally:
        await adb_manager.disconnect()


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
            _LOGGER.error("Connection error: %s", e)
            if "timeout" in str(e).lower():
                errors["base"] = "timeout"
            elif "unreachable" in str(e).lower():
                errors["base"] = "cannot_connect"
            else:
                errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
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