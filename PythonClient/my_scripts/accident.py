import os
import time
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

def main():
    os.makedirs('captured_images', exist_ok=True)
    idx = 0

    car1 = AirSimCarControl('Car1')
    car2 = AirSimCarControl('Car2')

    while True:
        # Print state of the car
        car1.printCarState()
        car2.printCarState()

        # Just go forward
        car1.control(throttle=10)
        car2.control(throttle=10)

        # get image
        car1.saveImage('MyCamera1', os.path.join('captured_images', '{}.png'.format(idx)))
        idx += 1

        time.sleep(1)

if __name__ == '__main__':
    main()
