
import subprocess
import numpy as np
import lz4.block
import cv2

from .screencap import ScreenCap

from ...logger import Logger

class aScreenCap(ScreenCap):

    s_screenCapPath = '/data/local/tmp'

    def __init__(self, device) -> None:
        # install ascreencap into emulator
        self._device = device
        device.checkOutput('push toolkit/ascreencap/x86_64/ascreencap ' + aScreenCap.s_screenCapPath)
        device.checkOutput('shell chmod 777 ' + aScreenCap.s_screenCapPath + '/ascreencap')

    def screenshot(self):
        pipe = self._device.Popen('exec-out ' + aScreenCap.s_screenCapPath + '/ascreencap --pack 2 --stdout')

        data = pipe.stdout.read()
        pipe.terminate()

        # See headers in:
        # https://github.com/ClnViewer/Android-fast-screen-capture#streamimage-compressed---header-format-using
        compressed_data_header = np.frombuffer(data[0:20], dtype=np.uint32)
        
        if compressed_data_header[0] != 828001602:
            compressed_data_header = compressed_data_header.byteswap()
            if compressed_data_header[0] != 828001602:
                Logger.error('Failed to verify aScreenCap data header!')
                return False
        
        _, uncompressed_size, _, width, height = compressed_data_header
        channel = 3
        decodeData = lz4.block.decompress(data[20:], uncompressed_size=uncompressed_size)

        image = np.frombuffer(decodeData, dtype=np.uint8)
        if image is None:
            Logger.error('Empty image after reading from buffer')
            return False
        
        try:
            image = image[-int(width * height * channel):].reshape(height, width, channel)
        except ValueError as e:
            Logger.error('cannot reshape array of size 0 into shape')
            return False
    
        image = cv2.flip(image, 0)
        if image is None:
            Logger.error('Empty image after cv2.flip')

        #cv2.imshow('', image)
        #cv2.waitKey(0)
        self._screenshot = image
    
    def getScreenshot(self):
        return self._screenshot


