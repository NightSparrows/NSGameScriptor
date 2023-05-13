
import time
import cv2

from core.game.game import Game
from core.device.device import Device
from core.logger import Logger

from core.matchutil import MatchUtil

from .state.lobbystate import LobbyState
from .state.basestate import BaseState

class GameArknights(Game):

    def __init__(self, device: Device) -> None:
        super().__init__('Arknights')
        self._device = device

        self._lobbyState = LobbyState(self._device, self._data)
        self._baseState = BaseState(self._device, self._data)

    def execute(self):
        raise NotImplementedError('Arknight execute() not impl.')
    
    def init(self):
        Logger.info('Arknights 初始化中 ...')

        #if self._lobbyState.enter():
        #    Logger.info('Already in init state.')
        #    self.initStates()
        #    return True
        
        return self.restart()

    def initStates(self):
        # in 大廳
        self._stateManager.init(self._lobbyState)
        self._stateManager.addState(self._baseState)

    def restart(self):
        Logger.info('Restarting Arknights ... ')

        self._device.killApp('tw.txwy.and.arknights')
        self._device.openApp('tw.txwy.and.arknights/com.u8.sdk.U8UnityContext')

        # startup resources
        startBtn = cv2.imread('assets/arknights/state/login/startBtn.png')
        loginBtn = cv2.imread('assets/arknights/state/login/loginBtn.png')

        # TODO 更新的自動化

        successfulInLobby = False

        while True:

            time.sleep(1)
            if MatchUtil.HavinginRange(self._device, startBtn, 590, 640, 100, 80):
                self._device.tap(640, 680)
            elif MatchUtil.HavinginRange(self._device, loginBtn, 540, 480, 200, 70):
                self._device.tap(640, 510)
            elif self._lobbyState.detect():
                successfulInLobby = True
                break

        if not successfulInLobby:
            return False

        self.initStates()

        return True




