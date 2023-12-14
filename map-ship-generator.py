import sys
import os
import re
from PIL import Image, ImageFilter

class ImageProcessor:
    def __init__(self, input_path):
        self.img = Image.open(input_path)
        self.canvas = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        self.canvas_glow = None
        self.canvas_shadow = None
        self.canvas_red = Image.open('map_ship_res/fuel_glow.png').convert('RGBA')

    def rotate_and_crop_source(self):
        # Rotate the original 90 degrees and crop the transparent edges
        self.img = self.img.rotate(90, expand=True)
        nonwhite_positions = [(x, y) for x in range(self.img.size[0]) for y in range(self.img.size[1]) if self.img.getdata()[x + y*self.img.size[0]][3] > 50]
        rect = (min([x for x, y in nonwhite_positions]), min([y for x, y in nonwhite_positions]), max([x for x, y in nonwhite_positions]) + 1, max([y for x, y in nonwhite_positions]) + 1)
        self.img = self.img.crop(rect)

    def resize_and_paste(self, size=(21, 21)):
        # Downsize the ship
        small = self.img.copy()
        small.thumbnail(size)
        x_offset = (64 - small.width) // 2
        y_offset = (64 - small.height) // 2
        self.canvas.paste(small, (x_offset, y_offset))

    def convert_to_grey(self, alpha=150):
        # Make all opaque pixels one color
        for x in range(64):
            for y in range(64):
                r, g, b, a = self.canvas.getpixel((x, y))
                if a >= alpha:
                    self.canvas.putpixel((x, y), (51, 57, 57, a))

    def remove_alpha_pixels(self):
        # Remove all non-opaque pixels
        for x in range(64):
            for y in range(64):
                r, g, b, a = self.canvas.getpixel((x, y))
                if 1 <= a <= 254:
                    self.canvas.putpixel((x, y), (0, 0, 0, 0))

    def draw_outline(self):
        # Make a copy so changes made arn't read unintentionally
        canvas_outline = self.canvas.copy()
        
        # For checking adjacent pixels
        adj = (0, 1, 0, -1)
        
        # Run on all pixels excepting the outer boarders
        for x in range(self.canvas.size[0]):
            for y in range(self.canvas.size[1]):
                # Check current pixel for alpha of 0
                if (self.canvas.getpixel((x, y))[3] <= 0):
                    for i in range(len(adj)):
                        # Check for an adjacent pixel with alpha above 0
                        xToCheck = x + adj[(i + 1) % len(adj)] 
                        yToCheck = y + adj[i]
                        if 0 <= xToCheck < self.canvas.size[0] and 0 <= yToCheck < self.canvas.size[1]:
                            if (self.canvas.getpixel((xToCheck, yToCheck))[3] > 0):
                                canvas_outline.putpixel((x, y), (234, 245, 229, 255))
                                break
        
        # Assign outlined ship to the main canvas
        self.canvas.close()
        self.canvas = canvas_outline

    def handle_symmetry(self):
        # Check if ship is symmetical
        mismatches = 0
        width = self.img.size[0]
        height = self.img.size[1]
        for x in range(width//2):
            for y in range(height):
                leftside = self.img.getpixel((x, y))
                rightside = self.img.getpixel((width - 1 - x, y))
                if (leftside[3] > 50) != (rightside[3] > 50):
                    mismatches += 1
        pixel_count = (width//2)*height
        symmetry_rating = (pixel_count - mismatches)/pixel_count
        
        # Copy the left half of the canvas to the right half if ship is symmetical
        if symmetry_rating > 0.98:
            for x in range(32):
                for y in range(64):
                    sym = self.canvas.getpixel((x, y))
                    self.canvas.putpixel((63 - x, y), sym)

    def draw_glow(self, alpha=255):
        # Draw the blue glow around the ship
        self.canvas_glow = self.canvas.copy()
        for _ in range(8):
            self.canvas_glow = self.canvas_glow.filter(ImageFilter.BoxBlur(1.05))
        for x in range(self.canvas_glow.size[0]):
            for y in range(self.canvas_glow.size[1]):
                pixel = self.canvas_glow.getpixel((x, y))
                if pixel[3] > 0:
                    self.canvas_glow.putpixel((x, y), (121, 242, 253) + (int(1.08*pixel[3]),))

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
        normal.alpha_composite(self.canvas_shadow, dest=(3, 4), source=(0, 0))
        normal.alpha_composite(self.canvas_glow)
        normal.alpha_composite(self.canvas)
        normal.save(output_path + '.png')
        
        # Save nofuel image
        normal = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        normal.alpha_composite(self.canvas_shadow, dest=(3, 4), source=(0, 0))
        normal.alpha_composite(self.canvas_red)
        normal.alpha_composite(self.canvas)
        normal.save(output_path + '_fuel.png')

# Set input and output folder
path = sys.argv[1]
path_output_data = 'data'
if not os.path.exists(path_output_data):
    os.makedirs(path_output_data)
path_output_img = 'img/map'
if not os.path.exists(path_output_img):
    os.makedirs(path_output_img)
bp_files = ['blueprints.xml.append', 'dlcBlueprints.xml.append']

# Run the process for each ship blueprint
def process_bp_line(bp_file, line):
    bp_name = re.search('name="([_A-Z0-9]+)"', line).group(1)
    img_name = re.search('img="([_a-zA-Z0-9]+)"', line).group(1)
    img_path = path + '/img/ship/' + img_name + "_base.png"
    if os.path.exists(img_path):
        print('Working on:', img_name)
        icon_name = 'map_icon_' + img_name
        
        # Generate map icons
        processor = ImageProcessor(img_path)
        manual_icon_path = 'map_ship_res/' + icon_name + '.png'
        if os.path.exists(manual_icon_path):
            processor.canvas = Image.open(manual_icon_path).convert('RGBA')
        else:
            processor.rotate_and_crop_source()
            processor.resize_and_paste()
            processor.convert_to_grey()
            processor.remove_alpha_pixels()
            processor.draw_outline()
            processor.handle_symmetry()
        processor.draw_glow()
        processor.draw_shadow()
        processor.save_images(path_output_img + '/' + icon_name)
        
        # Write map icons to blueprints
        bp_file.write(f'<mod:findName type="shipBlueprint" name="{bp_name}">\n')
        bp_file.write(f'    <mod-append:mapImage>{icon_name}</mod-append:mapImage>\n')
        bp_file.write('</mod:findName>\n\n')

print('Starting map icon generation')
# Iterate through all lines in the blueprint files
for bp_file in bp_files:
    bp_file_w = open(path_output_data + '/' + bp_file, 'w')
    bp_path = path + '/data/' + bp_file
    if os.path.exists(bp_path):
        with open(bp_path) as bp:
            for line in bp:
                line.strip()
                if line.startswith('<shipBlueprint'):
                    process_bp_line(bp_file_w, line)
    bp_file_w.close()
