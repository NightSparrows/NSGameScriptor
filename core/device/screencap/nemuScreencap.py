
import cv2
import subprocess
import numpy as np
import json
import ctypes
from .screencap import ScreenCap

from core.logger import Logger


class NemuIPCScreenCap(ScreenCap):

    EMULATOR_PATH = 'C:\\Program Files\\Netease\\MuMuPlayerGlobal-12.0'

    def __init__(self, device):
        
        ip, port = device._connectDevice.rsplit(':', 1)

        result = subprocess.check_output([
            f'{NemuIPCScreenCap.EMULATOR_PATH}\\nx_main\\MumuManager',
            'info',
            '--vmindex',
            'all'
        ])

        self.m_instance_id = -1

        emulator_info_list = json.loads(result.decode('utf-8').strip())
        for index, emulator_info in emulator_info_list.items():
            print(emulator_info)
            # exit(-1)
            adb_port = emulator_info.get('adb_port')
            if adb_port is None:
                continue            # 模擬器沒開

            if adb_port == int(port):
                self.m_instance_id = int(index)
                break

        if self.m_instance_id == -1:
            raise RuntimeError('Emulator index not found from serial port')
        
        Logger.info(f'emulator index {self.m_instance_id}')

        # 載入DLL
        ipc_dll = f'{NemuIPCScreenCap.EMULATOR_PATH}/nx_device/12.0/shell/sdk/external_renderer_ipc.dll'
        self.m_lib = ctypes.CDLL(ipc_dll)

        # 建立 IPC 連線
        self.m_connect_id = 0
        self.m_connect_id = self.m_lib.nemu_connect(NemuIPCScreenCap.EMULATOR_PATH, self.m_instance_id)

        if (self.m_connect_id == 0):
            raise RuntimeError(f'Failed to connect to Nemu IPC, instance id: {self.m_instance_id}')
        
        self.m_width = 0
        self.m_height = 0
        self.m_display_id = 0       # 應該只會是0
        self._update_resolution()
    
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
