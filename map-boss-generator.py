import sys
import os
import re
from PIL import Image, ImageFilter

class ImageProcessor:
    def __init__(self):
        self.canvas = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        self.canvas_glow = None
        self.canvas_shadow = None

    def draw_glow(self, alpha=255):
        # Draw the blue glow around the ship
        self.canvas_glow = self.canvas.copy()
        for _ in range(8):
            self.canvas_glow = self.canvas_glow.filter(ImageFilter.BoxBlur(1.05))
        for x in range(self.canvas_glow.size[0]):
            for y in range(self.canvas_glow.size[1]):
                pixel = self.canvas_glow.getpixel((x, y))
                if pixel[3] > 0:
                    self.canvas_glow.putpixel((x, y), (255, 28, 28) + (int(1.08*pixel[3]),))

    def draw_shadow(self, alpha=255):
        # Draw the blue glow around the ship
        self.canvas_shadow = self.canvas.copy()
        for _ in range(8):
            self.canvas_shadow = self.canvas_shadow.filter(ImageFilter.BoxBlur(0.4))
        for x in range(self.canvas_shadow.size[0]):
            for y in range(self.canvas_shadow.size[1]):
                pixel = self.canvas_shadow.getpixel((x, y))
                if pixel[3] > 0:
                    self.canvas_shadow.putpixel((x, y), (0, 0, 0) + (int(0.8*pixel[3]),))
    
    def save_images(self, output_path):
        # Save normal image
        normal = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        normal.alpha_composite(self.canvas_shadow, dest=(-3, 4), source=(0, 0))
        normal.alpha_composite(self.canvas_glow)
        normal.alpha_composite(self.canvas)
        normal.save(output_path)

# Generate map icon
path = sys.argv[1]
processor = ImageProcessor()
processor.canvas = Image.open(path).convert('RGBA')
processor.draw_glow()
processor.draw_shadow()
processor.save_images(path)
