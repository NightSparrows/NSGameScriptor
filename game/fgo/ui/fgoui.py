
import os
import json

from core.logger import Logger
from core.device.device import Device

from game.fgo.gamefgo import GameFGO

from ..configutil import ConfigUtil

from .addtaskui import AddTaskUI

from core.util.stringutil import StringUtil
from core.util.serializeutil import SerializeUtil

class FGOUI:

    def __init__(self) -> None:
        self._running = False
        
        self._configPath = './settings/fgo'

        # 讀取資料
        configData = ''
        try:
            with open(self._configPath + '/config.json') as f:
                configData = json.load(f)
        except:
            # 沒有檔案
            configData = ConfigUtil.GetDefault()
        
        self._device = Device(configData['device'])
        self._game = GameFGO(self._device)
        ConfigUtil.Serialize(self._game, configData)

    def save(self):
        Logger.info('儲存中...')
        if not os.path.exists(self._configPath):
            os.makedirs(self._configPath)

        # TODO 存檔
        configData = ConfigUtil.Deserialize(self._game)
        try:
            f = open(self._configPath + '/config.json', 'w')
            f.write(configData)
            Logger.info('儲存成功')
        except:
            Logger.error('無法寫入設定檔')
        finally:
            f.close()

    def cmdHelp(self):
        print('Fate Grand Order 腳本')

        print(
            f"{'指令':<10}       {'Description'}",'\n',
            f"{'help/h':<10}     {'顯示此幫助'}",'\n',
            f"{'quit/q':<10}     {'結束此程式'}",'\n',
            f"{'list/l':<10}     {'列出所有工作'}",'\n',
            f"{'exe/e':<10}     {'執行工作'}",'\n',
            f"{'save/s':<10}     {'儲存設定檔'}",'\n',
            f"{'add/a':<10}     {'新增工作'}",'\n',
            f"{'rm/r':<10}     {'刪除工作'}",'\n'
        )

    def cmdAdd(self, cmdArgs):
        AddTaskUI.Run(self._game)

    def cmdList(self):

        print(StringUtil.align('ID', 5) + StringUtil.align('工作', 15) + StringUtil.align('內容', 30) + StringUtil.align('是否啟用', 10) + StringUtil.align('執行日期', 30))
        i = 0
        for task in self._game._taskManager._tasks:
            print(StringUtil.align(str(i), 5) + StringUtil.align(task.getName(), 15) + StringUtil.align(task.getInfo(), 30) + StringUtil.align(str(task.isEnable()), 10) + StringUtil.align(SerializeUtil.GetStringFromDateTime(task.getDate()), 30))
            
            i += 1

    def cmdRunTask(self, args):
        if len(args) <= 1:
            print('無輸入工作')
            return
        
        try:
            id = int(args[1])
        except:
            print('不是數字')
            return
        
        result = self._game._taskManager.runTask(id)

        if result == -1:
            print('非法工作ID')
        elif result == -2:
            print('工作執行失敗')
        
    def run(self):

        self._game.init()

        self._running = True
        while self._running:
            cmd = input('>')

            if cmd == 'quit' or cmd == 'q':
                self._running = False
                break

            cmdArgs = cmd.split(' ')

            c = cmdArgs[0]

            if c == 'h' or c == 'help':
                self.cmdHelp()
            elif c == 'a' or c == 'add':
                self.cmdAdd(cmdArgs)
            elif c == 'l' or c == 'list':
                self.cmdList()
            elif c == 'e' or c == 'exe':
                self.cmdRunTask(cmdArgs)
            elif c == 'run':
                self._game.execute()
            else:
                print('未知的命令')
            
        self.save()

