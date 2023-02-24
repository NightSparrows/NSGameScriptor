
import time
import datetime
from datetime import timedelta

from core.logger import Logger
from core.game.task import Task
from core.game.statemanager import StateManager
from core.matchutil import MatchUtil

from game.bluearchive.asset import Asset

class ContestTask(Task):

    def __init__(self, game, date: datetime, enable: bool = True) -> None:
        super().__init__('contest', date, enable)
        self._stateManager = game._stateManager
        self._game = game

    def execute(self):
        
        if not self._stateManager.goto('Quest'):
            Logger.error('Failed to goto Quest state in task (Contest)')
            return False
        
        if not MatchUtil.pressUntilAppear(self._game._device, Asset.questContestImage, 1100, 500, 10):
            Logger.error('無法點入戰術大賽')
            return False
        
        # 點獲得錢
        self._game._device.tap(350, 387)
        time.sleep(1)

        # 點吊飾窗
        self._game._device.tap(309, 119)
        time.sleep(1) 

        # 點選獲得每日清輝石
        self._game._device.tap(350, 466)
        time.sleep(1)

        # 點吊飾窗
        self._game._device.tap(309, 119)
        time.sleep(1)

        # 返回main quest state
        if not MatchUtil.pressUntilDisappear(self._game._device, Asset.questContestImage, 58, 35, 10):
            Logger.error('無法返回quest state')
            return False
        
        self.m_date = datetime.datetime.today().date() + timedelta(days=1)
        Logger.info('戰術大賽每日 complete')
        return True






    

