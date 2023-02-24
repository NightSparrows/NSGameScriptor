
import cv2
import time

from core.game.state import State
from core.game.gamedata import GameData
from core.logger import Logger
from core.device.device import Device
from core.matchutil import MatchUtil

from game.fgo.asset import Asset



class GateState(State):

    def __init__(self, device: Device, gameData: GameData) -> None:
        super().__init__('Gate')
        self._data = gameData
        self._device = device
        self._titleImage = cv2.imread('.//assets//fgo//state//gate//title.png')
        self._enterBtnImage = cv2.imread('.//assets//fgo//state//gate//chaldeaGate.png')

    def goback(self):
        Logger.info('Try to go back from gate state')
        # assert is in this state
        if (self.m_data.currentState != self.getName()):
            Logger.warn('Current state not ' + self.getName() + ' cant go back.')
            return False
        
        time.sleep(1)
        self._device.screenshot()

        result = MatchUtil.match(self._device.getScreenshot(), Asset.gobackBtnImage)

        if MatchUtil.isMatch(result):
            point = MatchUtil.calculated(result, Asset.gobackBtnImage.shape)
            self._device.tap(point['x']['center'], point['y']['center'])
            # 沒有改current state是因為上一個state不一定是parent
            return True

        return False

    def detectGateBtnAndClick(self):

        self._device.screenshot()
        result = MatchUtil.match(self._device.getScreenshot(), self._enterBtnImage)

        if MatchUtil.isMatch(result):
            point = MatchUtil.calculated(result, self._enterBtnImage.shape)
            self._device.tap(point['x']['center'], point['y']['center'])
            return True

        return False


    def enter(self):
        # assert is in lobby state
        if (self.m_data.currentState != self.getParentName()):
            Logger.warn('Current state not ' + self.getParentName() + ' cant enter.')
            return False
        
        # 往上滑找嘉樂底按鈕
        pressed = False
        for i in range(1, 5):
            if (self.detectGateBtnAndClick()):
                pressed = True
                break
            else:
                self._device.swipe(1000, 200, 1000, 500)
                time.sleep(1)

        # 往下滑
        if not pressed:
            for i in range(1, 10):
                if (self.detectGateBtnAndClick()):
                    break
                else:
                    self._device.swipe(1000, 500, 1000, 200)
                    time.sleep(1)
        
        result,_ = MatchUtil.WaitFor(self._device, self._titleImage, 5)

        if not result:
            Logger.error('無法偵測已進入Gate')
            return False
        else:
            self._data.currentState = self.getName()
            Logger.info('entered Gate state')
            return True


    def detect(self):

        result, _ = MatchUtil.WaitForInRange(self._device, self._titleImage, 3, 500, 0, 780, 65)

        return result


    def getParentName(self):
        return str('Lobby')



