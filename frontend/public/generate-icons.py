"""
Script to generate PWA icons for CryptoBot
This creates simple but professional icons with the Bitcoin symbol
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#0f172a')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background circles
    center = size // 2
    
    # Purple gradient circle
    for i in range(10):
        radius = int(center * (1 - i * 0.08))
        color_val = 124 + i * 13  # Gradient from purple to lighter
        color = (color_val, 58 + i * 10, 237)
        draw.ellipse(
            [center - radius, center - radius, center + radius, center + radius],
            fill=color
        )
    
    # Draw Bitcoin symbol
    try:
        # Try to use a system font, fallback to default
        font_size = int(size * 0.5)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Bitcoin symbol
        text = "₿"
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (size - text_width) // 2 - bbox[0]
        y = (size - text_height) // 2 - bbox[1]
        
        # Draw text with shadow
        shadow_offset = max(2, size // 100)
        draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 128), font=font)
        draw.text((x, y), text, fill=(255, 215, 0), font=font)  # Gold color
    except Exception as e:
        print(f"Could not add text: {e}")
        # If font fails, just draw a circle
        draw.ellipse(
            [center - size//4, center - size//4, center + size//4, center + size//4],
            fill=(255, 215, 0)
        )
    
    # Save the image
    img.save(filename, 'PNG', quality=100)
    print(f"Created {filename}")

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create icons
    create_icon(192, os.path.join(script_dir, 'icon-192.png'))
    create_icon(512, os.path.join(script_dir, 'icon-512.png'))
    create_icon(180, os.path.join(script_dir, 'apple-touch-icon.png'))  # iOS specific
    create_icon(32, os.path.join(script_dir, 'favicon.ico'))
    
    print("\nAll icons created successfully!")
    print("If you see any errors above, you may need to install Pillow:")
    print("  pip install Pillow")

if __name__ == '__main__':
    main()

