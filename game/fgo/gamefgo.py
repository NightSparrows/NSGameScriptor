
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
        self._appleType = 'gold'

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
        self.initStates()
        return True

        #if self.lobbyState.enter():
        #    self.initStates()
        #    return True
        
        #return self.restart()

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


    # confirm the game is actually up and in a known-good state before
    # running anything - if it's not (app closed, crashed, or stuck
    # somewhere uncertain from a previous run), restart it. This is what
    # init()'s commented-out lobbyState.enter()/restart() fallback was
    # originally meant to do; re-enabled here as its own method so both
    # execute() and runTask() (the GUI's single-task "立即執行" bypasses
    # execute() entirely) go through it.
    def ensureReady(self) -> bool:
        if not self._device.ensureEmulatorRunning():
            Logger.error('模擬器無法啟動')
            return False

        if self.lobbyState.detect():
            return True

        Logger.warn('未偵測到穩定畫面 (遊戲可能已關閉或卡住)，嘗試重新啟動遊戲')
        try:
            return self.restart()
        except Exception as e:
            # restart() isn't defensive internally (e.g. a killApp/openApp
            # adb call failing outright) - ensureReady()'s contract is to
            # return a bool, never raise, so callers (execute()/runTask())
            # can handle "couldn't get ready" as a normal failure instead
            # of an uncaught exception blowing up the whole task run.
            Logger.error('重新啟動遊戲時發生例外: ' + str(e))
            return False

    def execute(self):
        if not self.ensureReady():
            Logger.error('無法確保遊戲穩定，跳過本次執行')
            return
        self._taskManager.execute()

    # return
    # -1: 非法ID
    # -2: 執行失敗
    # -3: 無法確保遊戲穩定 (重啟失敗)
    def runTask(self, id: int) -> int:
        if not self.ensureReady():
            Logger.error('無法確保遊戲穩定，跳過本次執行')
            return -3
        return self._taskManager.runTask(id)

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
        # was 'jp.delightworks.Fgo.player.AndroidPlugin' - a client update
        # switched the launcher activity to Unity's own, confirmed live via
        # `adb shell cmd package resolve-activity --brief com.xiaomeng.fategrandorder`
        result = self._device.openApp('com.xiaomeng.fategrandorder/com.unity3d.player.UnityPlayerActivity')

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

        # 關閉登入後可能跳出的其他視窗 (友情點數等獎勵確認彈窗等)
        time.sleep(1)
        closeBtnImages = [Asset.CloseBtnImage, Asset.CloseBtnPillImage]
        while MatchUtil.TapAnyImage(self._device, closeBtnImages):
            time.sleep(2)

        safty = False
        for i in range(10):
            if self.lobbyState.detect():
                safty = True
                break
            time.sleep(0.25)

        if not safty:
            Logger.error('無法確認穩定狀態')
            return False
        

        self.initStates()

        return True


