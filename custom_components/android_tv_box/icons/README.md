# Icons Directory

This directory contains the icon resources for the Android TV Box integration.

## Files

- `icon.svg` - Vector icon in SVG format (512x512 viewBox)
- `icon.png` - Raster icon in PNG format (512x512 pixels) - **To be generated**
- `icon@2x.png` - High-resolution icon (1024x1024 pixels) - **To be generated**

## Converting SVG to PNG

To convert the SVG icon to PNG format for better compatibility:

### Method 1: Online Converter
1. Visit [svgtopng.com](https://www.svgtopng.com/)
2. Upload `icon.svg`
3. Set dimensions to 512x512
4. Download and save as `icon.png`
5. Repeat with 1024x1024 for `icon@2x.png`

### Method 2: Command Line (Inkscape)
```bash
# Install Inkscape if not available
# Ubuntu/Debian: sudo apt install inkscape
# macOS: brew install inkscape

# Generate 512x512 PNG
inkscape --export-png=icon.png --export-width=512 --export-height=512 icon.svg

# Generate 1024x1024 PNG
inkscape --export-png=icon@2x.png --export-width=1024 --export-height=1024 icon.svg
```

### Method 3: ImageMagick
```bash
# Install ImageMagick if not available
# Ubuntu/Debian: sudo apt install imagemagick
# macOS: brew install imagemagick

# Generate PNGs
convert -density 300 -background transparent icon.svg -resize 512x512 icon.png
convert -density 300 -background transparent icon.svg -resize 1024x1024 icon@2x.png
```

## Icon Design

The icon features:
- **Android TV Box** - Dark rectangular device with rounded corners
- **Android Logo** - Green Android mascot on the device
- **Remote Control** - Small remote control to indicate TV functionality
- **ADB Symbol** - Red "ADB" badge indicating debug capabilities
- **WiFi Signal** - Blue WiFi symbol for connectivity
- **Connection Ports** - Visual ports on the device

## Color Scheme

- **Device Body**: Dark gray (#2D3748)
- **Android Logo**: Android green (#3DDC84)  
- **ADB Badge**: Red (#FF6B6B)
- **WiFi Signal**: Teal (#38B2AC)
- **Accents**: Various grays for depth

## Usage

Once generated, the PNG files will be automatically used by Home Assistant for:
- Integration icons in HACS
- Device icons in the device registry
- Entity icons in the UI (fallback)