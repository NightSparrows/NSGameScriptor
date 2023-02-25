
import time
import datetime
import cv2
import numpy as np
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
        self._device = game._device

    def execute(self):
        
        if not self._stateManager.goto('Quest'):
            Logger.error('Failed to goto Quest state in task (Contest)')
            return False
        
        if not MatchUtil.pressUntilAppear(self._game._device, Asset.questContestImage, 1100, 500, 10):
            Logger.error('無法點入戰術大賽')
            return False
        
        while True:
            self._device.screenshot()
            screenshot = self._device.getScreenshot()
            #a = [407:407, 353:353]
            color1 = screenshot[407, 353]
            color2 = screenshot[486, 353]

            if MatchUtil.MatchColor(color1, 213, 215, 214) and MatchUtil.MatchColor(color2, 215, 215, 212):
                break

            result = MatchUtil.match(screenshot, Asset.getRewardBtnImage)

            if MatchUtil.isMatch(result):
                point = MatchUtil.calculated(result, Asset.getRewardBtnImage.shape)
                self._device.tap(point['x']['center'], point['y']['center'])
                time.sleep(1)
            
            self._device.tap(309, 119)
            time.sleep(1) 

        # 返回main quest state
        if not MatchUtil.pressUntilDisappear(self._game._device, Asset.questContestImage, 58, 35, 10):
            Logger.error('無法返回quest state')
            return False
        
        self.m_date = datetime.datetime.today().date() + timedelta(days=1)
        Logger.info('戰術大賽每日 complete')
        return True






    

