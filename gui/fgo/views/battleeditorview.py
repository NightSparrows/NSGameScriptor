
import os

import cv2

from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFormLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QSplitter,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from core.logger import Logger

from gui.common.worker import WorkerPool
from game.fgo.battle.battle import Battle

SERVANT_DIR = './assets/fgo/servant'
CRAFT_ESSENCE_DIR = './assets/fgo/craftEssence'


# ---------------------------------------------------------------------------
# per-row script line editors
# ---------------------------------------------------------------------------

class SkillLineWidget(QWidget):
    """`skill <charNo 1-3> <skillNo 1-3> [useCharNo 1-3]`"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.charNoSpin = QSpinBox(self)
        self.charNoSpin.setRange(1, 3)
        self.skillNoSpin = QSpinBox(self)
        self.skillNoSpin.setRange(1, 3)
        self.useCharCombo = QComboBox(self)
        self.useCharCombo.addItem('無', -1)
        for i in (1, 2, 3):
            self.useCharCombo.addItem(str(i), i)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.addWidget(QLabel('從者', self))
        layout.addWidget(self.charNoSpin)
        layout.addWidget(QLabel('技能', self))
        layout.addWidget(self.skillNoSpin)
        layout.addWidget(QLabel('被使用從者', self))
        layout.addWidget(self.useCharCombo)
        layout.addStretch(1)

    def loadTokens(self, tokens: list):
        # tokens = cmdArgs[1:]
        self.charNoSpin.setValue(int(tokens[0]))
        self.skillNoSpin.setValue(int(tokens[1]))
        useChar = int(tokens[2]) if len(tokens) >= 3 else -1
        idx = self.useCharCombo.findData(useChar)
        self.useCharCombo.setCurrentIndex(idx if idx >= 0 else 0)

    def toLine(self) -> str:
        line = f'skill {self.charNoSpin.value()} {self.skillNoSpin.value()}'
        useChar = self.useCharCombo.currentData()
        if useChar != -1:
            line += f' {useChar}'
        return line


class CardLineWidget(QWidget):
    """`card <slot> <slot> ...` - slot is c1/c2/c3 (寶具), r (隨機), or t (打手卡).
    Real scripts use anywhere from 3 to 5+ slots (extra slots are fallback
    choices), so this stays a free-form token field rather than a fixed set
    of combo boxes."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.tokensEdit = QLineEdit(self)
        self.tokensEdit.setPlaceholderText('例如: c2 r r 或 c2 t t r r')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.addWidget(QLabel('卡片(c1/c2/c3=寶具, r=隨機, t=打手卡):', self))
        layout.addWidget(self.tokensEdit, 1)

    def loadTokens(self, tokens: list):
        self.tokensEdit.setText(' '.join(tokens))

    def toLine(self) -> str:
        return 'card ' + self.tokensEdit.text().strip()


