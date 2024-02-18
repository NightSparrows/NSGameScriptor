
import sys
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QIODevice

if __name__ == '__main__':
    app = QApplication(sys.argv)

    uiFileName = 'assets/fgo/gui/guiUI.ui'
    uiFile = QFile(uiFileName)

    if not uiFile.open(QIODevice.ReadOnly):
        print(f'Cannot open FGO UI File!')
        sys.exit(-1)
    
    loader = QUiLoader()
    window = loader.load(uiFile)
    uiFile.close()

    if not window:
        print(loader.errorString())
        sys.exit(-1)
    
    window.show()
    sys.exit(app.exec())

