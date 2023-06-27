
from core.device.device import Device
import cv2

# use to cap screen for file
if __name__ == '__main__':
    device = Device(connectDevice="127.0.0.1:5556")

    device._screenCap.screenshot_save()