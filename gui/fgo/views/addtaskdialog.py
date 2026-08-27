
import datetime

import cv2

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from core.logger import Logger

from game.fgo.task.activitytask import ActivityTask
from game.fgo.task.qptask import QPTask
from game.fgo.task.exptask import EXPTask


class AddTaskDialog(QDialog):
    """Replaces AddTaskUI's line-by-line input flow with a form.

    Field-for-field this mirrors AddTaskUI.addActivityTask / addDailyTask in
    game/fgo/ui/addtaskui.py, and constructs the exact same Task subclasses
    those flows do.

    Pass editTask to edit an existing task in place instead of creating a
    new one - this mutates editTask's attributes directly (keeping its
    current date/enable state and its position in the task list) rather
    than replacing it, matching how TaskView already mutates tasks
    in-place for enable/disable.
    """

    def __init__(self, controller, parent=None, editTask=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._editTask = editTask
        self.setWindowTitle('編輯工作' if editTask is not None else '新增工作')
        self.resize(420, 320)

        self._typeCombo = QComboBox(self)
        self._typeCombo.addItem('活動關卡周回', 'activity')
        self._typeCombo.addItem('每日QP任務', 'qp')
        self._typeCombo.addItem('每日EXP任務', 'exp')

        self._stack = QStackedWidget(self)
        self._activityPage = self._buildActivityPage()
        self._qpPage = self._buildDailyPage()
        self._expPage = self._buildDailyPage()
        self._stack.addWidget(self._activityPage)
        self._stack.addWidget(self._qpPage)
        self._stack.addWidget(self._expPage)

        self._typeCombo.currentIndexChanged.connect(self._stack.setCurrentIndex)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self._onAccept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._typeCombo)
        layout.addWidget(self._stack)
        layout.addWidget(buttons)

        if editTask is not None:
            # changing a task's underlying type isn't supported here (would
            # mean swapping the Task subclass, not just editing fields)
            self._typeCombo.setEnabled(False)
            self._prefillForEdit(editTask)

    # -- edit mode: pre-fill from an existing task ----------------------------

    def _prefillForEdit(self, task):
        name = task.getName()

        if name == 'ActivityTask':
            self._typeCombo.setCurrentIndex(self._typeCombo.findData('activity'))
            idx = self._areaCombo.findData(task._areaName)
            if idx >= 0:
                self._areaCombo.setCurrentIndex(idx)
            idx = self._levelCombo.findData(task._levelName)
            if idx >= 0:
                self._levelCombo.setCurrentIndex(idx)
            battleKey = self._controller.game.getKeyFromBattle(task._battle)
            idx = self._activityBattleCombo.findData(battleKey)
            if idx >= 0:
                self._activityBattleCombo.setCurrentIndex(idx)
            self._activityCountSpin.setValue(task._count)
            hours = min(24, max(1, round(task._interval.total_seconds() / 3600)))
            self._activityIntervalSpin.setValue(hours)

        elif name == 'qptask':
            self._typeCombo.setCurrentIndex(self._typeCombo.findData('qp'))
            self._prefillDailyPage(self._qpPage, task)

        elif name == 'exptask':
            self._typeCombo.setCurrentIndex(self._typeCombo.findData('exp'))
            self._prefillDailyPage(self._expPage, task)

        self._stack.setCurrentIndex(self._typeCombo.currentIndex())

    def _prefillDailyPage(self, page: QWidget, task):
        battleKey = self._controller.game.getKeyFromBattle(task._battle)
        idx = page.battleCombo.findData(battleKey)
        if idx >= 0:
            page.battleCombo.setCurrentIndex(idx)
        page.countSpin.setValue(task._count)

    # -- shared battle combo, kept in sync with game._battles --------------

    def _populateBattleCombo(self, combo: QComboBox):
        combo.clear()
        for key in self._controller.game._battles:
            combo.addItem(key, key)

    # -- 活動關卡周回 --------------------------------------------------------

    def _buildActivityPage(self) -> QWidget:
        page = QWidget(self)
        form = QFormLayout(page)

        self._areaCombo = QComboBox(page)
        for key, levelData in self._controller.game.activityState._levels.items():
            appName = levelData.get('appName', '') if isinstance(levelData, dict) else ''
            self._areaCombo.addItem(f'{key} ({appName})' if appName else key, key)
        self._areaCombo.currentIndexChanged.connect(self._onAreaChanged)

        self._levelCombo = QComboBox(page)
        self._onAreaChanged(self._areaCombo.currentIndex())

        self._activityBattleCombo = QComboBox(page)
        self._populateBattleCombo(self._activityBattleCombo)

        self._activityCountSpin = QSpinBox(page)
        self._activityCountSpin.setRange(1, 999)
        self._activityCountSpin.setValue(1)

        self._activityIntervalSpin = QSpinBox(page)
        self._activityIntervalSpin.setRange(1, 24)
        self._activityIntervalSpin.setValue(2)
        self._activityIntervalSpin.setSuffix(' 小時')

        form.addRow('地區:', self._areaCombo)
        form.addRow('關卡:', self._levelCombo)
        form.addRow('Battle:', self._activityBattleCombo)
        form.addRow('次數:', self._activityCountSpin)
        form.addRow('執行間隔:', self._activityIntervalSpin)
        return page

    def _onAreaChanged(self, index: int):
        self._levelCombo.clear()
        if index < 0:
            return
        areaName = self._areaCombo.itemData(index)
        try:
            areaData = self._controller.game.activityState._levels[areaName]
            for level in areaData['level']:
                self._levelCombo.addItem(level.get('name', level.get('imageName', '')), level.get('imageName'))
        except (KeyError, TypeError):
            # activityState 目前的資料結構與此地區/關卡巢狀格式不一致 (既有 CLI 也有相同限制)
            self._levelCombo.addItem('(此活動資料格式不支援關卡列表，請改用原始腳本或更新活動設定檔)', None)

    # -- 每日QP / 每日EXP -----------------------------------------------------

    def _buildDailyPage(self) -> QWidget:
        page = QWidget(self)
        form = QFormLayout(page)

        battleCombo = QComboBox(page)
        self._populateBattleCombo(battleCombo)

        countSpin = QSpinBox(page)
        countSpin.setRange(1, 100)
        countSpin.setValue(1)

        form.addRow('Battle:', battleCombo)
        form.addRow('次數:', countSpin)

        page.battleCombo = battleCombo
        page.countSpin = countSpin
        return page

    # -- submit --------------------------------------------------------------

    def _onAccept(self):
        taskType = self._typeCombo.currentData()

        if not self._controller.game._battles:
            QMessageBox.warning(self, '無法新增', '目前沒有任何 Battle，請先到 Battle 編輯器新增。')
            return

        isEdit = self._editTask is not None
        try:
            if isEdit:
                if taskType == 'activity':
                    self._editActivityTask()
                elif taskType == 'qp':
                    self._editDailyTask(self._qpPage)
                elif taskType == 'exp':
                    self._editDailyTask(self._expPage)
            else:
                if taskType == 'activity':
                    self._addActivityTask()
                elif taskType == 'qp':
                    self._addDailyTask(self._qpPage, QPTask)
                elif taskType == 'exp':
                    self._addDailyTask(self._expPage, EXPTask)
        except Exception as e:
            action = '編輯' if isEdit else '新增'
            Logger.error(action + '工作失敗: ' + str(e))
            QMessageBox.critical(self, action + '失敗', str(e))
            return

        self.accept()

    def _addActivityTask(self):
        areaName = self._areaCombo.currentData()
        levelID = self._levelCombo.currentData()
        if areaName is None or levelID is None:
            raise ValueError('請選擇有效的地區/關卡')

        battleKey = self._activityBattleCombo.currentData()
        battle = self._controller.game.getBattleFromKey(battleKey)
        if battle is None:
            raise ValueError('請選擇 Battle')

        count = self._activityCountSpin.value()
        interval = datetime.timedelta(hours=self._activityIntervalSpin.value())

        task = ActivityTask(
            self._controller.game._stateManager, self._controller.game,
            areaName, levelID, battle, count, interval, datetime.datetime.now(),
        )
        self._controller.game._taskManager.addTask(task)
        Logger.info('Task新增成功')
        self._controller.tasksChanged.emit()

    def _addDailyTask(self, page: QWidget, taskClass):
        battleKey = page.battleCombo.currentData()
        battle = self._controller.game.getBattleFromKey(battleKey)
        if battle is None:
            raise ValueError('請選擇 Battle')

        count = page.countSpin.value()
        date = datetime.datetime.combine(datetime.datetime.now().date(), datetime.time())

        task = taskClass(self._controller.game, battle, count, date, True)
        self._controller.game._taskManager.addTask(task)
        Logger.info(task.getName() + '新增成功')
        self._controller.tasksChanged.emit()

    # -- edit -----------------------------------------------------------------

    def _editActivityTask(self):
        areaName = self._areaCombo.currentData()
        levelID = self._levelCombo.currentData()
        if areaName is None or levelID is None:
            raise ValueError('請選擇有效的地區/關卡')

        battleKey = self._activityBattleCombo.currentData()
        battle = self._controller.game.getBattleFromKey(battleKey)
        if battle is None:
            raise ValueError('請選擇 Battle')

        task = self._editTask
        task._areaName = areaName
        task._levelName = levelID
        task._battle = battle
        task._count = self._activityCountSpin.value()
        task._interval = datetime.timedelta(hours=self._activityIntervalSpin.value())
        # _btnImage depends on areaName/levelName, exactly like ActivityTask.__init__
        task._btnImage = cv2.imread(
            './assets/fgo/activity/' + task._activityState._activityName + '/' + areaName + '/' + levelID + '.png'
        )

        Logger.info('Task編輯成功')
        self._controller.tasksChanged.emit()

    def _editDailyTask(self, page: QWidget):
        battleKey = page.battleCombo.currentData()
        battle = self._controller.game.getBattleFromKey(battleKey)
        if battle is None:
            raise ValueError('請選擇 Battle')

        task = self._editTask
        task._battle = battle
        task._count = page.countSpin.value()

        Logger.info(task.getName() + '編輯成功')
        self._controller.tasksChanged.emit()