class MsLineWidget(QWidget):
    """`ms <skillNo 1-3> [useCharNo] [anotherCharNo]` (御主技能/禮裝技能)"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.skillNoSpin = QSpinBox(self)
        self.skillNoSpin.setRange(1, 3)
        self.useCharCombo = QComboBox(self)
        self.useCharCombo.addItem('無', -1)
        for i in range(1, 7):
            self.useCharCombo.addItem(str(i), i)
        self.anotherCharCombo = QComboBox(self)
        self.anotherCharCombo.addItem('無', -1)
        for i in range(1, 7):
            self.anotherCharCombo.addItem(str(i), i)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.addWidget(QLabel('技能', self))
        layout.addWidget(self.skillNoSpin)
        layout.addWidget(QLabel('換人1', self))
        layout.addWidget(self.useCharCombo)
        layout.addWidget(QLabel('換人2', self))
        layout.addWidget(self.anotherCharCombo)
        layout.addStretch(1)

    def loadTokens(self, tokens: list):
        self.skillNoSpin.setValue(int(tokens[0]))
        useChar = int(tokens[1]) if len(tokens) >= 2 else -1
        anotherChar = int(tokens[2]) if len(tokens) >= 3 else -1
        idx = self.useCharCombo.findData(useChar)
        self.useCharCombo.setCurrentIndex(idx if idx >= 0 else 0)
        idx = self.anotherCharCombo.findData(anotherChar)
        self.anotherCharCombo.setCurrentIndex(idx if idx >= 0 else 0)

    def toLine(self) -> str:
        line = f'ms {self.skillNoSpin.value()}'
        useChar = self.useCharCombo.currentData()
        anotherChar = self.anotherCharCombo.currentData()
        if anotherChar != -1:
            line += f' {useChar} {anotherChar}'
        elif useChar != -1:
            line += f' {useChar}'
        return line


class RawLineWidget(QWidget):
    """Escape hatch for anything the structured editors above don't cover
    (select/jump commands, or lines this editor doesn't recognize) - edited
    as the exact raw script line."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setPlaceholderText('例如: select 2 或 jump 5')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.addWidget(QLabel('原始指令:', self))
        layout.addWidget(self.lineEdit, 1)

    def loadRawLine(self, line: str):
        self.lineEdit.setText(line)

    def toLine(self) -> str:
        return self.lineEdit.text().strip()


LINE_TYPES = ['skill', 'card', 'ms', 'other']


class ScriptLineRow(QWidget):
    """One script-line row: a type combo driving a stacked param editor."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.typeCombo = QComboBox(self)
        self.typeCombo.addItem('skill (技能)', 'skill')
        self.typeCombo.addItem('card (選卡)', 'card')
        self.typeCombo.addItem('ms (御主技能)', 'ms')
        self.typeCombo.addItem('其他/原始指令', 'other')

        self.skillWidget = SkillLineWidget(self)
        self.cardWidget = CardLineWidget(self)
        self.msWidget = MsLineWidget(self)
        self.rawWidget = RawLineWidget(self)

        self.stack = QStackedWidget(self)
        self.stack.addWidget(self.skillWidget)
        self.stack.addWidget(self.cardWidget)
        self.stack.addWidget(self.msWidget)
        self.stack.addWidget(self.rawWidget)

        self.typeCombo.currentIndexChanged.connect(self.stack.setCurrentIndex)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.typeCombo)
        layout.addWidget(self.stack, 1)

    def setType(self, typeKey: str):
        idx = LINE_TYPES.index(typeKey) if typeKey in LINE_TYPES else LINE_TYPES.index('other')
        self.typeCombo.setCurrentIndex(idx)
        self.stack.setCurrentIndex(idx)

    def loadFromLine(self, line: str):
        tokens = line.split(' ')
        cmd = tokens[0] if tokens else ''
        if cmd == 'skill' and len(tokens) >= 3:
            self.setType('skill')
            self.skillWidget.loadTokens(tokens[1:])
        elif cmd == 'card' and len(tokens) >= 2:
            self.setType('card')
            self.cardWidget.loadTokens(tokens[1:])
        elif cmd == 'ms' and len(tokens) >= 2:
            self.setType('ms')
            self.msWidget.loadTokens(tokens[1:])
        else:
            self.setType('other')
            self.rawWidget.loadRawLine(line)

    def toLine(self) -> str:
        return self.stack.currentWidget().toLine()


# ---------------------------------------------------------------------------
# main editor view
# ---------------------------------------------------------------------------

class BattleEditorView(QWidget):
    """Battle 腳本編輯器 tab. Replaces game/fgo/ui/battleui.py's line-by-line
    console flow. Editing state lives entirely in the form/table on the
    right; 儲存 constructs a Battle exactly like ConfigUtil.Serialize does
    and (re)inserts it into game._battles."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._pool = WorkerPool.instance()
        self._currentKey = None  # None while editing a not-yet-saved new battle

        self._battleList = QListWidget(self)
        self._battleList.currentItemChanged.connect(self._onSelectionChanged)

        newBtn = QPushButton('新增', self)
        newBtn.clicked.connect(self._onNew)
        deleteBtn = QPushButton('刪除', self)
        deleteBtn.clicked.connect(self._onDelete)

        listButtons = QHBoxLayout()
        listButtons.addWidget(newBtn)
        listButtons.addWidget(deleteBtn)

        listPanel = QWidget(self)
        listLayout = QVBoxLayout(listPanel)
        listLayout.addWidget(QLabel('Battle 列表', listPanel))
        listLayout.addWidget(self._battleList)
        listLayout.addLayout(listButtons)

        editPanel = self._buildEditPanel()

        splitter = QSplitter(self)
        splitter.addWidget(listPanel)
        splitter.addWidget(editPanel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        controller.battlesChanged.connect(self._reloadList)
        self._reloadList()

    # -- form construction ---------------------------------------------------

    def _buildEditPanel(self) -> QWidget:
        panel = QWidget(self)

        infoGroup = QGroupBox('基本資料', panel)
        form = QFormLayout(infoGroup)

        self._nameEdit = QLineEdit(infoGroup)
        self._partySpin = QSpinBox(infoGroup)
        self._partySpin.setRange(1, 10)
        self._classCombo = QComboBox(infoGroup)
        for i in range(0, 11):
            self._classCombo.addItem(str(i), i)
        self._servantCombo = QComboBox(infoGroup)
        self._skillChecks = [QCheckBox('技能' + str(i + 1), infoGroup) for i in range(3)]
        for c in self._skillChecks:
            c.setChecked(True)
        self._craftEssenceCombo = QComboBox(infoGroup)

        skillRow = QHBoxLayout()
        for c in self._skillChecks:
            skillRow.addWidget(c)
        skillRow.addStretch(1)

        form.addRow('名稱:', self._nameEdit)
        form.addRow('隊伍編號 (1-10):', self._partySpin)
        form.addRow('好友職階:', self._classCombo)
        form.addRow('好友從者:', self._servantCombo)
        form.addRow('好友技能確認:', skillRow)
        form.addRow('禮裝:', self._craftEssenceCombo)

        self._populateServantCombo()
        self._populateCraftEssenceCombo()

        scriptGroup = self._buildScriptGroup()

        actionRow = QHBoxLayout()
        self._saveBtn = QPushButton('儲存', panel)
        self._saveBtn.clicked.connect(self._onSave)
        self._testRunCountSpin = QSpinBox(panel)
        self._testRunCountSpin.setRange(1, 999)
        self._testRunCountSpin.setValue(1)
        self._testRunBtn = QPushButton('測試執行', panel)
        self._testRunBtn.clicked.connect(self._onTestRun)
        actionRow.addWidget(self._saveBtn)
        actionRow.addWidget(QLabel('執行次數:', panel))
        actionRow.addWidget(self._testRunCountSpin)
        actionRow.addWidget(self._testRunBtn)
        actionRow.addStretch(1)

        layout = QVBoxLayout(panel)
        layout.addWidget(infoGroup)
        layout.addWidget(scriptGroup, 1)
        layout.addLayout(actionRow)

        self._setEditingEnabled(False)
        return panel

    def _buildScriptGroup(self) -> QWidget:
        group = QGroupBox('戰鬥腳本', self)

        self._rawModeCheck = QCheckBox('原始文字模式', group)
        self._rawModeCheck.toggled.connect(self._onRawModeToggled)

        addRowBtn = QPushButton('新增指令', group)
        addRowBtn.clicked.connect(lambda: self._addRow('skill 1 1'))
        removeRowBtn = QPushButton('刪除指令', group)
        removeRowBtn.clicked.connect(self._onRemoveRow)
        moveUpBtn = QPushButton('上移', group)
        moveUpBtn.clicked.connect(lambda: self._moveRow(-1))
        moveDownBtn = QPushButton('下移', group)
        moveDownBtn.clicked.connect(lambda: self._moveRow(1))

        toolbar = QHBoxLayout()
        toolbar.addWidget(addRowBtn)
        toolbar.addWidget(removeRowBtn)
        toolbar.addWidget(moveUpBtn)
        toolbar.addWidget(moveDownBtn)
        toolbar.addStretch(1)
        toolbar.addWidget(self._rawModeCheck)

        self._scriptTable = QTableWidget(0, 2, group)
        self._scriptTable.setHorizontalHeaderLabels(['#', '指令'])
        self._scriptTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._scriptTable.verticalHeader().setVisible(False)
        self._scriptTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._scriptTable.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._scriptTable.setColumnWidth(0, 32)

        self._rawTextEdit = QPlainTextEdit(group)
        self._rawTextEdit.setPlaceholderText('每行一個指令, 例如:\nskill 2 1\ncard c2 r r')

        self._scriptStack = QStackedWidget(group)
        self._scriptStack.addWidget(self._scriptTable)
        self._scriptStack.addWidget(self._rawTextEdit)

        layout = QVBoxLayout(group)
        layout.addLayout(toolbar)
        layout.addWidget(self._scriptStack, 1)
        return group

    def _populateServantCombo(self):
        self._servantCombo.clear()

        appNameByFolder = {}
        try:
            for entry in self._controller.game._configData.get('friendServant', []):
                appNameByFolder[entry['name']] = entry.get('AppName', entry['name'])
        except Exception:
            pass

        if not os.path.isdir(SERVANT_DIR):
            return

        for folder in sorted(os.listdir(SERVANT_DIR)):
            if not os.path.isdir(os.path.join(SERVANT_DIR, folder)):
                continue
            label = appNameByFolder.get(folder, folder)
            self._servantCombo.addItem(f'{label} ({folder})' if label != folder else folder, folder)

    def _populateCraftEssenceCombo(self):
        self._craftEssenceCombo.clear()
        self._craftEssenceCombo.addItem('(無禮裝)', -1)

        if not os.path.isdir(CRAFT_ESSENCE_DIR):
            return

        for fileName in sorted(os.listdir(CRAFT_ESSENCE_DIR)):
            base, ext = os.path.splitext(fileName)
            if ext.lower() != '.png' or not base.isdigit():
                continue
            self._craftEssenceCombo.addItem(base, int(base))

    # -- list handling --------------------------------------------------------

    def _reloadList(self):
        selectedKey = self._currentKey
        self._battleList.blockSignals(True)
        self._battleList.clear()
        for key in self._controller.game._battles:
            item = QListWidgetItem(key)
            self._battleList.addItem(item)
        self._battleList.blockSignals(False)

        if selectedKey is not None:
            items = self._battleList.findItems(selectedKey, Qt.MatchFlag.MatchExactly)
            if items:
                self._battleList.setCurrentItem(items[0])

    def _onSelectionChanged(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current is None:
            return
        self._loadBattle(current.text())

    def _onNew(self):
        self._currentKey = None
        self._battleList.setCurrentItem(None)
        self._nameEdit.setText('')
        self._partySpin.setValue(1)
        self._classCombo.setCurrentIndex(5)
        self._servantCombo.setCurrentIndex(0)
        for c in self._skillChecks:
            c.setChecked(True)
        self._craftEssenceCombo.setCurrentIndex(0)
        self._setRows([])
        self._rawModeCheck.setChecked(False)
        self._setEditingEnabled(True)
        self._testRunBtn.setEnabled(False)
        self._nameEdit.setFocus()

    def _onDelete(self):
        item = self._battleList.currentItem()
        if item is None:
            QMessageBox.information(self, '刪除 Battle', '請先選擇一個 Battle。')
            return

        key = item.text()
        if QMessageBox.question(
            self, '刪除 Battle',
            f'確定要刪除 "{key}" 嗎？如果有工作正在使用這個 Battle，該工作執行時會失敗。',
        ) != QMessageBox.StandardButton.Yes:
            return

        del self._controller.game._battles[key]
        Logger.info('Battle[' + key + ']刪除成功')
        self._currentKey = None
        self._controller.battlesChanged.emit()
        self._setEditingEnabled(False)

    def _loadBattle(self, key: str):
        battle = self._controller.game._battles.get(key)
        if battle is None:
            return

        self._currentKey = key
        self._nameEdit.setText(key)
        self._partySpin.setValue(battle._partyNumber)

        classIdx = self._classCombo.findData(battle._friendInfo.get('class', 5))
        self._classCombo.setCurrentIndex(classIdx if classIdx >= 0 else 5)

        servantIdx = self._servantCombo.findData(battle._friendInfo.get('name'))
        self._servantCombo.setCurrentIndex(servantIdx if servantIdx >= 0 else 0)

        for i, c in enumerate(self._skillChecks):
            c.setChecked(bool(battle._skill[i]) if i < len(battle._skill) else True)

        ceIdx = self._craftEssenceCombo.findData(battle._craftEssenceNo)
        self._craftEssenceCombo.setCurrentIndex(ceIdx if ceIdx >= 0 else 0)

        lines = [l for l in battle._script.splitlines() if l.strip() != '']
        self._setRows(lines)
        self._rawModeCheck.setChecked(False)

        self._setEditingEnabled(True)
        self._testRunBtn.setEnabled(True)

    def _setEditingEnabled(self, enabled: bool):
        for w in (
            self._nameEdit, self._partySpin, self._classCombo, self._servantCombo,
            self._craftEssenceCombo, self._scriptTable, self._rawTextEdit,
            self._rawModeCheck, self._saveBtn,
        ):
            w.setEnabled(enabled)
        for c in self._skillChecks:
            c.setEnabled(enabled)

    # -- script table ----------------------------------------------------------

    def _setRows(self, lines: list):
        self._scriptTable.setRowCount(0)
        for line in lines:
            self._addRow(line)

    def _addRow(self, line: str):
        row = self._scriptTable.rowCount()
        self._scriptTable.insertRow(row)

        numberItem = QTableWidgetItem(str(row + 1))
        numberItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self._scriptTable.setItem(row, 0, numberItem)

        rowWidget = ScriptLineRow(self._scriptTable)
        rowWidget.loadFromLine(line)
        self._scriptTable.setCellWidget(row, 1, rowWidget)
        self._scriptTable.selectRow(row)

    def _onRemoveRow(self):
        row = self._scriptTable.currentRow()
        if row < 0:
            return
        self._scriptTable.removeRow(row)
        self._renumberRows()

    def _moveRow(self, direction: int):
        lines = self._getRowsAsLines()
        row = self._scriptTable.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= len(lines):
            return
        lines[row], lines[target] = lines[target], lines[row]
        self._setRows(lines)
        self._scriptTable.selectRow(target)

    def _renumberRows(self):
        for row in range(self._scriptTable.rowCount()):
            self._scriptTable.item(row, 0).setText(str(row + 1))

    def _getRowsAsLines(self) -> list:
        lines = []
        for row in range(self._scriptTable.rowCount()):
            widget = self._scriptTable.cellWidget(row, 1)
            line = widget.toLine().strip()
            if line:
                lines.append(line)
        return lines

    def _onRawModeToggled(self, checked: bool):
        if checked:
            lines = self._getRowsAsLines()
            self._rawTextEdit.setPlainText('\n'.join(lines))
            self._scriptStack.setCurrentWidget(self._rawTextEdit)
        else:
            lines = [l for l in self._rawTextEdit.toPlainText().splitlines() if l.strip() != '']
            self._setRows(lines)
            self._scriptStack.setCurrentWidget(self._scriptTable)

    def _currentScriptLines(self) -> list:
        if self._rawModeCheck.isChecked():
            return [l for l in self._rawTextEdit.toPlainText().splitlines() if l.strip() != '']
        return self._getRowsAsLines()

    # -- save / test run --------------------------------------------------------

    def _onSave(self):
        name = self._nameEdit.text().strip()
        if not name or ' ' in name:
            QMessageBox.warning(self, '無法儲存', 'Battle 名稱不可為空或包含空格。')
            return

        if name != self._currentKey and name in self._controller.game._battles:
            QMessageBox.warning(self, '無法儲存', f'已經有名稱為 "{name}" 的 Battle。')
            return

        friendName = self._servantCombo.currentData()
        if friendName is None:
            QMessageBox.warning(self, '無法儲存', '請選擇好友從者 (找不到 assets/fgo/servant 底下的資料夾)。')
            return

        scriptLines = self._currentScriptLines()
        script = '\n'.join(scriptLines) + ('\n' if scriptLines else '')

        friendInfo = {
            'name': friendName,
            'class': self._classCombo.currentData(),
            'nameImage': cv2.imread(f'{SERVANT_DIR}/{friendName}/name.png'),
            'skill1': cv2.imread(f'{SERVANT_DIR}/{friendName}/skill1.png'),
            'skill2': cv2.imread(f'{SERVANT_DIR}/{friendName}/skill2.png'),
            'skill3': cv2.imread(f'{SERVANT_DIR}/{friendName}/skill3.png'),
        }
        skill = [c.isChecked() for c in self._skillChecks]
        craftEssenceNo = self._craftEssenceCombo.currentData()

        try:
            battle = Battle(
                self._controller.game._device, name, self._partySpin.value(),
                friendInfo, skill, script, craftEssenceNo,
            )
        except Exception as e:
            Logger.error('建立 Battle 失敗: ' + str(e))
            QMessageBox.critical(self, '儲存失敗', str(e))
            return

        if self._currentKey is not None and self._currentKey != name:
            del self._controller.game._battles[self._currentKey]

        self._controller.game._battles[name] = battle
        self._currentKey = name
        Logger.info('Battle[' + name + ']儲存成功')

        self._controller.battlesChanged.emit()
        self._testRunBtn.setEnabled(True)

    def _onTestRun(self):
        if self._currentKey is None:
            return
        battle = self._controller.game._battles.get(self._currentKey)
        if battle is None:
            return

        self._testRunBtn.setEnabled(False)
        self._pool.submit(
            battle.execute, self._testRunCountSpin.value(),
            on_error=self._onTestRunError,
            on_finished=lambda: self._testRunBtn.setEnabled(True),
        )

    def _onTestRunError(self, message: str):
        Logger.error('測試執行失敗: ' + message)
        QMessageBox.critical(self, '測試執行失敗', message)
