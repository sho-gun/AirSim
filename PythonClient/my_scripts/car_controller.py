import airsim
import cv2
import numpy as np
import os
import setup_path
import time
import math
import json
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

    def getGroundTruthState(self, name):
        return self._client.simGetGroundTruthKinematics(name)

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
        self.X, self.Y, self.Z = getInitialPosition(name)
        # self.effector = FisheyeEffector(distortion=0.1)

    def printCarState(self):
        speed, gear, _, position, orientation = self.getCarState()
        print('%s: Speed %f, Gear %d, Orientation %f' % (self.name, speed, gear, orientation))
        # print('%s: x %f, y %f' % (self.name, position['x'], position['y']))

    def getCarState(self):
        state = self.client.getCarState(self.name)
        gtstate = self.client.getGroundTruthState(self.name)

        position = gtstate.position
        quaternion = gtstate.orientation

        position_dict = {'x': self.X + position.x_val, 'y': self.Y + position.y_val}

        orientation = calcCarOrientation(
            quaternion.w_val,
            quaternion.x_val,
            quaternion.y_val,
            quaternion.z_val
        )

        return state.speed, state.gear, state.handbrake, position_dict, orientation

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

    def drive(self, speed=20.0, orientation=0.0):
        current_speed, _, _, _, current_orientation = self.getCarState()

        throttle = speed - current_speed
        if throttle < 0:
            throttle = 0

        orientation_diff = orientation - current_orientation
        if orientation_diff > 180:
            orientation_diff -= 360
        elif orientation_diff < -180:
            orientation_diff += 360

        self.control(throttle=throttle, steering=orientation_diff*0.05)

    def goto(self, point, speed=20.0, brake=True):
        x, y = point
        current_speed, _, _, current_position, current_orientation = self.getCarState()

        vector_x = x - current_position['x']
        vector_y = y - current_position['y']

        distance = abs(math.sqrt(vector_x**2 + vector_y**2))
        norm_vec_x = vector_x / distance

        target_speed = distance
        if target_speed > speed:
            target_speed = speed

        target_orientation_rad = np.arccos(norm_vec_x)
        if vector_y < 0:
            target_orientation_rad = 2 * np.pi - target_orientation_rad
        target_orientation = np.rad2deg(target_orientation_rad)

        if distance <= 3 and current_speed < 1:
            if brake:
                self.control(brake=1)
            return True
        elif distance > 0.1 * current_speed**2:
            self.drive(speed=target_speed, orientation=target_orientation)
            return False
        else:
            if brake:
                self.control(brake=1)
                return False
            return True

def getInitialPosition(name):
    settings_path = os.path.join(os.path.expanduser('~'), 'Documents', 'AirSim', 'settings.json')
    x, y, z = 0, 0, 0

    with open(settings_path, 'r') as f:
        settings_dict = json.load(f)
        x = settings_dict['Vehicles'][name]['X']
        y = settings_dict['Vehicles'][name]['Y']
        z = settings_dict['Vehicles'][name]['Z']

    return x, y, z

def calcCarOrientation(w, x, y, z):
    orientation_x = x**2 - y**2 - z**2 + w**2
    orientation_y = 2 * (x*y + z*w)

    if orientation_x > 1:
        orientation_x = 1
    elif orientation_x < -1:
        orientation_x = -1

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
