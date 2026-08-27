
import cv2

import time

from core.logger import Logger
from core.game.state import State
from core.device.device import Device
from core.game.gamedata import GameData
from core.matchutil import MatchUtil

from ..asset import Asset

class DailyState(State):

    s_dailyBtnImage = cv2.imread('.//assets//fgo//state//daily//dailyBtn.png')

    # same translucent-title situation as GateState - see the comment
    # there. Detected via edge-IoU at a fixed region rather than raw
    # pixel matching.
    s_titleRegion = (930, 5, 350, 55)  # x, y, width, height

    def __init__(self, device: Device, gameData: GameData) -> None:
        super().__init__('Daily')
        self._data = gameData
        self._device = device
        self._titleEdgeMask = cv2.imread('.//assets//fgo//state//daily//titleEdgeMask.png', cv2.IMREAD_GRAYSCALE)

    def goback(self):
        Logger.info('daily state go back')

        if self._data.currentState != self.getName():
            Logger.error('Current state is not daily!')
            return False
        
        time.sleep(1)
        if not MatchUtil.TapImage(self._device, Asset.gobackBtnImage):
            return False
        
        return True

    def detectDailyBtnAndClick(self):

        if not MatchUtil.TapImage(self._device, DailyState.s_dailyBtnImage):
            return False

        return True

    def enter(self):
        Logger.info('Entering daily state')
        # assert is in gate state
        if (self._data.currentState != 'Gate'):
            Logger.warn('Current state not gate cant enter.')
            return False

        self._device.tap(1258, 150)
        time.sleep(1)

        for i in range(10):
            time.sleep(1)
            if self.detectDailyBtnAndClick():
                if MatchUtil.WaitForEdgeInRange(self._device, self._titleEdgeMask, 5, *DailyState.s_titleRegion):
                    return True
                Logger.warn('Tapped daily button but did not detect the Daily title afterward')
                return False

            # 往下滑
            self._device.swipe(1000, 500, 1000, 200)

        Logger.warn('Failed to enter daily state')
        return False



    def detect(self):
        return MatchUtil.HavingEdgeInRange(self._device, self._titleEdgeMask, *DailyState.s_titleRegion)

    def getParentName(self):
        return 'Gate'
