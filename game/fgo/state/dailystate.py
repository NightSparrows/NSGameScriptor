
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

    def __init__(self, device: Device, gameData: GameData) -> None:
        super().__init__('Daily')
        self._data = gameData
        self._device = device

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
                return True
            
            # 往下滑
            self._device.swipe(1000, 500, 1000, 200)
        
        Logger.warn('Failed to enter daily state')
        return False



    def detect(self):
        raise NotImplementedError('state detect() not impl.')

    def getParentName(self):
        return 'Gate'
