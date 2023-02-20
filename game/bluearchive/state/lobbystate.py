
import cv2

from core.matchutil import MatchUtil
from core.logger import Logger
from core.game.state import State

from core.game.gamedata import GameData

class LobbyState(State):

    def __init__(self, device) -> None:
        super().__init__('Lobby')
        self.iconImage = cv2.imread('assets/bluearchive/state/lobby/lobbyIcon.png')
        self.homeBtnImage = cv2.imread('assets/bluearchive/state/lobby/homeBtn.png')
        self._device = device

    def goback(self):
        Logger.error('Cant go back in init state(Lobby)')
        raise NotImplementedError()

    def enter(self):

        if not MatchUtil.pressUntilDisappear(self._device, self.homeBtnImage,1234, 25, 2):
            return False

        return True

    def detect(self):
        self._device.screenshot()
        if MatchUtil.isMatch(result = MatchUtil.match(self._device.getScreenshot(), self.iconImage)):
            return True
        return False

    def getParentName(self):
        return 'None'

    

