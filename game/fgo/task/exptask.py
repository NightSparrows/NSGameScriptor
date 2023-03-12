
import cv2
import datetime
import time

from core.logger import Logger

from core.game.task import Task
from core.matchutil import MatchUtil

from game.fgo.battle.battle import Battle
from game.fgo.battle.apple import Apple

class EXPTask(Task):

    s_BtnImage = cv2.imread('.//assets//fgo//task//dailyEXP//btn.png')
    s_BtnIconImage = cv2.imread('.//assets//fgo//task//dailyEXP//btnIcon.png')
    s_levelImage = cv2.imread('.//assets//fgo//task//dailyEXP//level.png')

    def __init__(self, game, battle: Battle, count: int, date: datetime, enable: bool = True) -> None:
        super().__init__('exptask', date, enable)

        self._game = game
        self._device = game._device
        self._stateManager = game._stateManager
        self._battle = battle
        self._count = count
    
    def detectBtnAndRun(self):
        
        self._device.screenshot()
        
        result = MatchUtil.match(self._device.getScreenshot(), EXPTask.s_BtnIconImage)

        if result['max_val'] < 0.97:
            return False

        x = result['max_loc'][0]
        y = result['max_loc'][1]

        levelX = x + 200
        levelY = y - 35

        result = MatchUtil.match(self._device.getScreenshot()[levelY:(levelY + 85), levelX:(levelX + 200)], EXPTask.s_levelImage)

        if result['max_val'] < 0.97:
            return False
        
        self._device.tap(x + 100, y + 50)
        time.sleep(1)

        Apple.checkAppleWindow(self._device)

        return True

    def searchAndClick(self):
        
        if self.detectBtnAndRun():
            return True

        self._device.tap(1257, 150)
        
        remainTime = self._count
        for i in range(5):
            if self.detectBtnAndRun():
                return True
            
            # 往下滑
            self._device.swipe(700, 500, 700, 200)
            time.sleep(1)
        
        return False


    def execute(self):
        
        if not self._stateManager.goto('Daily'):
            Logger.error('無法進入每日任務頁面')
            return False

        remainCount = self._count

        for i in range(5):
            if self.searchAndClick():
                result, count = self._battle.execute(remainCount)
                remainCount -= count
                if remainCount == 0:
                    self.m_date = datetime.datetime.combine(datetime.datetime.today().date(), datetime.time())
                    return True

        return False
    
    def getInfo(self):
        return 'EXP每日任務[' + str(self._count) + ']'
