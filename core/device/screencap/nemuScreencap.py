
import cv2
import glob
import os
import numpy as np
import ctypes
from .screencap import ScreenCap

from core.logger import Logger
from core.device.emulator.mumuEmulator import MumuEmulator


class NemuIPCScreenCap(ScreenCap):

    # fallback default path - canonical value lives on MumuEmulator.
    # 每個人電腦不一定同個路徑, so prefer device._emulatorPath (config's
    # "emulatorPath" field) over this when it's set.
    EMULATOR_PATH = MumuEmulator.EMULATOR_PATH

    def __init__(self, device):

        self._installPath = getattr(device, '_emulatorPath', None) or NemuIPCScreenCap.EMULATOR_PATH

        _, port = device._connectDevice.rsplit(':', 1)

        self.m_instance_id = MumuEmulator.findVmIndex(int(port), self._installPath)

        if self.m_instance_id == -1:
            raise RuntimeError('Emulator index not found from serial port')

        Logger.info(f'emulator index {self.m_instance_id} fetch from serial {device._connectDevice}')

        # 載入DLL
        ipc_dll = self._findIpcDll(self._installPath)
        self.m_lib = ctypes.CDLL(ipc_dll)

        # 建立 IPC 連線
        self.m_connect_id = 0
        self.m_connect_id = self.m_lib.nemu_connect(self._installPath, self.m_instance_id)

        if (self.m_connect_id == 0):
            raise RuntimeError(f'Failed to connect to Nemu IPC, instance id: {self.m_instance_id}')
        
        self.m_width = 0
        self.m_height = 0
        self.m_display_id = 0       # 應該只會是0
        self._update_resolution()
        Logger.info('Nemu IPC 截圖初始化成功')
    
    @staticmethod
    def _findIpcDll(installPath: str) -> str:
        # the sdk lives under nx_device/<version>/shell/sdk - <version>
        # tracks MuMu's own internal build (seen "12.0" and "15.0" across
        # installs, presumably more over time), not the app-facing MuMu
        # version number, so it can't be assumed. Discover whichever
        # version folder is actually present instead of hardcoding one;
        # if several exist, prefer the highest (newest) version.
        pattern = os.path.join(installPath, 'nx_device', '*', 'shell', 'sdk', 'external_renderer_ipc.dll')
        candidates = glob.glob(pattern)
        if not candidates:
            raise RuntimeError(f'找不到 external_renderer_ipc.dll (installPath={installPath})')

        def versionKey(path: str):
            version = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))
            return [int(part) if part.isdigit() else 0 for part in version.split('.')]

        candidates.sort(key=versionKey, reverse=True)
        return candidates[0]

    def _update_resolution(self):
        # 取得模擬器螢幕解析度
        width_ptr = ctypes.pointer(ctypes.c_int(0))
        height_ptr = ctypes.pointer(ctypes.c_int(0))
        nullptr = ctypes.POINTER(ctypes.c_int)()

        ret = self.m_lib.nemu_capture_display(
            self.m_connect_id, self.m_display_id, 0,
            width_ptr, height_ptr, nullptr
        )
        if ret > 0:
            raise RuntimeError("Failed to get resolution")
        self.m_width = width_ptr.contents.value
        self.m_height = height_ptr.contents.value

    def _capture_pixels(self) -> np.ndarray:
        # 抓取原始 RGBA 像素
        length = self.m_width * self.m_height * 4
        pixels_pointer = ctypes.pointer((ctypes.c_ubyte * length)())

        ret = self.m_lib.nemu_capture_display(
            self.m_connect_id, self.m_display_id, length,
            ctypes.pointer(ctypes.c_int(self.m_width)),
            ctypes.pointer(ctypes.c_int(self.m_height)),
            pixels_pointer
        )
        if ret > 0:
            raise RuntimeError("Failed to capture screen")

        # 轉成 numpy array
        img = np.ctypeslib.as_array(pixels_pointer.contents)
        img = img.reshape((self.m_height, self.m_width, 4))  # RGBA
        return img            

    def screenshot(self) -> bool:
        pixels = self._capture_pixels()
        # RGBA → BGR
        img = cv2.cvtColor(pixels, cv2.COLOR_BGRA2RGB)
        # 上下翻轉
        self.m_image = cv2.flip(img, 0)

        return self.m_image != None
        return self.m_image != None
    
    def getScreenshot(self):
        return self.m_image
