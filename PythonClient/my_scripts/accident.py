import os
import time
import random
import datetime
from car_controller import AirSimCarControl

# Use below in settings.json with blocks environment
"""
{
  "SettingsVersion": 1.2,
  "Recording": {
    "RecordOnMove": false,
    "RecordInterval": 0.1,
    "Cameras": [
        { "CameraName": "MyCamera1", "ImageType": 0, "PixelsAsFloat": false, "Compress": true }
    ]
  },
  "CameraDefaults": {
    "CaptureSettings": [
      {
        "ImageType": 0,
        "Width": 1280,
        "Height": 720,
        "FOV_Degrees": 120,
        "AutoExposureSpeed": 100,
        "MotionBlurAmount": 0,
        "AutoExposureMinBrightness": 300
      }
    ]
  },
  "SubWindows": [
    {"WindowID": 1, "CameraName": "MyCamera1", "ImageType": 0, "Visible": true}
  ],

  "SimMode": "Car",
  "Vehicles": {
      "Car1": {
        "VehicleType": "PhysXCar",
        "Cameras": {
          "MyCamera1": {
            "CaptureSettings": [
              {
                  "ImageType": 0,
                  "Width": 640,
                  "Height": 360,
                  "FOV_Degrees": 120,
                  "AutoExposureSpeed": 100,
                  "MotionBlurAmount": 0,
                  "AutoExposureMinBrightness": 300
              }
            ],
            "NoiseSettings": [
              {
                "Enabled": false,
                "ImageType": 0
              }
            ],
            "X": 0.7, "Y": 0, "Z": -1.55,
            "Pitch": 0.3, "Roll": 0, "Yaw": 0
          }
        },
        "X": -100, "Y": -1.75, "Z": 0,
        "Yaw": 0
      },
      "Car2": {
        "VehicleType": "PhysXCar",
        "X": 100, "Y": 1.75, "Z": 0,
        "Yaw": 180
      }
    }
}
"""

class RouteManager:
    directions = ['north', 'east', 'south', 'west']

    keypoints = {
        'north': [(80, 1.75), (7, 1.75), (1, -1), (5, -1.75), (100, -1.75)],
        'east': [(-1.75, 80), (-1.75, 7), (1, 1), (1.75, 5), (1.75, 100)],
        'south': [(-80, -1.75), (-7, -1.75), (-1, 1), (-5, 1.75), (-100, 1.75)],
        'west': [(1.75, -80), (1.75, -7), (-1, -1), (-1.75, -5), (-1.75, -100)]
    }

    speeds = {
        'straight': [5, 30],
        'left': [9, 30, 8, 30],
        'right': [30, 12, 16, 30]
    }

    brakes = {
        'straight': [False, True],
        'left': [False, True, False, True],
        'right': [True, False, False, True]
    }

    def __init__(self, car, route='straight', random=False):
        self.car = car
        self.idx = 0
        self.random = random

        _, _, _, initial_position, _ = self.car.getCarState()
        initial_direction = 'north'
        if initial_position['x'] < -50:
            initial_direction = 'south'
        elif initial_position['y'] < -50:
            initial_direction = 'west'
        elif initial_position['y'] > 50:
            initial_direction = 'east'

        self.control_list = self.getControlList(initial_direction, route)

    def getControlList(self, from_direction, route):
        control_list = {'points': None, 'speeds': None, 'brakes': None}
        directions_idx = self.directions.index(from_direction)

        if route == 'straight':
            to_direction = self.directions[(directions_idx + 2)%4]
            control_list['points'] = [
                self.keypoints[from_direction][0],
                self.keypoints[to_direction][4]
            ]

        elif route == 'left':
            to_direction = self.directions[(directions_idx + 1)%4]
            control_list['points'] = [
                self.keypoints[from_direction][0],
                self.keypoints[from_direction][1],
                self.keypoints[to_direction][3],
                self.keypoints[to_direction][4]
            ]

        else:
            to_direction = self.directions[(directions_idx + 3)%4]
            control_list['points'] = [
                self.keypoints[from_direction][1],
                self.keypoints[to_direction][2],
                self.keypoints[to_direction][3],
                self.keypoints[to_direction][4]
            ]

        control_list['speeds'] = self.speeds[route]
        control_list['brakes'] = self.brakes[route]

        return control_list

    def run(self):
        if self.idx in range(len(self.control_list['points'])):
            x, y = self.control_list['points'][self.idx]
            speed = self.control_list['speeds'][self.idx]

            if self.random:
                random_value = random.random() * 2 - 1 # between -1 and 1
                x += random_value * 0.3
                y += random_value * 0.3
                speed += random_value * 1

            arrived = self.car.goto(
                (x, y),
                speed = speed,
                brake = self.control_list['brakes'][self.idx]
            )

            if arrived:
                self.idx += 1

def main():
    dirname = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    os.makedirs(dirname, exist_ok=True)
    idx = 0

    car1 = AirSimCarControl('Car1')
    car2 = AirSimCarControl('Car2')

    car1_route = RouteManager(car1, route='straight', random=True)
    car2_route = RouteManager(car2, route='straight', random=True)

    while True:
        # Print state of the car
        # car1.printCarState()
        # car2.printCarState()

        car1_route.run()
        car2_route.run()

        # get image
        car1.saveImage('MyCamera1', os.path.join(dirname, '{}.png'.format(idx)))
        idx += 1

        time.sleep(0.1)

if __name__ == '__main__':
    main()
