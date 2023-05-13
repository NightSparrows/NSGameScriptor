
import time
import cv2

from core.logger import Logger

from core.game.game import Game

from core.device.device import Device
from core.matchutil import MatchUtil

from .state.lobbystate import LobbyState
from .state.queststate import QuestState
from .state.mainqueststate import MainQuestState

from .asset import Asset

class GameBlueArchive(Game):

    def __init__(self, device: Device) -> None:
        super().__init__('BlueArchive')
        self._device = device

        # loading states
        self.lobbyState = LobbyState(self._device, self._data)
        self.questState = QuestState(self._device, self._data)
        self.mainQuestState = MainQuestState(self._device, self._data)


    
    def execute(self):

        self.init()

        self._taskManager.execute()

    def init(self):
        Logger.info('Blue archive 初始化中 ...')
        if self.lobbyState.enter():
            Logger.info('Already in init state.')
            self.initStates()
            return True
        
        return self.restart()

    def initStates(self):
        # in 大廳
        self._stateManager.init(self.lobbyState)
        self._stateManager.addState(self.questState)
        self._stateManager.addState(self.mainQuestState)

    def restart(self):

        Logger.info('Restarting Blue archive ... ')

        self._device.killApp('com.nexon.bluearchive')
        result = self._device.openApp('com.nexon.bluearchive/.MxUnityPlayerActivity')

        Logger.trace(str(result))

        # 進入大廳

        # TODO 確認更新視窗

        # TODO 重寫，每個loop都偵測是否在大廳，或開始畫面，或更新視窗... etc
        
        iconImage = cv2.imread('assets/bluearchive/login/startIcon.png')
        annImage = cv2.imread('assets/bluearchive/login/announcementText.png')
        updateWin = cv2.imread('assets/bluearchive/login/updateWin.png')
        
        
        foundLobby = False
        timer = 0
        tapX = 100
        tapY = 687
        while timer <= 60:
            self._device.screenshot()

            screenshot = self._device.getScreenshot()

            if MatchUtil.isMatch(result = MatchUtil.match(screenshot, iconImage)):       # 在開始畫面
                Logger.info('在開始畫面...')
                tapX = 640
                tapY = 120
                self._device.tap(640, 120)
                time.sleep(0.5)
            elif MatchUtil.isMatch(result = MatchUtil.match(screenshot, annImage)):
                Logger.info('在公告視窗')
                if not MatchUtil.pressUntilDisappear(self._device, annImage, 1178, 117, 5):
                    Logger.error('Failed to close 公告 window')
                    return False
                time.sleep(0.5)
                break
            elif MatchUtil.Having(self._device, updateWin):
                Logger.trace('有更新通知')
                self._device.tap(770, 510)
                time.sleep(1)
            else:
                self._device.tap(tapX, tapY)
                time.sleep(0.5)
        

            time.sleep(1)
            timer += 1

        if self.lobbyState.detect():
            Logger.info('In Lobby')
            foundLobby = True


        if not foundLobby:
            Logger.error('Failed to enter lobby state')
            return False

        self.initStates()
        
        return True

