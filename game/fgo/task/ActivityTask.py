
import datetime

from core.game.task import Task
from core.game.statemanager import StateManager

class ActivityTask(Task):

    def __init__(self,  date: datetime, enable: bool = True) -> None:
        super().__init__('ActivityTask', date, enable)
    
    def execute(self):
        raise NotImplementedError('Task ' + self.m_name + ' not impl.')
    
    def getInfo(self):
        return ''

