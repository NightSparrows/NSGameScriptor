
import os
import json

from core.logger import Logger
from core.device.device import Device

from game.fgo.gamefgo import GameFGO

from ..configutil import ConfigUtil

from .addtaskui import AddTaskUI

from core.util.stringutil import StringUtil
from core.util.serializeutil import SerializeUtil

from .battleui import BattleUI

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
            Logger.warn('No config file get a default')
            configData = ConfigUtil.GetDefault()
        
        self._device = Device(configData['device'], Device.ScreenCapType(configData['screencap']))
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

    def cmdHelp(self, args):
        print('Fate Grand Order 腳本')

        if len(args) <= 1:
            print(
                f"{'指令':<10}       {'Description'}",'\n',
                f"{'help/h':<10}     {'顯示此幫助'}",'\n',
                f"{'quit/q':<10}     {'結束此程式'}",'\n',
                f"{'list/l':<10}     {'列出所有工作'}",'\n',
                f"{'exe/e':<10}     {'執行工作'}",'\n',
                f"{'save/s':<10}     {'儲存設定檔'}",'\n',
                f"{'add/a':<10}     {'新增工作'}",'\n',
                f"{'run':<10}     {'執行過期的工作'}",'\n',
                f"{'edit':<10}     {'編輯設定'}",'\n',
                f"{'rm':<10}     {'刪除工作'}",'\n',
                f"{'battle':<10} {'執行battle'}",'\n',
                f"{'enable':<10} {'啟用工作'}",'\n',
                f"{'disable':<10} {'停用工作'}",'\n'
            )
            return
        
        typeStr = args[1]

        if typeStr == 'exe':
            print('執行工作')
            print('Usage: ')
            print('\texe [工作ID]')

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
    
    def cmdRemoveTask(self, args):
        if len(args) <= 1:
            print('無輸入工作')
            return
        
        try:
            id = int(args[1])

            if id >= len(self._game._taskManager._tasks):
                print('超出最大工作')
                return

        except:
            print('不是數字')
            return
        
        
        del self._game._taskManager._tasks[id]

        print('刪除成功')
        return


    def cmdEdit(self, args):

        if len(args) <= 1:
            print('input: edit [type] for editing')
            return
        
        typeInput = args[1]

        match typeInput:
            case 'device':
                deviceName = input('輸入device: ')

                self._device._connectDevice = deviceName
                print('修改成功: ' + deviceName)
            case 'battle':
                BattleUI.Run(self._game)
            case _:
                print('未知')

    def cmdBattle(self, args):

        if len(args) <= 1:
            print('input: battle [name] [count]')
            return

        try:
            battle = self._game._battles[args[1]]
        except:
            Logger.warn('Unknown battle script')
            return

        if battle == None:
            print('Unknown battle name')
            return
        
        if len(args) <= 2:
            battle.execute(1)
        else:
            try:
                count = int(args[2])
            except Exception as e:
                Logger.warn('Your parameter is not a number')
                return
            
            for i in range(5):
                try:
                    result, currentCount = battle.execute(count)
                    count -= currentCount

                    Logger.info('Execute success: ' + str(result) + ', count: ' + str(currentCount))
                    
                    if count == 0:
                        break

                except Exception as e:
                    Logger.error('執行失敗:')
                    Logger.error('Error[', e.__name__, ']: ', e)
                    Logger.info('Try to reconnect it')
                    self._device.restart()
                    Logger.info('Try to restart')

    def cmdEnable(self, args):
        if len(args) <= 1:
            print('無輸入工作')
            return

        try:
            taskId = int(args[1])

            if taskId >= len(self._game._taskManager._tasks):
                print('超出最大工作')
                return

        except:
            print('非法輸入')
            return

        task = self._game._taskManager._tasks[taskId]

        task._enable = True

        print('Task[' + task.getName() + ']啟用成功')


    def cmdDisable(self, args):
        if len(args) <= 1:
            print('無輸入工作')
            return

        try:
            taskId = int(args[1])

            if taskId >= len(self._game._taskManager._tasks):
                print('超出最大工作')
                return

        except:
            print('非法輸入')
            return

        task = self._game._taskManager._tasks[taskId]

        task._enable = False

        print('Task[' + task.getName() + ']停用成功')



    def run(self):

        if not self._game.init():
            print('無法初始化FGO')
            return

        self._running = True
        while self._running:
            cmd = input('>')

            if cmd == 'quit' or cmd == 'q':
                self._running = False
                break

            cmdArgs = cmd.split(' ')

            c = cmdArgs[0]

            if c == 'h' or c == 'help':
                self.cmdHelp(cmdArgs)
            elif c == 'a' or c == 'add':
                self.cmdAdd(cmdArgs)
            elif c == 'l' or c == 'list':
                self.cmdList()
            elif c == 'e' or c == 'exe':
                self.cmdRunTask(cmdArgs)
            elif c == 'run':
                self._game.execute()
            elif c == 'save':
                self.save()
            elif c == 'edit':
                self.cmdEdit(cmdArgs)
            elif c == 'rm':
                self.cmdRemoveTask(cmdArgs)
            elif c == 'battle':
                self.cmdBattle(cmdArgs)
            elif c == 'enable':
                self.cmdEnable(cmdArgs)
            elif c == 'disable':
                self.cmdDisable(cmdArgs)
            else:
                print('未知的命令')
            
        self.save()

