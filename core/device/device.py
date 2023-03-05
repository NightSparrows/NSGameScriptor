
import subprocess

from enum import Enum

from core.logger import Logger

from .screencap.ascreencap import aScreenCap
from core.base import Base

class Device:

    class ScreenCapType(Enum):
        aScreenCap = 'aScreenCap'           # direct 

    def __init__(self, connectDevice: str = 'emulator-5554', screencapType: ScreenCapType = ScreenCapType.aScreenCap) -> None:
        self._adbExePath = Base.s_toolkitPath + '/adb/adb.exe'
        self._connectDevice = connectDevice
        
        # try:
        #     subprocess.check_output(self._adbExePath + ' kill-server')
        #     subprocess.check_output(self._adbExePath + ' start-server')
        # except:
        #     pass

        if screencapType == screencapType.aScreenCap:
            self._screenCap = aScreenCap(self)
        else:
            raise NotImplementedError('unknown screen cap type')

            
    
    def screenshot(self):
        self._screenCap.screenshot()

    def getScreenshot(self):
        return self._screenCap.getScreenshot()

    def checkOutput(self, cmd: str):
        return subprocess.check_output(self._adbExePath + ' -s ' + self._connectDevice  + ' ' + cmd, shell=True)

    def Popen(self, cmd):
        return subprocess.Popen(self._adbExePath + ' -s ' + self._connectDevice + ' ' + cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

    def openApp(self, appName):
        return self.checkOutput('shell am start -n ' + appName)

    def killApp(self, appName):
        return self.checkOutput('shell am force-stop ' + appName)

    def tap(self, x: int, y: int):
        return self.checkOutput('shell input tap %d %d' % (x, y))

    # Swipe the screen
    def swipe(self, x0, y0, x1, y1):
        return self.checkOutput('shell input swipe %d %d %d %d' % (x0, y0, x1, y1))

    # 長按
    # time in millisecond
    def hold(self, x, y, time):
        return self.checkOutput('shell input swipe %d %d %d %d %d' % (x, y, x, y, time))

    # 長按
    # time in millisecond
    def holdScroll(self, x0, y0, x1, y1, time):
        return self.checkOutput('shell input swipe %d %d %d %d %d' % (x0, y0, x1, y1, time))

    def connect(self, deviceName: str):
        self._connectDevice = deviceName
