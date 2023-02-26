
import cv2

from core.matchutil import MatchUtil
from core.logger import Logger
from core.game.state import State

from core.game.gamedata import GameData
from core.device.device import Device

class LobbyState(State):

    def __init__(self, device: Device, data: GameData) -> None:
        super().__init__('Lobby')
        self.iconImage = cv2.imread('assets/bluearchive/state/lobby/lobbyIcon.png')
        self.homeBtnImage = cv2.imread('assets/bluearchive/state/lobby/homeBtn.png')
        self._device = device
        self._data = data

    def goback(self):
        Logger.error('Cant go back in init state(Lobby)')
        raise NotImplementedError()

    def enter(self):

        if self.detect():   # already in lobby state
            return True
        
        if not MatchUtil.TapImage(self._device, self.homeBtnImage):
            return False

        if not MatchUtil.WaitFor(self._device, self.iconImage, 5):
            # exception connection lost 之類的
            Logger.error('Failed to wait to lobby state')
            return False

        self._data.currentState = self.getName()
        Logger.trace('Lobby entered.')

        return True

    def detect(self):
        
        if MatchUtil.Having(self._device, self.iconImage):   # already in lobby state
            return True
        
        return False

    def getParentName(self):
        return 'None'

    

