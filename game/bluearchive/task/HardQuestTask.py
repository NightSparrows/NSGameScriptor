
import datetime
import cv2

from core.logger import Logger
from core.game.task import Task
from core.game.statemanager import StateManager

class HardQuestTask(Task):

    def __init__(self, stateManager: StateManager, date: datetime) -> None:
        super().__init__('HardQuest', date)
        self._stateManager = stateManager

    def execute(self):

        if not self._stateManager.goto('Quest'):
            Logger.error('Failed to goto Quest state in task (HardQuest)')
            return False
        


        raise NotImplementedError('Task ' + self.m_name + ' not impl.')
    