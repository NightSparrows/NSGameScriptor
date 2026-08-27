
import cv2

from core.game.state import State
from core.logger import Logger
from core.device.device import Device
from core.matchutil import MatchUtil
from core.game.gamedata import GameData

# the init state of FGO
class LobbyState(State):

    # top-left "公告" pill button, checked via edge-IoU rather than raw
    # pixel matching: the previous approach (matching the whole pill
    # region, plus a second check on a "stone" resource icon elsewhere on
    # screen) turned out to false-positive on the Gate screen - its "關閉"
    # pill has the same shape/position/border as Lobby's "公告" pill (only
    # the 2 glyphs differ), and the stone-icon check landed on a plain
    # patch of the character's clothing where normalized template matching
    # is numerically unstable (near-zero variance) and reported a match
    # that wasn't there. Narrowing to just the glyph area and comparing
    # edge structure discriminates cleanly (verified against live
    # screenshots: ~0.98 IoU on real Lobby shots vs ~0.15 on Gate/Daily).
    s_announcementRegion = (68, 22, 100, 45)  # x, y, width, height

    def __init__(self, device: Device, gameData: GameData) -> None:
        super().__init__('Lobby')
        self._data = gameData
        self._device = device
        self._announcementEdgeMask = cv2.imread('./assets/fgo/state/lobby/announcementEdgeMask.png', cv2.IMREAD_GRAYSCALE)

    def goback(self):
        Logger.warn('The lobby state is the init state, cant go back')
        return False

    def enter(self):

        if self.detect():
            return True

        Logger.warn('Maybe future will implement this function(Lobby state::enter())')
        return False

    def detect(self):
        if MatchUtil.HavingEdgeInRange(self._device, self._announcementEdgeMask, *LobbyState.s_announcementRegion):
            Logger.trace('Is in lobby')
            return True

        return False

