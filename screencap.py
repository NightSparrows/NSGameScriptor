
from core.device.device import Device
import cv2

# use to cap screen for file
if __name__ == '__main__':
    device = Device()

    device._screenCap.screenshot_save()