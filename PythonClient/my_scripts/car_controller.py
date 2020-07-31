import airsim
import cv2
import numpy as np
import os
import setup_path
import time
import math
from fisheye_effector import FisheyeEffector
from threading import Thread

# AirSim API Documentation
# https://microsoft.github.io/AirSim/apis/#vehicle-specific-apis

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
        "X": 0, "Y": 0, "Z": 0,
        "Yaw": 0
      },
      "Car2": {
        "VehicleType": "PhysXCar",
        "X": 10, "Y": 3.5, "Z": 0,
        "Yaw": 180
      }
    }
}
"""

class AirSimClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        if self._client is None:
            # connect to the AirSim simulator
            self._client = airsim.CarClient()
            self._client.confirmConnection()

    def enableApiControl(self, flag, name):
        self._client.enableApiControl(flag, name)

    def getCarState(self, name):
        return self._client.getCarState(name)

    def setCarControls(self, controls, name):
        self._client.setCarControls(controls, name)

    def simGetImage(self, name, image_type):
        return self._client.simGetImage(name, image_type)

class AirSimCarControl:
    def __init__(self, name):
        self.client = AirSimClient()
        self.name = name
        self.client.enableApiControl(True, name)
        self.controls = airsim.CarControls()
        # self.effector = FisheyeEffector(distortion=0.1)

    def printCarState(self):
        state = self.client.getCarState(self.name)
        # position = state.kinematics_estimated.position
        quaternion = state.kinematics_estimated.orientation
        orientation = calcCarOrientation(
            quaternion.w_val,
            quaternion.x_val,
            quaternion.y_val,
            quaternion.z_val
        )
        print('%s: Speed %d, Gear %d, Orientation %d' % (self.name, state.speed, state.gear, orientation))

    def control(self, throttle=0, steering=0, brake=0, gear=None):
        self.controls.throttle = throttle
        self.controls.steering = steering
        self.controls.brake = brake

        if gear is None:
            self.controls.is_manual_gear = False
            self.controls.manual_gear = 0
        else:
            self.controls.is_manual_gear = True
            self.controls.manual_gear = gear

        self.client.setCarControls(self.controls, self.name)

    def saveImage(self, name, save_path):
        image = self.client.simGetImage(name, airsim.ImageType.Scene)
        # image = self.effector.apply(image)
        Thread(target=self.threadedSaveImage, args=(image, save_path)).start()

    def threadedSaveImage(self, image, save_path):
        # image = self.effector.apply(image)
        with open(save_path, 'wb') as output:
            output.write(image)

def calcCarOrientation(w, x, y, z):
    theta = 2 * np.arccos([w])
    cos = np.cos(theta)
    sin = np.sin(theta)
    # print(np.rad2deg(theta))

    orientation_x = cos + np.power(x, 2) * (1 - cos)
    orientation_y = x * y * (1 - cos) + z * sin
    # orientation_z = z * x * (1 - cos) - y * sin
    # print(orientation_x, orientation_y, orientation_z)

    orientation_rad = np.arccos(orientation_x)
    if orientation_y < 0:
        orientation_rad = 2 * np.pi - orientation_rad
    return np.rad2deg(orientation_rad)

def main():
    car1 = AirSimCarControl('Car1')
    car2 = AirSimCarControl('Car2')

    while True:
        # Print state of the car
        car1.printCarState()
        car2.printCarState()

        # Just go forward
        car1.control(throttle=5)
        car2.control(throttle=5)

        time.sleep(1)

if __name__ == '__main__':
    main()
