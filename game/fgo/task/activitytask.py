
import cv2
import datetime
import time

from core.logger import Logger
from core.game.task import Task
from core.game.statemanager import StateManager
from core.matchutil import MatchUtil

from game.fgo.battle.battle import Battle
from game.fgo.state.activitystate import ActivityState

from game.fgo.battle.apple import Apple

class ActivityTask(Task):

    # areaName: 關卡所在地區
    # levelName: 關卡名稱
    # battle: 給serializer寫入battle instance
    # count: 執行次數
    # interval: 執行間隔
    def __init__(self, stateManager: StateManager, game, areaName: str, levelName: str, battle: Battle, count: int, interval: datetime.timedelta, date: datetime, enable: bool = True) -> None:
        super().__init__('ActivityTask', date, enable)
        self._stateManager = stateManager
        self._activityState = game.activityState
        self._device = game._device
        self._levelName = levelName
        self._areaName = areaName
        self._battle = battle
        self._count = count
        self._interval = interval
        self._btnImage = cv2.imread('./assets/fgo/activity/' + self._activityState._activityName + '/' + self._areaName + '/' + self._levelName + '.png')
    
    def findBtnAndPress(self):
        self._device.tap(1259, 150)
        time.sleep(1)

        isPress = False
        for i in range(5):
            # tap
            if MatchUtil.TapImage(self._device, self._btnImage):
                isPress = True
                break

            self._device.swipe(1000, 500, 1000, 200)
            time.sleep(1)

        if not isPress:
            Logger.error('Failed to press the button: ' + self._levelName)
            return False
        
        return True
        


    def execute(self):

        if not self._stateManager.goto('Activity'):
            Logger.error('無法進入活動頁面')
            return False

        if not self._activityState.gotoLevel(self._areaName):
            Logger.error('無法進入活動地區頁面')
            return False
        

        remainingCount = self._count

        while True:
            # 尋找關卡按鈕
            if not self.findBtnAndPress():
                return False

            # check apple window
            Apple.checkAppleWindow(self._device)

            # in battle
            result, count = self._battle.execute(remainingCount)
            remainingCount -= count
            
            if remainingCount == 0:
                break
    
        MatchUtil.WaitFor(self._device, self._btnImage, 10)

        # 案返回返回到 activity state
        for i in range(5):
            self._device.tap(108, 42)
            time.sleep(1)

            if self._activityState.detect():
                break

        self.m_date = datetime.datetime.now() + self._interval

        Logger.info('activity task complete')

        return True
    
    def getInfo(self):
        return '打活動副本[' + self._areaName + ':' + self._levelName + ']'

