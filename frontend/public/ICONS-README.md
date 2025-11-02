# PWA Icons for CryptoBot

## How to Generate Icons

### Option 1: Using Python Script (Recommended)

1. Install Pillow (if not already installed):
   ```bash
   pip install Pillow
   ```

2. Run the icon generator:
   ```bash
   cd frontend/public
   python generate-icons.py
   ```

This will create:
- `icon-192.png` - Standard PWA icon (192x192)
- `icon-512.png` - High-res PWA icon (512x512)
- `apple-touch-icon.png` - iOS home screen icon (180x180)
- `favicon.ico` - Browser tab icon (32x32)

### Option 2: Manual Creation

If you prefer to create your own icons:

1. Create a square image with your design
2. Export in these sizes:
   - 192x192 pixels → save as `icon-192.png`
   - 512x512 pixels → save as `icon-512.png`
   - 180x180 pixels → save as `apple-touch-icon.png`
   - 32x32 pixels → save as `favicon.ico`

### Option 3: Online Tools

Use online PWA icon generators:
- https://www.pwabuilder.com/imageGenerator
- https://realfavicongenerator.net/

Upload your logo and download the generated icons.

## Icon Guidelines

- Use simple, recognizable designs
- Ensure good contrast
- Make it look good at small sizes
- Use your brand colors
- Square format (1:1 ratio)
- PNG format for transparency support

## Current Design

The default icons feature:
- Purple gradient background (brand color: #7c3aed)
- Gold Bitcoin symbol (₿)
- Professional look suitable for finance apps

