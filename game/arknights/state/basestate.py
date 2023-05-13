
import cv2
import time

from core.matchutil import MatchUtil
from core.logger import Logger
from core.game.state import State

from core.game.gamedata import GameData

from core.matchutil import MatchUtil
from core.device.device import Device

class BaseState(State):

    def __init__(self, device: Device, data: GameData) -> None:
        super().__init__('Base')

        self._device = device
        self._data = data

        self._robotIcon = cv2.imread('assets/arknights/state/base/robotIcon.png')

    
    def enter(self) -> bool:
        assert(self._data.currentState == self.getParentName())

        
        # TODO 我現在懶得做穩定性 improve some tweak

        while not self.detect():
            self._device.tap(1015, 640)
            time.sleep(1)

        return True



    def goback(self) -> bool:
        assert(self._data.currentState == self.getName())

        while True:
            self._device.tap(90, 40)
            time.sleep(1)
            if not self.detect():
                break
            # TODO 計時的API
        
        return True

    def detect(self) -> bool:

        if MatchUtil.HavinginRange(self._device, self._robotIcon, 680, 0, 90, 65):
            return True
        
        return False

    def getParentName(self) -> str:
        return 'Lobby'
