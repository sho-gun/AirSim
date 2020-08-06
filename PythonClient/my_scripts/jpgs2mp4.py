import os
import argparse
import cv2
from natsort import natsorted

parser = argparse.ArgumentParser()
parser.add_argument(
    'input_dir',
    help='source image directory')


fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
video = cv2.VideoWriter('video.mp4', fourcc, 5.0, (1280, 720))


if __name__ == '__main__':
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print('No such file or directory:', args.input_dir)
        exit()

    for image in natsorted(os.listdir(args.input_dir)):
        print('Processing', image)
        img = cv2.imread(os.path.join(args.input_dir, image))
        img = cv2.resize(img, (1280,720))
        video.write(img)

    video.release()
