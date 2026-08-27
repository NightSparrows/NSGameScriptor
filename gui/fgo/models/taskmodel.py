
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from core.util.serializeutil import SerializeUtil


class TaskTableModel(QAbstractTableModel):
    """Read-through table model over game._taskManager._tasks.

    Rows are addressed by list index, matching the existing CLI semantics
    (FGOUI.cmdList / cmdRunTask / cmdRemoveTask) - deleting a task shifts the
    ids of every task after it. refresh() must be called after the
    underlying list is mutated (add/remove/enable/disable) since the list is
    plain Python, not observable on its own.
    """

    HEADERS = ['ID', '名稱', '內容', '啟用', '執行日期']

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller

    def _tasks(self):
        return self._controller.game._taskManager._tasks

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._tasks())

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        return self.HEADERS[section]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        task = self._tasks()[index.row()]
        column = index.column()

        if column == 0:
            return str(index.row())
        if column == 1:
            return task.getName()
        if column == 2:
            return task.getInfo()
        if column == 3:
            return '是' if task.isEnable() else '否'
        if column == 4:
            return SerializeUtil.GetStringFromDateTime(task.getDate())

        return None

    def taskAt(self, row: int):
        tasks = self._tasks()
        if row < 0 or row >= len(tasks):
            return None
        return tasks[row]

    def refresh(self):
        self.beginResetModel()
        self.endResetModel()
