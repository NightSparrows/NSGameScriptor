
import os
import json
import datetime

from core.logger import Logger
from core.device.device import Device
from game.bluearchive.gamebluearchive import GameBlueArchive
from game.bluearchive.configutil import ConfigUtil
from game.bluearchive.task.hardquest import HardQuestTask
from game.bluearchive.task.contest import ContestTask

class BlueArchiveUI:

    def __init__(self) -> None:
        self._running = False
        self._device = Device()
        self._game = GameBlueArchive(self._device)

        self._configPath = './settings/bluearchive'

        # 讀取資料
        configData = ''
        try:
            with open(self._configPath + '/config.json') as f:
                configData = json.load(f)
        except:
            # 沒有檔案
            configData = ConfigUtil.GetDefault()
        
        ConfigUtil.Serialize(game=self._game, config=configData)


    def cmdHelp(self):
        print('Blue Archive 腳本')


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

    def cmdList(self):

        print(f"{'ID':<3}{'工作':<15}{'內容':<20}{'是否啟用':<5}{'執行日期':<10}",'\n')
        i = 0
        for task in self._game._taskManager._tasks:
            if task.getName() == 'HardQuest':
                taskName = '打困難圖'
            elif task.getName() == 'contest':
                taskName = '戰術大賽每日'
            else:
                taskName = '未知'
            print(
                f"{str(i):<3}{taskName:<15}{task.getInfo():<20}{str(task.isEnable()):<5}{datetime.datetime.strftime(task.getDate(), '%y/%m/%d %H:%M:%S')}",'\n'
            )
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
        
        if id >= len(self._game._taskManager._tasks):
            print('超過工作數')
        
        self._game._taskManager._tasks[id].execute()

    def cmdAddTask(self, cmdArgs):
        
        print('hard: 打困難圖')
        print('contest: 戰術大賽(基本上一個工作即可)')

        type = ''

        while True:
            try:
                type = input('工作類型: ')
                if type == 'help':
                    Logger.info('')
                    # TODO
                else:
                    break
            except:
                Logger.error('未知的輸入')
    
        if type == 'hard':
            try:
                areaNo = int(input('輸入地區(Area)(1~7): '))
                levelNo = int(input('輸入關卡(Level)(1~3): '))
            except:
                Logger.error('有問題的輸入')
                return

            if areaNo < 1 or areaNo > 7:
                print('未知的地區')
                return
            

            if levelNo < 1 or levelNo > 3:
                print('非法的關卡')
                return
            
            task = HardQuestTask(self._game._stateManager, self._game.mainQuestState, areaNo, levelNo, datetime.datetime.now(), True)
            self._game._taskManager.addTask(task)
            print('新增困難圖[' + str(areaNo) + '-' + str(levelNo) + ']任務成功')
            return
        if type == 'contest':
            task = ContestTask(self._game, datetime.datetime.now())
            self._game._taskManager.addTask(task)
            print('新增戰術大賽每日成功')
            return
        else:
            print('未知的任務類型')
            return
    
    def cmdRemoveTask(self, cmdArgs):
        try:
            id = int(cmdArgs[1])

            del self._game._taskManager._tasks[id]
            print('刪除成功')
        except:
            Logger.error('非法的輸入')



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


    def run(self):

        # TODO 看看模擬器之類的，先都重啟
        self._game.restart()
        #self._game.init()

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
                pass
            elif c == 'l' or c == 'list':
                self.cmdList()
            elif c == 'e' or c == 'exe':
                self.cmdRunTask(cmdArgs)
            elif c == 's' or c == 'save':
                self.save()
            elif c == 'a' or c == 'add':
                self.cmdAddTask(cmdArgs)
            elif c == 'r' or c == 'rm':
                self.cmdRemoveTask(cmdArgs)
                pass
            else:
                print('未知的命令')
            
        self.save()



