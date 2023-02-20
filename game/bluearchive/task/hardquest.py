
import time
import datetime
import cv2

from core.logger import Logger
from core.game.task import Task
from core.game.statemanager import StateManager
from core.matchutil import MatchUtil

from game.bluearchive.state.mainqueststate import MainQuestState

from game.bluearchive.asset import Asset

# 掃蕩3次困難圖
class HardQuestTask(Task):

    def __init__(self, stateManager: StateManager, mainQuestState: MainQuestState, areaNo: int, levelNo: int, date: datetime) -> None:
        super().__init__('HardQuest', date)
        self._stateManager = stateManager
        self._mainQuestState = mainQuestState
        self._areaNo = areaNo
        self._levelNo = levelNo
        self._device = self._mainQuestState._device
        self.notEnoughInfoImage = cv2.imread('assets/bluearchive/task/hardquest/notEnoughInfo.png')
        assert(self._levelNo <= 3)

    def execute(self):

        if not self._stateManager.goto('MainQuest'):
            Logger.error('Failed to goto Quest state in task (HardQuest)')
            return False
        
        # switch to current page
        if not self._mainQuestState.switch(areaNo=self._areaNo):
            Logger.error('[TASK][HardQuest] failed to switch area')
            return False

        screenshot = self._mainQuestState._device.getScreenshot()

        if MatchUtil.isMatch(MatchUtil.match(screenshot, self._mainQuestState.hardOffImage)):
            if not MatchUtil.pressUntilDisappear(self._mainQuestState._device, self._mainQuestState.hardOffImage, 1070, 160, 5):
                Logger.error('[TASK][HardQuest] failed to switch to hard page')
                return False
        
        levelY = 150 + 110 * self._levelNo

        # 按入場按鈕
        if not MatchUtil.pressUntilAppear(self._device, Asset.questInfoWindowIconImage, 1105, levelY, 5):
            Logger.error('[TASK][HardQuest] 無法點入任務資訊')
            return False
        
        # 按3次
        for i in range(3):
            self._device.tap(1035, 300)
            time.sleep(0.5)

        # 按掃蕩開始
        time.sleep(1)
        self._device.tap(870, 403)

        # 沒有AP
        if MatchUtil.Having(self._device, Asset.buyAPWindowImage):
            # TODO 調整下次執行的時間
            Logger.warn('[TASK][HardQuest] 沒有AP')
            self._device.tap(1240, 85)
            time.sleep(0.5)
            self._device.tap(1240, 85)
            time.sleep(0.5)
            return False

        # 次數不足
        if MatchUtil.Having(self._device, self.notEnoughInfoImage):
            Logger.warn('[TASK][HardQuest]  已打完')
            # TODO 執行時間調到明天
            return True

        # 按確認
        if not MatchUtil.pressUntilDisappear(self._device, Asset.infoWindowIconImage, 765, 500, 5):
            Logger.error('[TASK][HardQuest] 無法按\'確認\'開始掃蕩')

        # 等到掃蕩結束
        while not MatchUtil.Having(self._device, Asset.confirmBtnImage):
            time.sleep(1)

        self._device.tap(640, 580)
        time.sleep(1)
        self._device.tap(1240, 85)
        time.sleep(1)

        self._stateManager.goto('Lobby')

        return True

