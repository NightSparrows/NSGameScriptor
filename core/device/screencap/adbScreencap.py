
import cv2
from adbutils import adb

import numpy as np

class AdbScreenCap:

    def __init__(self, device):
        self.m_adb = adb.device(device._connectDevice)

    def screenshot(self) -> bool:
        data = self.m_adb.shell(['screencap', '-p'], stream=False, encoding=None)

        if len(data) < 500:
            pass        # TODO warning: wired output
        image = np.frombuffer(data, np.uint8)
        self.m_image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return self.m_image != None
    
    def getScreenshot(self):
        return self.m_image
