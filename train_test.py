from pathlib import Path
import random
import os

# Define paths to image folders
image_path = '/content/images/all'
train_path = '/content/images/train'
val_path = '/content/images/validation'
test_path = '/content/images/test'

# Create directories if they don't exist
Path(train_path).mkdir(parents=True, exist_ok=True)
Path(val_path).mkdir(parents=True, exist_ok=True)
Path(test_path).mkdir(parents=True, exist_ok=True)

# Get list of all images
image_extensions = ['*.jpeg', '*.jpg', '*.png', '*.bmp', '*.JPEG', '*.JPG']
file_list = []
for ext in image_extensions:
    file_list.extend(Path(image_path).rglob(ext))

file_num = len(file_list)
print('Total images: %d' % file_num)

# Determine number of files to move to each folder
train_percent = 0.8  # 80% of the files go to train
val_percent = 0.1 # 10% go to validation
test_percent = 0.1 # 10% go to test
train_num = int(file_num * train_percent)
val_num = int(file_num * val_percent)
test_num = file_num - train_num - val_num
print('Images moving to train: %d' % train_num)
print('Images moving to validation: %d' % val_num)
print('Images moving to test: %d' % test_num)

def move_file(move_me, destination_path):
    fn = move_me.name
    os.rename(move_me, os.path.join(destination_path, fn))

# Select 80% of files randomly and move them to train folder
for i in range(train_num):
    move_me = random.choice(file_list)
    move_file(move_me, train_path)
    file_list.remove(move_me)

# Select 10% of remaining files and move them to validation folder
for i in range(val_num):
    move_me = random.choice(file_list)
    move_file(move_me, val_path)
    file_list.remove(move_me)

# Move remaining files to test folder
for i in range(test_num):
    move_me = random.choice(file_list)
    move_file(move_me, test_path)
    file_list.remove(move_me)
