
import time
import cv2

from core.logger import Logger
from core.device.device import Device
from core.matchutil import MatchUtil

class Apple:

    s_appleWindow = cv2.imread('.//assets//fgo//battle//appleWindow.png')
    s_copperAppleImage = cv2.imread('.//assets//fgo//battle//copperApple.png')
    s_silverAppleImage = cv2.imread('.//assets//fgo//battle//silverApple.png')
    s_OKBtnImage = cv2.imread('.//assets//fgo//battle//ok.png')

    def checkAppleWindow(device: Device):

        Logger.info('Checking apple window...')
        result, _ = MatchUtil.WaitFor(device, Apple.s_appleWindow, 2)

        if not result:
            Logger.info('No apple window')
            return False
        else:
            Logger.info('Having apple window, Eat apple')
            if not Apple.eatApple(device):
                Logger.error('Failed to eat apple')
                return False
            return True


    def eatApple(device: Device):
        device.swipe(640, 400, 640, 200)
        time.sleep(1)
        if not MatchUtil.TapImage(device, Apple.s_silverAppleImage):
            Logger.error('Failed to identify apple')
            return False
        timer = 0
        Tapped = False
        while timer < 5:
            time.sleep(0.5)
            device.screenshot()
            result = MatchUtil.match(device.getScreenshot(), Apple.s_OKBtnImage)
            if MatchUtil.isMatch(result):
                Logger.info('OK window is not close')
                if MatchUtil.TapImage(device, Apple.s_OKBtnImage):
                    Tapped = True
            else:
                if Tapped:
                    Logger.info('apple eaten.')
                    return True
            timer += 1
            time.sleep(1)

        
