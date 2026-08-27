
from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget
from PySide6.QtCore import QTimer

from gui.common.worker import WorkerPool
from gui.fgo.controller import FGOController
from gui.fgo.views.taskview import TaskView
from gui.fgo.views.monitorview import MonitorView
from gui.fgo.views.battleeditorview import BattleEditorView
from gui.fgo.views.settingsview import SettingsView


class FGOMainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('NSGameScriptor - FGO')
        self.resize(1000, 640)

        self._controller = FGOController()
        self._pool = WorkerPool.instance()

        self._monitorView = MonitorView(self._controller, self)

        tabs = QTabWidget(self)
        tabs.addTab(TaskView(self._controller, self), '工作管理與排程')
        tabs.addTab(self._monitorView, '即時畫面 + Log 面板')
        tabs.addTab(BattleEditorView(self._controller, self), 'Battle 腳本編輯器')
        tabs.addTab(SettingsView(self._controller, self), '設定/裝置管理')
        self.setCentralWidget(tabs)

        self._statusLabel = QLabel('就緒', self)
        self.statusBar().addPermanentWidget(self._statusLabel)

        self._statusTimer = QTimer(self)
        self._statusTimer.setInterval(300)
        self._statusTimer.timeout.connect(self._updateStatus)
        self._statusTimer.start()

    def _updateStatus(self):
        self._statusLabel.setText('執行中...' if self._pool.isBusy() else '就緒')

    def closeEvent(self, event):
        self._monitorView.shutdown()
        super().closeEvent(event)
