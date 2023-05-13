
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
from game.fgo.state.gatestate import GateState
from game.fgo.state.dailystate import DailyState



class GameFGO(Game):

    def __init__(self, device: Device) -> None:
        super().__init__('fgo')

        self._device = device
        
        self.lobbyState = LobbyState(self._device, self._data)
        self.gateState = GateState(self._device, self._data)
        self.dailyState = DailyState(self._device, self._data)

        self._battles = dict[Battle]()

        # Data
        try:
            with open('config/fgo/data.json', encoding='utf-8') as f:
                self._configData = json.load(f)
        except:
            # 沒有檔案
            Logger.error('No FGO config data!')

        activityData = dict()
        if self._configData['activityName'] != 'None':
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
        else:
            activityData['current'] = 'None'
            activityData['button'] = ''
            activityData['level'] = []

        self.activityState = ActivityState(self._device, self._data, activityData)


    def init(self):

        if self.lobbyState.enter():
            self.initStates()
            return True
        
        return self.restart()

    def getKeyFromBattle(self, battle: Battle) -> str:

        for key in self._battles:
            if self._battles[key] == battle:
                return key
            
        return None

    def getBattleFromKey(self, keyName: str) -> Battle:

        for key in self._battles:
            if key == keyName:
                return self._battles[key]
        
        return None


    def execute(self):
        self._taskManager.execute()

    def initStates(self):
        # in 大廳
        self._stateManager.init(self.lobbyState)

        self._stateManager.addState(self.activityState)
        self._stateManager.addState(self.gateState)
        self._stateManager.addState(self.dailyState)
        # TODO other states

    def restart(self):
        
        Logger.info('Restarting Fate Grand Order ... ')

        # TODO mycard版本的切換
        self._device.killApp('com.xiaomeng.fategrandorder')
        result = self._device.openApp('com.xiaomeng.fategrandorder/jp.delightworks.Fgo.player.AndroidPlugin')

        # load some startup resources
        annImage = cv2.imread('./assets/fgo/stateDetect/announcement.png')
        startUpdateBtn = cv2.imread('./assets/fgo/etc/updateBtn.png')
        blankNoTouchScreen = cv2.imread('./assets/fgo/etc/blank.png')
        loadingImage = cv2.imread('./assets/fgo/etc/loading.png')
        servantImage = cv2.imread('./assets/fgo/etc/servant.png')

        Logger.info('等待公告畫面...')


        # 0 = startup
        # 1 = updating
        # 2 = waitForTouch
        # 3 = inLoginScreen
        # 4 = inLobby
        currentState = 0

        Logger.trace('wait for loading')
        while not MatchUtil.HavinginRange(self._device, loadingImage, 920, 670, 160, 50):
            time.sleep(0.5)

        Logger.trace('loading waited.')
        while True:

            time.sleep(1)
            if currentState == 0:
                isNeedUpdate = MatchUtil.Having(self._device, startUpdateBtn)
                if isNeedUpdate:
                    if MatchUtil.TapImage(self._device, startUpdateBtn, 0.95):
                        currentState = 1
                        continue
                    else:
                        Logger.error('無法按更新按鈕')
                        continue
                else:
                    if MatchUtil.HavinginRange(self._device, servantImage, 450, 0, 400, 100): # in wait state
                        self._device.tap(150, 400)
                    else:
                        # 已經不在loading state
                        currentState = 3

            elif currentState == 1:
                # TODO 無法連線
                currentState = 0
                pass
            elif currentState == 2:
                pass
            elif currentState == 3:
                waitResult = MatchUtil.pressUntilAppear(self._device, annImage, 150, 400, 60)
                if not waitResult:
                    Logger.error('無法等到公告畫面')
                    return False
                else:
                    currentState = 4
                    continue
            elif currentState == 4:
                break
            else:
                pass

        
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


