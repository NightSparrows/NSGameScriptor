
import json
import subprocess
import time

from core.logger import Logger

from .emulator import Emulator


class MumuEmulator(Emulator):
    """Wraps the MumuManager CLI shipped with MuMu Player's multi-instance
    ("多開") manager. Canonical home for the MuMu install path and the
    "which vmindex does this adb port belong to" lookup -
    core/device/screencap/nemuScreencap.py reuses both rather than
    duplicating them (NemuIPC only ever talks to MuMu anyway).

    Only applies when the multi-instance manager is actually set up -
    Device catches construction failures here and falls back to no
    emulator lifecycle management for single-instance MuMu installs (or
    machines without MuMu's manager at this path at all), rather than
    crashing."""

    # default install path - not everyone's MuMu lives here (portable
    # installs, non-default drive, etc), so it's overridable per-instance
    # via installPath (wired from config's "emulatorPath" field)
    EMULATOR_PATH = 'C:\\Program Files\\Netease\\MuMuPlayer'
    MANAGER_EXE = EMULATOR_PATH + '\\nx_main\\MumuManager'

    def __init__(self, connectDevice: str, installPath: str = None) -> None:
        self._installPath = installPath or MumuEmulator.EMULATOR_PATH
        self._managerExe = MumuEmulator._managerExe(self._installPath)

        _, port = connectDevice.rsplit(':', 1)
        self._vmIndex = MumuEmulator.findVmIndex(int(port), self._installPath)

        if self._vmIndex == -1:
            raise RuntimeError('Emulator index not found from serial port: ' + connectDevice)

    @staticmethod
    def _managerExe(installPath: str = None) -> str:
        return (installPath or MumuEmulator.EMULATOR_PATH) + '\\nx_main\\MumuManager'

    # a stopped instance's info doesn't report adb_port at all (confirmed
    # live), so a live port match is impossible while it's off - exactly
    # the case this most needs to get right, since the whole point is
    # being able to launch a currently-stopped emulator. MuMu multi-
    # instance ports follow a fixed formula (16384 + vmIndex*32,
    # confirmed live: index 3 -> port 16480), so as a fallback, compute
    # the candidate index from the port and only trust it if that index
    # is actually a registered instance (whether running or not) - never
    # trust the formula alone.
    @staticmethod
    def findVmIndex(adbPort: int, installPath: str = None) -> int:
        managerExe = MumuEmulator._managerExe(installPath)
        try:
            result = subprocess.check_output([
                managerExe, 'info', '--vmindex', 'all',
            ])
        except OSError as e:
            raise RuntimeError('找不到 MuMuManager (' + managerExe + ')，請至設定確認模擬器安裝路徑: ' + str(e)) from e

        emulatorInfoList = json.loads(result.decode('utf-8').strip())
        for index, emulatorInfo in emulatorInfoList.items():
            if isinstance(emulatorInfo, dict) and emulatorInfo.get('adb_port') == adbPort:
                return int(index)

        if (adbPort - 16384) % 32 == 0:
            candidate = (adbPort - 16384) // 32
            if str(candidate) in emulatorInfoList:
                return candidate

        return -1

    def _info(self) -> dict:
        result = subprocess.check_output([
            self._managerExe, 'info', '--vmindex', str(self._vmIndex),
        ])
        return json.loads(result.decode('utf-8').strip())

    def isRunning(self) -> bool:
        # is_android_started is not a reliable signal in practice - it was
        # observed staying False across many live checks this session even
        # while the instance was demonstrably up and usable (real
        # screenshots/adb commands succeeding). is_process_started +
        # player_state == 'start_finished' correlated correctly every time.
        info = self._info()
        return bool(info.get('is_process_started')) and info.get('player_state') == 'start_finished'

    def launch(self) -> bool:
        Logger.info('啟動模擬器 (vmindex ' + str(self._vmIndex) + ') ...')
        try:
            subprocess.check_output([
                self._managerExe, 'control', '--vmindex', str(self._vmIndex), 'launch',
            ])
            return True
        except subprocess.CalledProcessError as e:
            Logger.error('無法啟動模擬器: ' + str(e))
            return False

    def shutdown(self) -> bool:
        try:
            subprocess.check_output([
                self._managerExe, 'control', '--vmindex', str(self._vmIndex), 'shutdown',
            ])
            return True
        except subprocess.CalledProcessError as e:
            Logger.error('無法關閉模擬器: ' + str(e))
            return False

    def waitUntilReady(self, timeout: float = 90) -> bool:
        if self.isRunning():
            return True

        if not self.launch():
            return False

        elapsed = 0.0
        interval = 2.0
        while elapsed < timeout:
            time.sleep(interval)
            elapsed += interval
            if self.isRunning():
                Logger.info('模擬器已啟動')
                return True

        Logger.error('等待模擬器啟動逾時')
        return False
