
import datetime

class Task:

    # name: 工作名稱
    # date: 下次要執行的日期
    def __init__(self, name: str, date: datetime) -> None:
        self.m_name = name
        self.m_date = date
        pass

    def execute(self):
        raise NotImplementedError('Task ' + self.m_name + ' not impl.')
    
    def getName(self):
        return self.m_name

    def getDate(self):
        return self.m_date
