
import time
import cv2

from core.logger import Logger
from core.device.device import Device
from core.matchutil import MatchUtil
from core.util.timer import Timer

class Apple:

    s_appleWindow = cv2.imread('.//assets//fgo//battle//appleWindow.png')
    s_copperAppleImage = cv2.imread('.//assets//fgo//battle//copperApple.png')
    s_silverAppleImage = cv2.imread('.//assets//fgo//battle//silverApple.png')
    s_goldAppleImage = cv2.imread('.//assets//fgo//battle//goldApple.png')
    s_OKBtnImage = cv2.imread('.//assets//fgo//battle//ok.png')

    s_appleTypeName = 'gold'

    def checkAppleWindow(device: Device):

        Logger.info('Checking apple window...')
        result, _ = MatchUtil.WaitFor(device, Apple.s_appleWindow, 2)

        if not result:
            Logger.info('No apple window')
            return False
        else:
            Logger.info('Having apple window, Eat apple')
            if not Apple.eatApple(device, Apple.s_appleTypeName):
                Logger.error('Failed to eat apple')
                return False
            return True


    def eatApple(device: Device, appleType: str = 'gold'):

        if appleType == 'gold':
            apple = Apple.s_goldAppleImage
        elif appleType == 'silver':
            apple = Apple.s_silverAppleImage
        elif appleType == 'copper':
            apple = Apple.s_copperAppleImage
        else:
            Logger.error('Unknown apple type')
            return False

        Tapped = False
        timer = Timer(5)
        timer.restart()
        while not timer.timeout():
            
            if not MatchUtil.TapImage(device, apple):
                Logger.info('Apple ' + appleType + ' not found, swipe.')
                device.swipe(640, 400, 640, 200)
                time.sleep(1)
            else:
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

        
        return False

        
