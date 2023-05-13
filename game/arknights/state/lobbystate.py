

import cv2

from core.matchutil import MatchUtil
from core.logger import Logger
from core.game.state import State

from core.game.gamedata import GameData
from core.device.device import Device


class LobbyState(State):

    def __init__(self, device: Device, data: GameData) -> None:
        super().__init__('Lobby')
        self._device = device
        self._data = data
        self._friendBtn = cv2.imread('assets/arknights/state/lobby/friendBtn.png')

    def goback(self):
        Logger.error('Cant go back in init state(Lobby)')
        raise NotImplementedError()


    def enter(self):
        raise NotImplementedError()

    def detect(self):
        
        if MatchUtil.HavinginRange(self._device, self._friendBtn, 260, 530, 200, 100):   # already in lobby state
            return True
        
        return False

    def getParentName(self):
        return 'None'