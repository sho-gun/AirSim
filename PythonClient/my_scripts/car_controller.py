import airsim
import cv2
import numpy as np
import os
import setup_path
import time
from fisheye_effector import FisheyeEffector

# AirSim API Documentation
# https://microsoft.github.io/AirSim/apis/#vehicle-specific-apis

# Use below in settings.json with blocks environment
"""
{
    "SettingsVersion": 1.2,
    "SimMode": "Car",

    "Vehicles": {
        "Car1": {
          "VehicleType": "PhysXCar",
          "X": 4, "Y": 0, "Z": -2
        },
        "Car2": {
          "VehicleType": "PhysXCar",
          "X": -4, "Y": 0, "Z": -2
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
        self.effector = FisheyeEffector(distortion=0.3)

    def printCarState(self):
        state = self.client.getCarState(self.name)
        print('%s: Speed %d, Gear %d' % (self.name, state.speed, state.gear))

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
        image = self.effector.apply(image)
        with open(save_path, 'wb') as output:
            output.write(image)


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
