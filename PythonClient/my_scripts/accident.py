import time
from car_controller import AirSimCarControl

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

def main():
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
        car1.saveImage('0')

        time.sleep(1)

if __name__ == '__main__':
    main()
