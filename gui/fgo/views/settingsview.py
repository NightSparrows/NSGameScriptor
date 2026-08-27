
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from core.logger import Logger
from core.device.device import Device

from game.fgo.battle.apple import Apple

from gui.common.worker import WorkerPool

SCREENCAP_LABELS = {
    Device.ScreenCapType.aScreenCap: 'aScreenCap',
    Device.ScreenCapType.droidCast: 'droidCast',
    Device.ScreenCapType.ADB: 'ADB',
    Device.ScreenCapType.NEMUIPC: 'NemuIPC (MuMu)',
}

APPLE_LABELS = [
    ('金蘋果', 'gold'),
    ('銀蘋果', 'silver'),
    ('銅蘋果', 'copper'),
]


class SettingsView(QWidget):
    """設定/裝置管理 tab. Device name/connect/restart use Device.connect() /
    Device.restart() directly (same methods the CLI's Device class already
    exposes, just never wired up to a UI button - FGOUI.cmdEdit's 'device'
    case only ever set _connectDevice without calling connect()). Screencap
    type and apple type only take effect for the running process after
    儲存設定 + restarting the app, since swapping a live capture backend or
    an already-connected adb wrapper mid-session isn't something the
    underlying Device/ScreenCap classes support."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._pool = WorkerPool.instance()

        deviceGroup = QGroupBox('裝置連線', self)
        deviceForm = QFormLayout(deviceGroup)

        self._deviceEdit = QLineEdit(deviceGroup)
        self._deviceEdit.setText(self._controller.game._device._connectDevice)

        self._connectBtn = QPushButton('連線', deviceGroup)
        self._connectBtn.clicked.connect(self._onConnect)
        self._restartBtn = QPushButton('重啟 ADB', deviceGroup)
        self._restartBtn.clicked.connect(self._onRestart)

        deviceRow = QHBoxLayout()
        deviceRow.addWidget(self._deviceEdit, 1)
        deviceRow.addWidget(self._connectBtn)
        deviceRow.addWidget(self._restartBtn)

        self._deviceStatusLabel = QLabel('', deviceGroup)
        self._deviceStatusLabel.setStyleSheet('color: gray;')

        deviceForm.addRow('裝置名稱/位址:', deviceRow)
        deviceForm.addRow('', self._deviceStatusLabel)

        captureGroup = QGroupBox('截圖與蘋果設定', self)
        captureForm = QFormLayout(captureGroup)

        self._screencapCombo = QComboBox(captureGroup)
        for screencapType, label in SCREENCAP_LABELS.items():
            self._screencapCombo.addItem(label, screencapType)
        idx = self._screencapCombo.findData(self._controller.game._device._screenCapType)
        self._screencapCombo.setCurrentIndex(idx if idx >= 0 else 0)

        screencapHint = QLabel('變更截圖模式需按「儲存設定」後重新啟動程式才會生效', captureGroup)
        screencapHint.setStyleSheet('color: gray;')

        self._appleCombo = QComboBox(captureGroup)
        for label, value in APPLE_LABELS:
            self._appleCombo.addItem(label, value)
        idx = self._appleCombo.findData(Apple.s_appleTypeName)
        self._appleCombo.setCurrentIndex(idx if idx >= 0 else 0)

        captureForm.addRow('截圖模式:', self._screencapCombo)
        captureForm.addRow('', screencapHint)
        captureForm.addRow('自動吃蘋果類型:', self._appleCombo)

        self._saveBtn = QPushButton('儲存設定', self)
        self._saveBtn.clicked.connect(self._onSave)

        saveRow = QHBoxLayout()
        saveRow.addWidget(self._saveBtn)
        saveRow.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(deviceGroup)
        layout.addWidget(captureGroup)
        layout.addLayout(saveRow)
        layout.addStretch(1)

    def _setDeviceButtonsEnabled(self, enabled: bool):
        self._connectBtn.setEnabled(enabled)
        self._restartBtn.setEnabled(enabled)

    def _onConnect(self):
        deviceName = self._deviceEdit.text().strip()
        if not deviceName:
            return

        self._deviceStatusLabel.setText('連線中...')
        self._setDeviceButtonsEnabled(False)
        self._pool.submit(
            self._controller.game._device.connect, deviceName,
            on_result=lambda _: self._onConnectResult(deviceName),
            on_error=self._onDeviceError,
            on_finished=lambda: self._setDeviceButtonsEnabled(True),
        )

    def _onConnectResult(self, deviceName: str):
        Logger.info('連線成功: ' + deviceName)
        self._deviceStatusLabel.setText('已連線: ' + deviceName)

    def _onRestart(self):
        self._deviceStatusLabel.setText('重啟 ADB 中...')
        self._setDeviceButtonsEnabled(False)
        self._pool.submit(
            self._controller.game._device.restart,
            on_result=lambda _: self._onRestartResult(),
            on_error=self._onDeviceError,
            on_finished=lambda: self._setDeviceButtonsEnabled(True),
        )

    def _onRestartResult(self):
        Logger.info('ADB 重啟完成')
        self._deviceStatusLabel.setText('ADB 重啟完成')

    def _onDeviceError(self, message: str):
        Logger.error('裝置操作失敗: ' + message)
        self._deviceStatusLabel.setText('失敗: ' + message)

    def _onSave(self):
        self._controller.game._device._screenCapType = self._screencapCombo.currentData()
        Apple.s_appleTypeName = self._appleCombo.currentData()
        self._controller.save()
