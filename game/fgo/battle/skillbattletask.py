
import time

from core.logger import Logger
from core.matchutil import MatchUtil

from .battletask import BattleTask
from .battledata import BattleData

class SkillBattleTask(BattleTask):

    def __init__(self, data: BattleData, charNo: int, skillNo: int, useCharNo: int) -> None:
        self._data = data
        self._charNo = charNo
        self._skillNo = skillNo
        self._useCharNo = useCharNo
        self._skillX = 70 + (self._charNo - 1) * 320 + (self._skillNo - 1) * 90

    def execute(self):

        self._data.device.screenshot()
        screenshot = self._data.device.getScreenshot()
        color = screenshot[580, self._skillX]

        while True:
            self._data.device.tap(self._skillX, 580)

            if self._useCharNo != -1:
                useCharX = 320 * self._useCharNo
                time.sleep(1)
                self._data.device.tap(useCharX, 450)
                time.sleep(0.23)     # 加速
                self._data.device.tap(900, 55)
                time.sleep(1)
            else:
                time.sleep(0.23)
                self._data.device.tap(900, 55)             # 加速
                time.sleep(1)

                
            self._data.device.screenshot()
            screenshot = self._data.device.getScreenshot()
            
            newColor = screenshot[580, self._skillX]

            if not MatchUtil.MatchColor(color, newColor[2], newColor[1], newColor[0]):
                break


        Logger.info('skill ' + str(self._charNo) + ' ' + str(self._skillNo) + ' executed.')
        return True
