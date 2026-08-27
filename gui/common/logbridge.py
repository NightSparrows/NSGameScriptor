
from PySide6.QtCore import QObject, Signal

from core.logger import Logger


class LogBridge(QObject):
    """
    Bridges core.logger.Logger to a Qt signal so GUI widgets can subscribe to
    log output without touching the existing print()-based CLI behavior.

    Logger callbacks may fire from a worker thread; Qt automatically queues
    cross-thread signal/slot connections, so logMessage subscribers always
    run on the GUI thread.
    """

    logMessage = Signal(str, str)  # level, msg

    def __init__(self) -> None:
        super().__init__()
        Logger.addListener(self._onLog)

    def _onLog(self, level: str, msg: str):
        self.logMessage.emit(level, msg)

    def close(self):
        Logger.removeListener(self._onLog)
