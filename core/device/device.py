
import subprocess

from enum import Enum

from core.logger import Logger

from .screencap.ascreencap import aScreenCap
from .screencap.droidCast import droidCast
from core.base import Base

class Device:

    class ScreenCapType(Enum):
        aScreenCap = 0           # direct 
        droidCast = 1

    def __init__(self, connectDevice: str = 'emulator-5554', screencapType: ScreenCapType = ScreenCapType.aScreenCap) -> None:
        self._adbExePath = '\"' + Base.s_toolkitPath + '/adb/adb.exe\"'
        self._connectDevice = connectDevice
        self.restart()
        # try:
        #     subprocess.check_output(self._adbExePath + ' kill-server')
        #     subprocess.check_output(self._adbExePath + ' start-server')
        # except:
        #     pass

        self._screenCapType = screencapType

        if screencapType == screencapType.aScreenCap:
            self._screenCap = aScreenCap(self)
        elif screencapType == screencapType.droidCast:
            self._screenCap = droidCast(self)
        else:
            raise NotImplementedError('unknown screen cap type')
        
        # push the sh files
        self.checkOutput('push .\\assets\\nscript /sdcard')

    def screenshot(self) -> bool:
        return self._screenCap.screenshot()

    def getScreenshot(self):
        return self._screenCap.getScreenshot()

    def checkOutput(self, cmd: str):
        return subprocess.check_output(self._adbExePath + ' -s ' + self._connectDevice  + ' ' + cmd, shell=True)

    def Popen(self, cmd):
        try:
            return subprocess.Popen(self._adbExePath + ' -s ' + self._connectDevice + ' ' + cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=False)
        except subprocess.CalledProcessError as e:
            Logger.error('Error: ', e)
            return None
        except OSError as e:
            Logger.error('存取被拒: ', e)
            return None
        #return subprocess.Popen(self._adbExePath + ' -s ' + self._connectDevice + ' ' + cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=False)

    # completely kill the process will executing something
    def run_adb_dontcare(self, args):
        args = ['../toolkit/adb/adb.exe', '-s', self._connectDevice] + args

        try:
            p = subprocess.Popen([str(arg) for arg in args], stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, encoding='utf-8')
            p.communicate(timeout=1) # 1 second to run
            return p
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
            return None
        except subprocess.CalledProcessError as e:
            Logger.error('Error: ' + e.output)
            return None
        except OSError as e:
            Logger.error('存取被拒: ' + str(e.winerror))
            return None

    def run_adb(self, args, pipeOutput=True):
        args = ['../toolkit/adb/adb.exe', '-s', self._connectDevice] + args

        # print('exec cmd : %s' % args)
        out = subprocess.DEVNULL
        if (pipeOutput):
            out = subprocess.PIPE

        #print([str(arg) for arg in args])

        try:
            p = subprocess.Popen([str(arg) for arg in args], stdout=out, encoding='utf-8')
            stdout, stderr = p.communicate()
            return (p.returncode, stdout, stderr)
        except subprocess.CalledProcessError as e:
            Logger.error('Error: ' + e.output)
            return None
        except OSError as e:
            Logger.error('存取被拒: ' + str(e.winerror))
            return None

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

    def zoomOut(self, count: int):
        for i in range(count):
            self.checkOutput('shell sh /sdcard/nscript/zoomout.sh')

    def connect(self, deviceName: str):
        self._connectDevice = deviceName
        return self.checkOutput('connect %s' % (deviceName))
    
    def restart(self):
        try:
            self.checkOutput('kill-server')
        except Exception as e:
            None
        self.checkOutput('start-server')
        self.connect(self._connectDevice)

