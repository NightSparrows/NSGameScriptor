
import datetime

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QColor, QTextCharFormat

from gui.common.logbridge import LogBridge

LEVEL_COLORS = {
    'info': QColor('#2AA9C4'),
    'warn': QColor('#C9A227'),
    'error': QColor('#D64545'),
    'trace': QColor('#7FB8C4'),
}

LEVEL_ORDER = ['trace', 'info', 'warn', 'error']


class LogView(QWidget):
    """Log console fed by core.logger.Logger via gui.common.logbridge.LogBridge.

    Screenshot preview (即時畫面) lands alongside this in a later pass; this
    tab is a fully working log console on its own in the meantime.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._bridge = LogBridge()
        self._bridge.logMessage.connect(self._onLogMessage)

        self._minLevelCombo = QComboBox(self)
        self._minLevelCombo.addItem('全部', 'trace')
        self._minLevelCombo.addItem('Info 以上', 'info')
        self._minLevelCombo.addItem('Warn 以上', 'warn')
        self._minLevelCombo.addItem('Error 以上', 'error')

        self._clearBtn = QPushButton('清除', self)
        self._clearBtn.clicked.connect(self._onClear)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel('顯示等級:', self))
        toolbar.addWidget(self._minLevelCombo)
        toolbar.addStretch(1)
        toolbar.addWidget(self._clearBtn)

        self._console = QPlainTextEdit(self)
        self._console.setReadOnly(True)
        self._console.setMaximumBlockCount(5000)

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self._console)

    def _onClear(self):
        self._console.clear()

    def _onLogMessage(self, level: str, msg: str):
        minLevel = self._minLevelCombo.currentData()
        if LEVEL_ORDER.index(level) < LEVEL_ORDER.index(minLevel):
            return

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        fmt = QTextCharFormat()
        fmt.setForeground(LEVEL_COLORS.get(level, QColor('white')))

        cursor = self._console.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.setCharFormat(fmt)
        cursor.insertText(f'[{timestamp}][{level.upper()}] {msg}\n')
        self._console.setTextCursor(cursor)
        self._console.ensureCursorVisible()

    def shutdown(self):
        """Call from the owning window's closeEvent - this widget is a tab,
        not a top-level window, so it never receives its own closeEvent."""
        self._bridge.close()
