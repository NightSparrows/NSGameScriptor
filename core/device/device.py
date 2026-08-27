
import subprocess
import threading
import time

from enum import Enum

from core.logger import Logger

from .screencap.ascreencap import aScreenCap
from .screencap.droidCast import droidCast
from .screencap.adbScreencap import AdbScreenCap
from .screencap.nemuScreencap import NemuIPCScreenCap
from .emulator.mumuEmulator import MumuEmulator
from core.base import Base

class Device:

    class ScreenCapType(Enum):
        aScreenCap = 0           # direct
        droidCast = 1
        ADB = 2
        NEMUIPC = 3

    class EmulatorType(Enum):
        NONE = 0   # no lifecycle management - assume it's already running
        MUMU = 1

    def __init__(self, connectDevice: str = 'emulator-5554', screencapType: ScreenCapType = ScreenCapType.aScreenCap, emulatorType: EmulatorType = EmulatorType.NONE) -> None:
        self._adbExePath = '\"' + Base.s_toolkitPath + '/adb/adb.exe\"'
        self._connectDevice = connectDevice
        # Screencap backends (esp. NemuIPC, which calls straight into a
        # native DLL over a shared IPC handle) aren't safe to call
        # concurrently from multiple threads - the GUI's live preview
        # calls screenshot() on this same Device from a background thread
        # while automation may be doing the same on another. This lock
        # serializes those calls; it's a no-op for the CLI's single thread.
        self._screenshotLock = threading.Lock()

        self._emulatorType = emulatorType
        self._emulator = self._buildEmulator(emulatorType, connectDevice)

        self._screenCapType = screencapType
        self._screenCap = None

        # If the emulator's already up (or nothing's being managed, e.g.
        # non-MuMu setups - the overwhelmingly common case) build the
        # connection now, exactly like before. Only defer when we
        # positively know the emulator isn't running yet, so just
        # constructing Device/opening the GUI or CLI doesn't require the
        # emulator to already be open - browsing/editing tasks or battles
        # shouldn't need it running at all. It gets built lazily the
        # moment something actually needs the device, via
        # ensureEmulatorRunning() (which GameFGO.ensureReady() already
        # calls before running any task) or screenshot() below.
        if self._emulator is None or self._emulator.isRunning():
            self._screenCap = self._connectAndBuildScreenCap(screencapType, connectDevice)
        else:
            Logger.info('模擬器目前未開啟，延後建立裝置連線 (執行工作時會自動確認/啟動模擬器)')

        # push the sh files
        # self.checkOutput('push .\\assets\\nscript /sdcard')

    def _buildEmulator(self, emulatorType: EmulatorType, connectDevice: str):
        if emulatorType == Device.EmulatorType.NONE:
            return None
        if emulatorType == Device.EmulatorType.MUMU:
            # MumuManager (the multi-instance CLI) only exists/behaves this
            # way when the user actually has MuMu's multi-instance manager
            # set up - a single-instance MuMu install (or none at all)
            # won't have it at this path, or findVmIndex() just won't find
            # a match. Don't let that crash Device construction entirely -
            # fall back to no emulator lifecycle management, same as if
            # EmulatorType.NONE had been configured.
            try:
                return MumuEmulator(connectDevice)
            except (OSError, RuntimeError) as e:
                Logger.warn('無法初始化模擬器管理 (可能沒有安裝/啟用MuMu多開管理器): ' + str(e))
                return None
        raise NotImplementedError('unknown emulator type')

    def _buildScreenCap(self, screencapType: ScreenCapType):
        if screencapType == Device.ScreenCapType.aScreenCap:
            return aScreenCap(self)
        elif screencapType == Device.ScreenCapType.droidCast:
            return droidCast(self)
        elif screencapType == Device.ScreenCapType.ADB:
            return AdbScreenCap(self)
        elif screencapType == Device.ScreenCapType.NEMUIPC:
            return NemuIPCScreenCap(self)
        else:
            raise NotImplementedError('unknown screen cap type')

    # actually connects adb + builds the screencap backend. Callers are
    # responsible for confirming the emulator is already up first (either
    # __init__'s check above, or ensureEmulatorRunning() below) - this
    # method doesn't call ensureEmulatorRunning() itself to avoid a
    # circular call (ensureEmulatorRunning() calls this when deferred).
    # If it fails despite that and an emulator is under management,
    # restart it once and retry - a "running but not actually reachable"
    # emulator is a different failure mode than "not running at all",
    # and a plain isRunning() check can't catch it.
    def _connectAndBuildScreenCap(self, screencapType: ScreenCapType, connectDevice: str):
        maxAttempts = 2 if self._emulator is not None else 1

        for attempt in range(1, maxAttempts + 1):
            try:
                self.connect(connectDevice)
                return self._buildScreenCap(screencapType)
            except Exception as e:
                if attempt >= maxAttempts:
                    raise
                Logger.warn(f'連線/截圖初始化失敗 (第{attempt}次): {e}，重新啟動模擬器後重試')
                self._emulator.shutdown()
                self._emulator.waitUntilReady()
                time.sleep(1)

    # the single entry point task execution should call before touching
    # the device: confirms the emulator (if managed) is up, launching it
    # if needed, THEN lazily builds the adb/screencap connection if
    # __init__ deferred it (emulator wasn't running at construction time).
    # No-op-ish (returns True immediately once connected) when no
    # EmulatorType was configured - existing setups are unaffected unless
    # they opt in.
    def ensureEmulatorRunning(self, timeout: float = 90) -> bool:
        if self._emulator is not None:
            if not self._emulator.waitUntilReady(timeout):
                return False

        if self._screenCap is None:
            try:
                self._screenCap = self._connectAndBuildScreenCap(self._screenCapType, self._connectDevice)
            except Exception as e:
                Logger.error('無法建立裝置連線: ' + str(e))
                return False

        return True

    # capture can transiently raise (e.g. NemuIPC's nemu_capture_display
    # failing right after the foreground app is killed/relaunched, while
    # the emulator's render surface is momentarily in flux) - retry a few
    # times rather than letting one bad frame crash whatever's polling the
    # screen (this is exactly what ensureReady()'s auto-restart hits).
    def screenshot(self, retries: int = 3) -> bool:
        with self._screenshotLock:
            if self._screenCap is None and not self.ensureEmulatorRunning():
                Logger.error('裝置尚未就緒 (模擬器未啟動或連線失敗)，無法截圖')
                return False

            lastError = None
            for attempt in range(retries):
                try:
                    return self._screenCap.screenshot()
                except Exception as e:
                    lastError = e
                    time.sleep(0.3)

            Logger.error('screenshot() failed after ' + str(retries) + ' retries: ' + str(lastError))
            return False

    def getScreenshot(self):
        return self._screenCap.getScreenshot()

    # adb's connection to the device can transiently drop ("device
    # offline") independent of whether the emulator/app is actually fine
    # - observed live: emulator running, screencap connected fine, but a
    # subsequent adb shell command (killApp, during GameFGO.restart())
    # failed outright with no recovery anywhere in the call chain. Retry
    # once via an adb server bounce + reconnect (the same thing restart()
    # already does) before giving up. retries=0 is used internally by
    # restart()/connect() themselves so this can't recurse.
    def checkOutput(self, cmd: str, retries: int = 1):
        fullCmd = self._adbExePath + ' -s ' + self._connectDevice + ' ' + cmd
        try:
            return subprocess.check_output(fullCmd, shell=True)
        except subprocess.CalledProcessError as e:
            if retries <= 0:
                raise
            Logger.warn('adb 指令失敗，嘗試重新連線 adb 後重試: ' + cmd)
            self.restart()
            return self.checkOutput(cmd, retries - 1)

    def Popen(self, cmd: str):
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

    def run_adb(self, args, pipeOutput=True, timeout=5.0):
        args = ['../toolkit/adb/adb.exe', '-s', self._connectDevice] + args

        # print('exec cmd : %s' % args)
        out = subprocess.DEVNULL
        if (pipeOutput):
            out = subprocess.PIPE

        #print([str(arg) for arg in args])

        try:
            p = subprocess.Popen([str(arg) for arg in args], stdout=out, encoding='utf-8')
            stdout, stderr = p.communicate(timeout=timeout)
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

    def goHome(self):
        return self.checkOutput('shell input keyevent 3')   # Mumu 
    


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

    # part of the adb-level recovery machinery itself (checkOutput()'s
    # retry calls this) - retries=0 so a failure here surfaces directly
    # instead of recursing back into checkOutput()'s own retry.
    def connect(self, deviceName: str):
        self._connectDevice = deviceName
        Logger.trace(F'連接{deviceName} ...')
        return self.checkOutput('connect %s' % (deviceName), retries=0)

    def restart(self):
        try:
            self.checkOutput('kill-server', retries=0)
        except Exception as e:
            None
        self.checkOutput('start-server', retries=0)
        self.connect(self._connectDevice)

