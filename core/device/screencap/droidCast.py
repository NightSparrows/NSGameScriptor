
import numpy as np
import cv2
import requests
import time

from core.base import Base

from .screencap import ScreenCap

from ...logger import Logger

class droidCast(ScreenCap):
    
    DROIDCAST_FILEPATH_LOCAL = './bin/DroidCast/droidCast_raw.apk'
    DROIDCAST_FILEPATH_REMOTE = '/data/local/tmp/DroidCast_raw.apk'

    def __init__(self, device) -> None:
        # install ascreencap into emulator
        self._device = device
        self._port = 53517                  # the port of the droidcast

        # stop droidcast
        self.stop()

        # push droidcast to the emulator
        Logger.info('Pushing droidCast apk')
        self._device.run_adb(['push', droidCast.DROIDCAST_FILEPATH_LOCAL, droidCast.DROIDCAST_FILEPATH_REMOTE])

        # run droid cast in emulator
        args = ["shell",
                "nohup",
                "app_process",
                '-Djava.class.path=%s' % droidCast.DROIDCAST_FILEPATH_REMOTE,
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
        self._device.run_adb_dontcare(args)
        Logger.trace('Run droidcast in background')
        # forward tcp the adb to host
        (code, _, err) = self._device.run_adb(["forward", "tcp:%d" % self._port, "tcp:%d" % self._port])
        Logger.trace(">>> adb forward tcp:%d %s" % (self._port, code))



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

    def stop(self):
        # find droidcast process
        (returncode, stdout, _) = self._device.run_adb(['shell', 'ps', '-ef'])

        if (returncode != 0):
            return

        splitStr = stdout.split('\n')

        for line in splitStr:
            processInfo = list(filter(None, line.split(' ')))
            if len(processInfo) < 1:
                continue
            #print('pid: ' + processInfo[1])
            #print('name: ' + processInfo[7])

            if processInfo[7] == 'app_process' and processInfo[8] == ('-Djava.class.path=%s' % droidCast.DROIDCAST_FILEPATH_REMOTE):
                self._device.run_adb(['shell', 'kill', processInfo[1]])
                print('process ' + processInfo[1] + ' killed')
        return
