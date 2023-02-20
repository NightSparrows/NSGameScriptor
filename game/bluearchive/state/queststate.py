
import cv2
import time

from core.matchutil import MatchUtil
from core.logger import Logger
from core.game.state import State

from core.game.gamedata import GameData

from ..asset import Asset

# 任務state: 有主線
class QuestState(State):

    def __init__(self, device, data: GameData) -> None:
        super().__init__('Quest')
        self.iconImage = cv2.imread('assets/bluearchive/state/quest/icon.png')
        self.folderBtnImage = cv2.imread('assets/bluearchive/state/quest/folderBtn.png')
        self._device = device
        self._data = data

    def goback(self):
        assert(self._data.currentState == self.getName())

        return MatchUtil.pressUntilDisappear(self._device, self.iconImage, 57, 36, 3)


    def enter(self):

        assert(self._data.currentState == 'Lobby')

        timer = 0
        while timer <= 10:
            self._device.screenshot()
            result = MatchUtil.match(self._device.getScreenshot(), self.folderBtnImage)

            if not MatchUtil.isMatch(result):
                self._device.tap(640, 360)
                time.sleep(1)
            else:
                if MatchUtil.pressUntilDisappear(self._device, self.folderBtnImage, 1200, 578, 4):
                    
                    have, result = MatchUtil.WaitFor(self._device, self.iconImage, 5)
                    if have:
                        self._data.currentState = self.getName()
                        Logger.trace('Entered Quest State')
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
        return 'Lobby'

    

