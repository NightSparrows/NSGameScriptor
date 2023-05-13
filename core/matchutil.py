
import time
import cv2
import numpy as np

from .device.device import Device

class MatchUtil:

    s_threshhold = 0.95
    s_waitInterval = 1.0

    def TapImage(device: Device, template, thresh = 0.9):
        device.screenshot()
        result = MatchUtil.match(device.getScreenshot(), template)
        if MatchUtil.isMatch(result, thresh):
            point = MatchUtil.calculated(result, template.shape)
            device.tap(point['x']['center'], point['y']['center'])
            time.sleep(1)
            return True
        
        return False

    def MatchColor(color, r: int, g: int, b: int):
        if color[0] == b and color[1] == g and color[2] == r:
            return True
        return False

    def PressUntilColorChange(device: Device, x: int, y: int, timeout: float):

        timer = 0

        device.screenshot()

        screenshot = device.getScreenshot()
        
        color = screenshot[y, x]

        while timer <= timeout:

            device.tap(x, y)
            time.sleep(1)

            device.screenshot()
            screenshot = device.getScreenshot()

            newColor = screenshot[y, x]
            if not MatchUtil.MatchColor(color, newColor[2], newColor[1], newColor[0]):
                return True
            
            timer += 1
        
        # timeout
        return False





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

    def matchMultiple(image, template, thresh = 0.9, method = cv2.TM_CCOEFF_NORMED):
        result = cv2.matchTemplate(image, templ=template, method=method)

        (y_points, x_points) = np.where(result >= thresh)

        matches = list()
        for (x, y) in zip(x_points, y_points):
            matches.append((x, y))

        return matches


    def isMatch(result, thresh = 0.9):
        return result['max_val'] > thresh

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

    def WaitForInRange(device: Device, template, timeout: float, x, y, width, height):
        
        timer = 0

        while timer <= timeout:

            device.screenshot()

            screenshot = device.getScreenshot()

            result = MatchUtil.match(screenshot[y:(y+height), x:(x+width)], template=template, method=cv2.TM_CCOEFF_NORMED)

            if result['max_val'] > 0.9:
                return True, result
            
            time.sleep(MatchUtil.s_waitInterval)
            timer += MatchUtil.s_waitInterval

        
        return False, None


    def Having(device: Device, template):
        device.screenshot()
        screenshot = device.getScreenshot()
        result = MatchUtil.match(screenshot, template=template, method=cv2.TM_CCOEFF_NORMED)

        if MatchUtil.isMatch(result):
            return True
        
        return False
    
    def HavinginRange(device: Device, template: cv2.Mat, x, y, width, height):
        device.screenshot()
        screenshot = device.getScreenshot()
        result = MatchUtil.match(screenshot[y:(y+height), x:(x+width)], template=template, method=cv2.TM_CCOEFF_NORMED)

        if MatchUtil.isMatch(result):
            return True
        
        return False

    
    def calculated(result, shape):
        mat_top, mat_left = result['max_loc']
        prepared_height, prepared_width, prepared_channels = shape

        x = {
            'left': int(mat_top),
            'center': int((mat_top + mat_top + prepared_width) / 2),
            'right': int(mat_top + prepared_width),
        }

        y = {
            'top': int(mat_left),
            'center': int((mat_left + mat_left + prepared_height) / 2),
            'bottom': int(mat_left + prepared_height),
        }

        return {
            'x': x,
            'y': y,
        }








        


