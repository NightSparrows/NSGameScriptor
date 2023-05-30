
import cv2

from core.game.state import State
from core.logger import Logger
from core.device.device import Device
from core.matchutil import MatchUtil
from core.game.gamedata import GameData

# the init state of FGO
class LobbyState(State):
    
    def __init__(self, device: Device, gameData: GameData) -> None:
        super().__init__('Lobby')
        self._data = gameData
        self._device = device
        self._annImage = cv2.imread('.//assets//fgo//stateDetect//lobby.png')
        self._stoneImg = cv2.imread('./assets/fgo/state/lobby/stone.png')

    def goback(self):
        Logger.warn('The lobby state is the init state, cant go back')
        return False

    def enter(self):
        
        if self.detect():
            return True

        Logger.warn('Maybe future will implement this function(Lobby state::enter())')
        return False

    def detect(self):

        self._device.screenshot()
        screenshot = self._device.getScreenshot()

        result = MatchUtil.match(screenshot[0:100, 0:400], self._annImage)

        havingStone = MatchUtil.HavinginRange(self._device, self._stoneImg, 217, 565, 40, 40)

        if MatchUtil.isMatch(result) and havingStone:
            Logger.trace('Is in lobby')
            return True

        return False

    def getParentName(self):
        return 'None'


