
from typing import final
from abc import abstractmethod
import datetime

class Task:

    # name: 工作名稱
    # date: 下次要執行的日期
    def __init__(self, name: str, date: datetime, enable: bool = True) -> None:
        self.m_name = name
        self.m_date = date
        self._enable = enable
        pass

    @abstractmethod
    def execute(self):
        raise NotImplementedError('Task ' + self.m_name + ' not impl.')
    
    def getInfo(self):
        return ''

    @final
    def getName(self):
        return self.m_name

    @final
    def getDate(self):
        return self.m_date

    @final
    def isEnable(self):
        return self._enable
