
import os

from PySide6.QtCore import QObject, Signal

from core.logger import Logger

from game.fgo.gamefgo import GameFGO
from game.fgo.configutil import ConfigUtil


class FGOController(QObject):
    """
    Owns the GameFGO instance shared by every GUI view.

    All the actual automation calls made off of self.game (task execution,
    battle test-runs, device connect/restart, ...) are blocking and MUST be
    dispatched through gui.common.worker.WorkerPool rather than called
    directly on the GUI thread.
    """

    tasksChanged = Signal()
    battlesChanged = Signal()
    connectionChanged = Signal()

    def __init__(self, configPath: str = 'settings/fgo') -> None:
        super().__init__()
        self.configPath = configPath
        self.game: GameFGO = ConfigUtil.LoadGame(configPath)
        # registers Lobby/Activity/Gate/Daily with the StateManager - every
        # Task subclass calls stateManager.goto(...), so without this every
        # task execution would fail with "Unknown state name". FGOUI (CLI)
        # calls this in its run() before entering its loop; the GUI needs
        # the same call since it has no equivalent single entry point.
        self.game.init()

    def save(self):
        Logger.info('儲存中...')
        if not os.path.exists(self.configPath):
            os.makedirs(self.configPath)

        configData = ConfigUtil.Deserialize(self.game)
        try:
            with open(self.configPath + '/config.json', 'w', encoding='utf-8') as f:
                f.write(configData)
            Logger.info('儲存成功')
        except Exception as e:
            Logger.error('無法寫入設定檔: ' + str(e))
