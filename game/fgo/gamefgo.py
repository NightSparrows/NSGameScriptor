
import time
import cv2
import json

from core.logger import Logger
from core.device.device import Device
from core.game.game import Game
from core.matchutil import MatchUtil

from game.fgo.asset import Asset
from game.fgo.battle.battle import Battle
from game.fgo.state.lobbystate import LobbyState
from game.fgo.state.activitystate import ActivityState


class GameFGO(Game):

    def __init__(self, device: Device) -> None:
        super().__init__('fgo')

        self._device = device
        
        self.lobbyState = LobbyState(self._device, self._data)

        self._battles = dict[Battle]()

        # Data
        try:
            with open('config/fgo/data.json') as f:
                self._configData = json.load(f)
        except:
            # 沒有檔案
            Logger.error('No FGO config data!')

        activityData = dict()
        if self._configData['activityName'] != None:
            try:
                configFilePath = 'config/fgo/activity/' + self._configData['activityName'] + '.json'
                with open(configFilePath, encoding='utf-8') as f:
                    Logger.info('Open file successfully')
                    activityData = json.load(f)
            except Exception as e:
                # 沒有檔案
                Logger.error('Failed to read FGO config data!: ' + configFilePath)
                Logger.error(e)
                activityData['current'] = 'None'

        self.activityState = ActivityState(self._device, self._data, activityData)


    def init(self):

        if self.lobbyState.enter():
            self.initStates()
            return True
        
        return self.restart()

    def execute(self):
        self._taskManager.execute()

    def initStates(self):
        # in 大廳
        self._stateManager.init(self.lobbyState)

        self._stateManager.addState(self.activityState)
        # TODO other states

    def restart(self):
        
        Logger.info('Restarting Fate Grand Order ... ')

        # TODO mycard版本的切換
        self._device.killApp('com.xiaomeng.fategrandorder')
        result = self._device.openApp('com.xiaomeng.fategrandorder/jp.delightworks.Fgo.player.AndroidPlugin')

        annImage = cv2.imread('./assets/fgo/stateDetect/announcement.png')

        Logger.info('等待公告畫面...')
        # TODO 下載更新
        waitResult = MatchUtil.pressUntilAppear(self._device, annImage, 150, 400, 60)
        if not waitResult:
            Logger.error('無法等到公告畫面')
            return False
        
        # 等到公告畫面
        # 關閉公告
        self._device.tap(1275, 5)
        time.sleep(1)

        # TODO 視窗 for closing
        time.sleep(1)
        while MatchUtil.TapImage(self._device, Asset.CloseBtnImage):
            time.sleep(2)

        safty = False
        for i in range(10):
            if self.lobbyState.detect():
                safty = True
                break
            time.sleep(1)

        if not safty:
            Logger.error('無法確認穩定狀態')
            return False
        

        self.initStates()

        return True


