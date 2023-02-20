
import time
import cv2

from .device.device import Device

class MatchUtil:

    s_waitInterval = 1.0

    def pressUntilAppear(device: Device, template, x: int, y: int, timeout: float):
        
        timer = 0

        while timer <= timeout:

            device.screenshot()

            screenshot = device.getScreenshot()

            result = MatchUtil.match(screenshot, template=template, method=cv2.TM_CCOEFF_NORMED)

            if result['max_val'] > 0.9:
                time.sleep(MatchUtil.s_waitInterval)
                return True
            else:
                # press
                device.tap(x, y)
            
            time.sleep(MatchUtil.s_waitInterval)
            timer += MatchUtil.s_waitInterval

        
        return False

    def pressUntilDisappear(device: Device, template, x: int, y: int, timeout: float):
        
        timer = 0

        while timer <= timeout:

            device.screenshot()

            screenshot = device.getScreenshot()

            result = MatchUtil.match(screenshot, template=template, method=cv2.TM_CCOEFF_NORMED)

            if result['max_val'] > 0.9:
                # press
                device.tap(x, y)
                time.sleep(MatchUtil.s_waitInterval)
                timer += MatchUtil.s_waitInterval
            else:
                time.sleep(MatchUtil.s_waitInterval)
                return True
            
            time.sleep(MatchUtil.s_waitInterval)
            timer += MatchUtil.s_waitInterval

        
        return False

    def setWaitInterval(interval: float):
        MatchUtil.s_waitInterval = interval

    def match(image, template, method = cv2.TM_CCOEFF_NORMED):
        result = cv2.matchTemplate(image, templ=template, method=method)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        return {'min_val':min_val, 'max_val':max_val, 'min_loc':min_loc, 'max_loc':max_loc}

    def isMatch(result):
        return result['max_val'] > 0.9

    def WaitFor(device: Device, template, timeout: float):

        timer = 0

        while timer <= timeout:

            device.screenshot()

            screenshot = device.getScreenshot()

            result = MatchUtil.match(screenshot, template=template, method=cv2.TM_CCOEFF_NORMED)

            if result['max_val'] > 0.9:
                return True, result
            
            time.sleep(MatchUtil.s_waitInterval)
            timer += MatchUtil.s_waitInterval

        
        return False, None


    def Having(device: Device, template):
        device.screenshot()
        screenshot = device.getScreenshot()
        result = MatchUtil.match(screenshot, template=template, method=cv2.TM_CCOEFF_NORMED)

        if result['max_val'] > 0.9:
            return True
        
        return False
            







        


