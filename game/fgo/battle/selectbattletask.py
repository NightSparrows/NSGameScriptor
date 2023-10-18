
import time
import cv2

from core.logger import Logger

from .battletask import BattleTask
from .battledata import BattleData

from core.matchutil import MatchUtil

class SelectBattleTask(BattleTask):

    def __init__(self, data: BattleData, selectNo: int) -> None:
        self._selectNo = selectNo
        self._data = data

    def execute(self):
        
        Logger.info('Select ' + str(self._selectNo))
        if (self._selectNo == 1):           # 最左邊
            self._data.device.tap(45, 45)
        elif (self._selectNo == 2):         # 中間
            self._data.device.tap(295, 45)
        elif (self._selectNo == 3):         # 右邊
            self._data.device.tap(545, 45)
        elif (self._selectNo == 4):         # 最大之
            self._data.device.tap(41, 45)
        elif (self._selectNo == 5):         # 左邊小怪
            self._data.device.tap(45, 150)
        elif (self._selectNo == 6):         # 左邊小怪
            self._data.device.tap(545, 150)
        else:
            Logger.error('Unknown selection: ' + self._selectNo)

        time.sleep(0.25)
        

        return True





