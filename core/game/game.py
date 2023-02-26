
from .gamedata import GameData
from .statemanager import StateManager
from .taskmanager import TaskManager

class Game:

    def __init__(self, name: str) -> None:
        self._name = name
        self._data = GameData()
        self._stateManager = StateManager(self._data)
        self._taskManager = TaskManager()

    # 若在遊戲裡，則回到init state，否則重啟
    def init(self):
        raise NotImplementedError('Game ' + self.m_name + ' init not impl')

    def execute(self):
        raise NotImplementedError('Game ' + self.m_name + ' execute not impl')

    def restart(self):
        raise NotImplementedError('Game ' + self.m_name + ' restart not impl.')

    def getName(self):
        return self._name

    def getData(self):
        return self._data
