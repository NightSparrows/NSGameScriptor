
import cv2

class ScreenCap:


    def screenshot(self) -> bool:
        raise NotImplementedError()
    
    def screenshot_save(self):
        self.screenshot()

        # TODO 只有nemu Screenshot對
        cv2.imwrite('screenshot.png', self.m_image)

        return

    def getScreenshot(self):
        raise NotImplementedError()
