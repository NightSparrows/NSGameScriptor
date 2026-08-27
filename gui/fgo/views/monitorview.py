
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpinBox, QSplitter, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt, QTimer

from core.logger import Logger

from gui.common.worker import WorkerPool
from gui.common.imageutil import cvImageToPixmap
from gui.fgo.views.logview import LogView


class ScreenshotPanel(QWidget):
    """即時畫面 half of the tab. Screenshot capture goes through Device, which
    is blocking (adb/screencap I/O) - every capture runs on the shared
    WorkerPool, never on the GUI thread."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._pool = WorkerPool.instance('screenshot')
        self._lastPixmap = None

        self._imageLabel = QLabel('尚未取得畫面 (按刷新或開啟自動刷新)', self)
        self._imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._imageLabel.setMinimumSize(320, 180)
        self._imageLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._imageLabel.setStyleSheet('background-color: #202020; color: #aaaaaa;')

        self._refreshBtn = QPushButton('刷新', self)
        self._refreshBtn.clicked.connect(self._captureOnce)

        self._autoCheck = QCheckBox('自動刷新', self)
        self._autoCheck.toggled.connect(self._onAutoToggled)

        self._intervalSpin = QSpinBox(self)
        self._intervalSpin.setRange(1, 30)
        self._intervalSpin.setValue(2)
        self._intervalSpin.setSuffix(' 秒')
        self._intervalSpin.valueChanged.connect(self._onIntervalChanged)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self._refreshBtn)
        toolbar.addWidget(self._autoCheck)
        toolbar.addWidget(QLabel('間隔:', self))
        toolbar.addWidget(self._intervalSpin)
        toolbar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._imageLabel, 1)
        layout.addLayout(toolbar)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._captureOnce)

    def _onIntervalChanged(self, value: int):
        if self._timer.isActive():
            self._timer.start(value * 1000)

    def _onAutoToggled(self, checked: bool):
        if checked:
            self._timer.start(self._intervalSpin.value() * 1000)
        else:
            self._timer.stop()

    def _captureOnce(self):
        if self._pool.isBusy():
            # 上一次截圖還沒完成，跳過這次刷新，避免請求堆積 (跟自動化用的是不同 pool,
            # 所以這裡不會因為 task/battle 在跑而被卡住)
            return

        self._refreshBtn.setEnabled(False)
        self._pool.submit(
            self._captureScreenshot,
            on_result=self._onCaptureResult,
            on_error=self._onCaptureError,
            on_finished=lambda: self._refreshBtn.setEnabled(True),
        )

    def _captureScreenshot(self):
        device = self._controller.game._device
        device.screenshot()
        return device.getScreenshot()

    def _onCaptureResult(self, image):
        if image is None:
            Logger.warn('截圖失敗: 沒有取得畫面')
            return

        self._lastPixmap = cvImageToPixmap(image)
        self._applyScaledPixmap()

    def _onCaptureError(self, message: str):
        Logger.error('截圖失敗: ' + message)

    def _applyScaledPixmap(self):
        if self._lastPixmap is None or self._lastPixmap.isNull():
            return

        scaled = self._lastPixmap.scaled(
            self._imageLabel.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._imageLabel.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._applyScaledPixmap()

    def shutdown(self):
        self._timer.stop()


class MonitorView(QWidget):
    """即時畫面 + Log 面板 tab: screenshot preview on the left, log console
    on the right."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)

        self.screenshotPanel = ScreenshotPanel(controller, self)
        self.logView = LogView(self)

        splitter = QSplitter(self)
        splitter.addWidget(self.screenshotPanel)
        splitter.addWidget(self.logView)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

    def shutdown(self):
        self.screenshotPanel.shutdown()
        self.logView.shutdown()
