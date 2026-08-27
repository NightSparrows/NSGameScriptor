
import sys

from PySide6.QtWidgets import QApplication

from gui.fgo.mainwindow import FGOMainWindow

if __name__ == '__main__':

    app = QApplication(sys.argv)

    window = FGOMainWindow()
    window.show()

    sys.exit(app.exec())
