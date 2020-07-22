import io
import numpy as np
from PIL import Image
from math import sqrt

class FisheyeEffector:
    def __init__(self, height=720, width=1280, distortion=0.5):
        float_height, float_width = float(height), float(width)

        self.filter = np.full((height, width, 2), -1)

        for h in range(height):
            for w in range(width):
                norm_h, norm_w = float((2*h - float_height) / float_height), float((2*w - float_width) / float_width)
                radius = sqrt(norm_h**2 + norm_w**2)
                org_norm_h, org_norm_w = calc_points_of_original_image(norm_h, norm_w, radius, distortion)
                org_h, org_w = int((org_norm_h + 1) * float_height / 2), int((org_norm_w + 1) * float_width / 2)

                if org_h in range(height) and org_w in range(width):
                    self.filter[h][w] = [org_h, org_w]

    def apply(self, image_bytes):
        image = np.array(Image.open(io.BytesIO(image_bytes)))
        fish_image = np.zeros_like(image)

        for h in range(len(fish_image)):
            for w in range(len(fish_image[0])):
                org_h, org_w = self.filter[h][w]
                if org_h >= 0 and org_w >= 0:
                    fish_image[h][w] = image[org_h][org_w]

        fish_image_bytes = io.BytesIO()
        Image.fromarray(fish_image).save(fish_image_bytes, 'png')

        return fish_image_bytes.getvalue()

def calc_points_of_original_image(x, y, r, distortion):
    if 1 - distortion*(r**2) == 0:
        return x, y

    return x / (1 - distortion*(r**2)), y / (1 - distortion*(r**2))
