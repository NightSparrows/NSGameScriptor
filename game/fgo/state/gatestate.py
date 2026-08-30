
import cv2
import time

from core.game.state import State
from core.game.gamedata import GameData
from core.logger import Logger
from core.device.device import Device
from core.matchutil import MatchUtil

from game.fgo.asset import Asset



class GateState(State):

    # top-right screen title ("迦勒底之門 Chaldea Gate") is rendered with a
    # semi-transparent background over Lobby's animated backdrop, so raw
    # pixel template matching against it is unreliable (the background
    # behind the text keeps changing on its own). Detected via edge-IoU
    # instead - see MatchUtil.HavingEdgeInRange/WaitForEdgeInRange. The
    # title's position is fixed (not part of any scrollable area), so no
    # sliding search is needed, just a fixed region check.
    s_titleRegion = (930, 5, 350, 55)  # x, y, width, height

    def __init__(self, device: Device, gameData: GameData) -> None:
        super().__init__('Gate')
        self._data = gameData
        self._device = device
        self._titleEdgeMask = cv2.imread('.//assets//fgo//state//gate//titleEdgeMask.png', cv2.IMREAD_GRAYSCALE)
        self._enterBtnImage = cv2.imread('.//assets//fgo//state//gate//chaldeaGate.png')
        self._enterBtn01Image = cv2.imread('.//assets//fgo//state//gate//chaldeaGate01.png')

    def goback(self):
        Logger.info('Try to go back from gate state')
        # assert is in this state
        if (self._data.currentState != self.getName()):
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

        if MatchUtil.TapImage(self._device, self._enterBtn01Image):
            return True

        self._device.screenshot()
        result = MatchUtil.match(self._device.getScreenshot(), self._enterBtnImage)

        if MatchUtil.isMatch(result):
            point = MatchUtil.calculated(result, self._enterBtnImage.shape)
            self._device.tap(point['x']['center'], point['y']['center'])
            return True

        # a reward/support popup (e.g. 友情點數) can pop up unprompted a few
        # seconds after entering Lobby, covering the swipeable area this
        # loop is scanning - close it so the next swipe/detect attempt can
        # actually see the Gate button underneath.
        if MatchUtil.TapAnyImage(self._device, [Asset.CloseBtnImage, Asset.CloseBtnPillImage]):
            return False

        return False


    def enter(self):
        # assert is in lobby state
        if (self._data.currentState != self.getParentName()):
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
        
        result = MatchUtil.WaitForEdgeInRange(self._device, self._titleEdgeMask, 5, *GateState.s_titleRegion)

        if not result:
            Logger.error('無法偵測已進入Gate')
            return False
        else:
            Logger.info('entered Gate state')
            return True


    def detect(self):
        return MatchUtil.HavingEdgeInRange(self._device, self._titleEdgeMask, *GateState.s_titleRegion)


    def getParentName(self):
        return str('Lobby')



