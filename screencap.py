
from core.device.device import Device
import cv2

# use to cap screen for file
if __name__ == '__main__':
    device = Device(connectDevice="127.0.0.1:16448", screencapType=Device.ScreenCapType.droidCast)

    device._screenCap.screenshot_save()