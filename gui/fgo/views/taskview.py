
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QMessageBox,
    QPushButton, QTableView, QVBoxLayout, QWidget,
)

from core.logger import Logger

from gui.common.worker import WorkerPool
from gui.fgo.models.taskmodel import TaskTableModel
from gui.fgo.views.addtaskdialog import AddTaskDialog


class TaskView(QWidget):
    """工作管理與排程 tab. Replaces list/add/rm/enable/disable/exe/run."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._pool = WorkerPool.instance()

        self._model = TaskTableModel(controller, self)

        self._table = QTableView(self)
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self._table.horizontalHeader()
        # every column freely resizable by dragging its header border,
        # with sane starting widths (Stretch mode on a column, used here
        # previously, ignores manual resize entirely - that's why it
        # couldn't be widened)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for column, width in enumerate((40, 140, 320, 60, 140)):
            header.resizeSection(column, width)

        self._table.doubleClicked.connect(self._onRowDoubleClicked)

        self._addBtn = QPushButton('新增', self)
        self._editBtn = QPushButton('編輯', self)
        self._removeBtn = QPushButton('刪除', self)
        self._toggleBtn = QPushButton('啟用/停用', self)
        self._runBtn = QPushButton('立即執行', self)
        self._runDueBtn = QPushButton('執行所有到期工作', self)
        self._saveBtn = QPushButton('儲存設定', self)

        self._addBtn.clicked.connect(self._onAdd)
        self._editBtn.clicked.connect(self._onEdit)
        self._removeBtn.clicked.connect(self._onRemove)
        self._toggleBtn.clicked.connect(self._onToggleEnable)
        self._runBtn.clicked.connect(self._onRunSelected)
        self._runDueBtn.clicked.connect(self._onRunDue)
        self._saveBtn.clicked.connect(self._onSave)

        buttonRow = QHBoxLayout()
        for btn in (self._addBtn, self._editBtn, self._removeBtn, self._toggleBtn, self._runBtn, self._runDueBtn, self._saveBtn):
            buttonRow.addWidget(btn)
        buttonRow.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._table)
        layout.addLayout(buttonRow)

        controller.tasksChanged.connect(self._model.refresh)

    def _selectedRow(self):
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return -1
        return indexes[0].row()

    def _setRunningButtonsEnabled(self, enabled: bool):
        for btn in (self._editBtn, self._removeBtn, self._toggleBtn, self._runBtn, self._runDueBtn):
            btn.setEnabled(enabled)

    def _onAdd(self):
        dialog = AddTaskDialog(self._controller, self)
        if dialog.exec():
            self._model.refresh()

    def _onEdit(self):
        row = self._selectedRow()
        if row < 0:
            QMessageBox.information(self, '編輯工作', '請先選擇一個工作。')
            return
        self._openEditDialog(row)

    def _onRowDoubleClicked(self, index):
        self._openEditDialog(index.row())

    def _openEditDialog(self, row: int):
        task = self._model.taskAt(row)
        if task is None:
            return
        dialog = AddTaskDialog(self._controller, self, editTask=task)
        if dialog.exec():
            self._model.refresh()

    def _onRemove(self):
        row = self._selectedRow()
        if row < 0:
            QMessageBox.information(self, '刪除工作', '請先選擇一個工作。')
            return

        del self._controller.game._taskManager._tasks[row]
        Logger.info('刪除成功')
        self._model.refresh()

    def _onToggleEnable(self):
        row = self._selectedRow()
        if row < 0:
            QMessageBox.information(self, '啟用/停用', '請先選擇一個工作。')
            return

        task = self._model.taskAt(row)
        task._enable = not task._enable
        Logger.info('Task[' + task.getName() + ']' + ('啟用' if task._enable else '停用') + '成功')
        self._model.refresh()

    def _onRunSelected(self):
        row = self._selectedRow()
        if row < 0:
            QMessageBox.information(self, '執行工作', '請先選擇一個工作。')
            return

        self._setRunningButtonsEnabled(False)
        self._pool.submit(
            self._controller.game._taskManager.runTask, row,
            on_result=self._onRunFinishedResult,
            on_error=self._onWorkerError,
            on_finished=lambda: (self._setRunningButtonsEnabled(True), self._model.refresh()),
        )

    def _onRunFinishedResult(self, result):
        if result == -1:
            Logger.error('非法工作ID')
        elif result == -2:
            Logger.error('工作執行失敗')

    def _onRunDue(self):
        self._setRunningButtonsEnabled(False)
        self._pool.submit(
            self._controller.game.execute,
            on_error=self._onWorkerError,
            on_finished=lambda: (self._setRunningButtonsEnabled(True), self._model.refresh()),
        )

    def _onWorkerError(self, message: str):
        Logger.error('執行失敗: ' + message)
        QMessageBox.critical(self, '執行失敗', message)

    def _onSave(self):
        self._controller.save()
