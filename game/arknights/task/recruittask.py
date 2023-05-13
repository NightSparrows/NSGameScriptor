
import cv2
import datetime
import time

from core.game.statemanager import StateManager
from core.game.task import Task
from core.game.game import Game
from core.device.device import Device
from core.game.statemanager import StateManager

from core.matchutil import MatchUtil

class RecruitTask(Task):


    def __init__(self, game: Game, date: datetime, enable: bool = True) -> None:
        super().__init__('RecruitTask', date, enable)
        self._game = game
        self._stateManager = game._stateManager
        self._device = game._device
        self._recruitBtn = cv2.imread('assets/arknights/task/recruittask/recruitBtn.png')

    # True mean open successful
    # False mean no empty slot or error
    def chooseEmptySlot(self) -> bool:

        

        raise NotImplementedError()

    def emptySlots(self):

        while MatchUtil.Having(self._device, self._recruitBtn):
            if MatchUtil.TapImage(self._device, self._recruitBtn, 0.95):

                while True:
                    self._device.tap(1220, 40)
                    time.sleep(1)


    def execute(self):
        
        # TODO in recruit state

        self.emptySlots()

        for i in range(3):
            if not self.chooseEmptySlot():
                return False

        raise NotImplementedError()
