import sys
import os
import re
from PIL import Image, ImageFilter

# File setup
path_data = 'data'
path_img = 'img/map'
bp_files = ['blueprints.xml.append', 'dlcBlueprints.xml.append']

# List of sets of duplicates
replace_lists = []

# Check if two images are the same
def images_equal(img1, img2):
    img1 = Image.open(img1).convert('RGBA')
    img2 = Image.open(img2).convert('RGBA')
    for x in range(img1.size[0]):
        for y in range(img1.size[1]):
            if not img1.getpixel((x, y)) == img2.getpixel((x, y)):
                return False
    return True

# Remove all duplicates of an icon
def remove_duplicates(img_name_original, img_path_original):
    remove_list = []
    for file in os.listdir(path_img):
        fname = os.fsdecode(file)
        if not (fname.endswith('_fuel.png') or fname == img_name_original + '.png'):
            img_name = fname[:-4]
            img_path_1 = path_img + '/' + fname
            img_path_2 = path_img + '/' + img_name + '_fuel.png'
            if images_equal(img_path_original, img_path_1):
                remove_list.append(img_name)
                os.remove(img_path_1)
                os.remove(img_path_2)
    return remove_list

# Run through blueprints and remove duplicates for each entry
for bp_file_name in bp_files:
    result = ''
    with open(path_data + '/' + bp_file_name, 'r') as bp_file:
        for line in bp_file:
            r = re.search('<mod-append:mv-mapImage>([_a-zA-Z0-9]+)</mod-append:mv-mapImage>', line)
            if r != None:
                img_name = r.group(1)
                img_path = path_img + '/' + img_name + '.png'
                if not os.path.exists(img_path):
                    for replace_list in replace_lists:
                        if img_name in replace_list:
                            line = line.replace(img_name, replace_list[0])
                else:
                    removed = remove_duplicates(img_name, img_path)
                    replace_lists.append([img_name, ] + removed)
            result += line
            print(line, end='')
    with open(path_data + '/' + bp_file_name, 'w') as bp_file:
        bp_file.write(result)
