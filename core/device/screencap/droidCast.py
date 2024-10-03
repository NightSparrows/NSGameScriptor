
import numpy as np
import cv2
import requests
import threading
import time

from core.base import Base

from .screencap import ScreenCap

from ...logger import Logger

class droidCast(ScreenCap):
    
    def __init__(self, device) -> None:
        # install ascreencap into emulator
        self._device = device
        self._port = 53517                  # the port of the droidcast

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

        self._class_path = out[beg + len(prefix):(end + len(postfix))].strip()

        class_path = "CLASSPATH=" + self._class_path

        # forward tcp the adb to host
        (code, _, err) = self._device.run_adb(["forward", "tcp:%d" % self._port, "tcp:%d" % self._port])
        Logger.trace(">>> adb forward tcp:%d %s" % (self._port, code))


        # run the droidcast
        self.droidCastFun(class_path=class_path)
        #thread = threading.Thread(target=self.droidCastFun, args=(class_path,))
        #thread.start()
        self._session = requests.Session()
        self._session.trust_env = False




    def screenshot(self) -> bool:
        
        startTime = time.time()
        url = 'http://localhost:%d/screenshot' % (self._port)

        raw_image = self._session.get(url, timeout=3).content
        durTime = time.time() - startTime
        #Logger.trace('Screenshot takes ' + str(durTime) + ' secs')

        img_array = np.asarray(bytearray(raw_image), dtype=np.uint8)
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
                "nohup",
                "app_process",
                '-Djava.class.path=%s' % self._class_path,
                '/',
                "com.rayworks.droidcast.Main",
                "--port=%d" % self._port,
                ">",
                "/dev/null",
                "&"]
                
        # args = ["shell",
        #         class_path,
        #         "app_process",
        #         "/",  # unused
        #         "com.rayworks.droidcast.Main",
        #         "--port=%d" % self._port]
        p = self._device.run_adb_dontcare(args)
        Logger.trace('Run droidcast in background')
        if p.returncode is 0:
            p.terminate()
        return


