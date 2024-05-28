from __future__ import division, print_function, absolute_import
import os
import io
import pandas as pd

import tensorflow as tf
from PIL import Image
from object_detection.utils import dataset_util
from collections import namedtuple

flags = tf.app.flags
flags.DEFINE_string('csv_input', '', 'Path to the CSV input')
flags.DEFINE_string('labelmap', '', 'Path to the labelmap file')
flags.DEFINE_string('image_dir', '', 'Path to the image directory')
flags.DEFINE_string('output_path', '', 'Path to output TFRecord')
FLAGS = flags.FLAGS

def split(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]

def create_tf_example(group, path):
    with tf.io.gfile.GFile(os.path.join(path, '{}'.format(group.filename)), 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)
    width, height = image.size

    filename = group.filename.encode('utf8')
    image_format = b'jpg'
    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    labels = []
    with open(FLAGS.labelmap, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    for index, row in group.object.iterrows():
        xmins.append(row['xmin'] / width)
        xmaxs.append(row['xmax'] / width)
        ymins.append(row['ymin'] / height)
        ymaxs.append(row['ymax'] / height)
        classes_text.append(row['class'].encode('utf8'))
        classes.append(int(labels.index(row['class'])+1))

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))
    return tf_example

def main(_):
    # Ensure the output directory exists
    output_dir = os.path.dirname(FLAGS.output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Verify input CSV file exists
    if not os.path.isfile(FLAGS.csv_input):
        raise FileNotFoundError(f"The specified CSV file {FLAGS.csv_input} does not exist.")

    # Verify image directory exists
    if not os.path.isdir(FLAGS.image_dir):
        raise NotADirectoryError(f"The specified image directory {FLAGS.image_dir} does not exist.")

    # Load and prepare data
    writer = tf.io.TFRecordWriter(FLAGS.output_path)
    path = os.path.join(os.getcwd(), FLAGS.image_dir)
    examples = pd.read_csv(FLAGS.csv_input)

    # Create TFRecord files
    grouped = split(examples, 'filename')
    for group in grouped:
        tf_example = create_tf_example(group, path)
        writer.write(tf_example.SerializeToString())

    writer.close()
    output_path = os.path.join(os.getcwd(), FLAGS.output_path)
    print('Successfully created the TFRecords: {}'.format(output_path))

    # Create labelmap.pbtxt file
    path_to_labeltxt = os.path.join(os.getcwd(), FLAGS.labelmap)
    if not os.path.isfile(path_to_labeltxt):
        raise FileNotFoundError(f"The specified labelmap file {path_to_labeltxt} does not exist.")
    
    with open(path_to_labeltxt, 'r') as f:
        labels = [line.strip() for line in f.readlines()]
    
    path_to_labelpbtxt = os.path.join(os.getcwd(), 'labelmap.pbtxt')
    with open(path_to_labelpbtxt,'w') as f:
        for i, label in enumerate(labels):
            f.write('item {\n' +
                    '  id: %d\n' % (i + 1) +
                    '  name: \'%s\'\n' % label +
                    '}\n' +
                    '\n')

if __name__ == '__main__':
    tf.compat.v1.app.run()
