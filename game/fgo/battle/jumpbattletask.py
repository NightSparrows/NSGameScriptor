
import time
import cv2

from core.logger import Logger

from .battletask import BattleTask
from .battledata import BattleData

class JumpBattleTask(BattleTask):

    def __init__(self, data: BattleData, jumpCmdNo: int) -> None:
        self._jumpCmdNo = jumpCmdNo
        self._data = data

    def execute(self):
        self._data.executePC = self._jumpCmdNo - 2
        Logger.info('Jump to cmd: ' + str(self._jumpCmdNo))
        return True





