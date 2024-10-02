
import subprocess
import numpy as np
import lz4.block
import cv2
import argparse
import requests
import threading

from core.base import Base

from .screencap import ScreenCap

from ...logger import Logger

class droidCast(ScreenCap):
    
    def __init__(self, device) -> None:
        # install ascreencap into emulator
        self._device = device
        self._port = 53516                  # the port of the droidcast

        # locate droidcast apk path
        (rc, out, _) = self._device.run_adb(["shell", "pm",
                                "path",
                                "com.rayworks.droidcast"])
        if rc or out == "":
            raise RuntimeError(
                "Locating apk failure, have you installed the app successfully?")

        prefix = "package:"
        postfix = ".apk"
        beg = out.index(prefix, 0)
        end = out.rfind(postfix)

        class_path = "CLASSPATH=" + out[beg + len(prefix):(end + len(postfix))].strip()

        # forward tcp the adb to host
        (code, _, err) = self._device.run_adb(["forward", "tcp:%d" % self._port, "tcp:%d" % self._port])
        Logger.trace(">>> adb forward tcp:%d %s" % (self._port, code))


        # run the droidcast
        thread = threading.Thread(target=self.droidCastFun, args=(class_path,))
        thread.start()



    def screenshot(self) -> bool:
        
        url = 'http://localhost:%d/screenshot' % (self._port)

        response = requests.get(url)

        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        self._screenshot = image
    
    def getScreenshot(self):
        return self._screenshot

    def screenshot_save(self):
        self.screenshot()

        cv2.imwrite('screenshot.png', self._screenshot)

        Logger.trace('Img saved.')

        return


    def droidCastFun(self, class_path):
        
        args = ["shell",
                class_path,
                "app_process",
                "/",  # unused
                "com.rayworks.droidcast.Main",
                "--port=%d" % self._port]
        self._device.run_adb(args, pipeOutput=False)
        return


