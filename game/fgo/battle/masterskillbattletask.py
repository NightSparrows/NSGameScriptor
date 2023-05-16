
import time

from .battletask import BattleTask
from .battledata import BattleData

class MasterSkillBattleTask(BattleTask):

    def __init__(self, data: BattleData, skillNo: int, useCharNo: int = -1, anotherCharNo: int = -1) -> None:
        assert(skillNo >= 1 and skillNo <= 3)
        self._data = data
        self._skillX = 815 + (90 * skillNo)
        self._useCharNo = useCharNo
        self._anotherCharNo = anotherCharNo

    def execute(self):

        # TODO 選擇角色的功能

        self._data.device.tap(1194, 316)
        time.sleep(1.5)

        self._data.device.tap(self._skillX, 314)
        time.sleep(1)

        if self._anotherCharNo != -1:           # 換人
            firstCharX = 140 + 200 * (self._useCharNo - 1)
            secondCharX = 140 + 200 * (self._anotherCharNo - 1)
            self._data.device.tap(firstCharX, 340)
            time.sleep(1)
            self._data.device.tap(secondCharX, 340)
            time.sleep(1)
            self._data.device.tap(640, 625)
            time.sleep(1)
        elif self._useCharNo != -1:
            useCharX = 320 * self._useCharNo
            self._data.device.tap(useCharX, 450)
            time.sleep(1)

        return True

