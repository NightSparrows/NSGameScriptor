
import cv2
import time

from core.matchutil import MatchUtil
from core.logger import Logger
from core.game.state import State

from core.game.gamedata import GameData

from ..asset import Asset

# 任務state: 有主線
class MainQuestState(State):

    def __init__(self, device, data: GameData) -> None:
        super().__init__('MainQuest')
        self.iconImage = cv2.imread('assets/bluearchive/state/mainquest/icon.png')
        self.enterBtnImage = cv2.imread('assets/bluearchive/state/quest/icon.png')
        self.hardOffImage = cv2.imread('assets/bluearchive/state/mainquest/hardOff.png')
        self.hardOnImage = cv2.imread('assets/bluearchive/state/mainquest/hardOn.png')
        
        # load quest area images
        self.areaIconImages = []
        for i in range(1, 8):
            self.areaIconImages.append(cv2.imread('assets/bluearchive/state/mainquest/area' + str(i) + '.png'))

        
        self._device = device
        self._data = data

    def switch(self, areaNo: int):

        assert(self._data.currentState == self.getName())

        self._device.screenshot()

        screenshot = self._device.getScreenshot()

        currentAreaNo = -1
        for i in range(len(self.areaIconImages)):
            result = MatchUtil.match(screenshot, self.areaIconImages[i])

            if MatchUtil.isMatch(result):
                currentAreaNo = i + 1
                break

        assert(currentAreaNo != -1)
        Logger.info('Current area is ' + str(currentAreaNo))

        if currentAreaNo > areaNo:
            pressPageX = 40
        elif currentAreaNo == areaNo:                     # already on this page
            Logger.trace('already on this page')
            return True
        else:
            pressPageX = 1245
        
        pressCount = abs(currentAreaNo - areaNo)

        for i in range(pressCount):
            self._device.tap(pressPageX, 360)
            time.sleep(1)
        
        self._device.screenshot()
        screenshot = self._device.getScreenshot()

        if MatchUtil.isMatch(MatchUtil.match(screenshot, self.areaIconImages[areaNo - 1])):
            Logger.info('Switch to area ' + str(areaNo) + ' successfully')
            return True
        else:
            Logger.error('Failed to switch to area ' + str(areaNo))
            return False




    def goback(self):
        assert(self._data.currentState == self.getName())

        return MatchUtil.pressUntilDisappear(self._device, self.iconImage, 57, 36, 3)


    def enter(self):

        assert(self._data.currentState == 'Quest')

        timer = 0
        while timer <= 10:
            self._device.screenshot()
            result = MatchUtil.match(self._device.getScreenshot(), self.enterBtnImage)

            if MatchUtil.pressUntilDisappear(self._device, self.enterBtnImage, 825, 269, 4):
                
                # TODO 通知
                self._device.tap(1270, 50)
                time.sleep(1)

                have, result = MatchUtil.WaitFor(self._device, self.iconImage, 5)
                if have:
                    Logger.trace('Entered MainQuest State')
                    self._data.currentState = self.getName()
                    return True
                else:
                    Logger.error('Unknown page cant find quest icon image')
                    return False
            
            timer += 1
            time.sleep(1)
                

        return False

    def detect(self):
        self._device.screenshot()
        if MatchUtil.isMatch(result = MatchUtil.match(self._device.getScreenshot(), self.iconImage)):
            return True
        return False

    def getParentName(self):
        return 'Quest'

    

