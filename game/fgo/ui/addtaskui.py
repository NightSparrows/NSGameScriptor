
import time
import datetime

from core.util.stringutil import StringUtil
from core.util.inpututil import InputUtil

from game.fgo.gamefgo import GameFGO

from game.fgo.task.activitytask import ActivityTask
from game.fgo.task.qptask import QPTask
from game.fgo.task.exptask import EXPTask
from .battleui import BattleUI


class AddTaskUI:

    def addActivityTask(game: GameFGO):

        # read the current activity
        print()
        print('現在活動為: ' + game.activityState._activityName)

        print('\n' + StringUtil.align('Key', 20) + StringUtil.align('名稱', 30))
        for key in game.activityState._levels:
            print(StringUtil.align(key, 20) + StringUtil.align(game.activityState._levels[key]['appName'], 30))
        
        try:
            areaName = input('輸入地區(英文): ')

            areaData = game.activityState._levels[areaName]

            if areaData == None:
                print('地區輸入錯誤')
                return False

        except:
            print('非法輸入!')
            return False
        
        print(StringUtil.align('ID', 10) + StringUtil.align('名稱', 20))
        for level in areaData['level']:
            print(StringUtil.align(level['imageName'], 10) + StringUtil.align(level['name'], 20))

        try:
            levelID = input('輸入ID: ')

            found = False
            for level in areaData['level']:
                if level['imageName'] == levelID:
                    found = True
                    break
            
            if not found:
                print('非法ID輸入')
                return False

        except:
            print('非法輸入!')
            return False

        # list battle info

        BattleUI.CmdList(game)

        try:
            battleKey = input('輸入Key: ')

            battle = game._battles[battleKey]

            if battle == None:
                print('未知的Key')
                return False

        except:
            print('非法輸入!')
            return False


        try:
            count = int(input('輸入次數: '))

        except:
            print('非法輸入!')
            return False
        
        task = ActivityTask(game._stateManager, game, areaName, levelID, battle, count, datetime.timedelta(hours=2), datetime.datetime.now())

        game._taskManager.addTask(task)
        print('Task新增成功')
        return True

    def addDailyTask(game: GameFGO):
        
        print()
        print(StringUtil.align('ID', 5) + StringUtil.align('類型', 20))
        print(StringUtil.align('0', 5) + StringUtil.align('QP每日任務', 20))
        print(StringUtil.align('1', 5) + StringUtil.align('EXP每日任務', 20))
        print()
        taskType = InputUtil.InputNumber(0, 1, '任務類型(ID)>')
        
        if taskType == None:
            print('非法輸入')
            return False

        count = InputUtil.InputNumber(1, 100, '次數>')
        if count == None:
            print('非法次數')
            return False

        BattleUI.CmdList(game)

        battleKey = InputUtil.InputString('Key>')
        if battleKey == None:
            print('非法輸入')
            return False
        
        battle = game.getBattleFromKey(battleKey)

        if battle == None:
            print('Key輸入錯誤')
            return False

        match taskType:
            case 0:
                task = QPTask(game, battle, count, datetime.datetime.combine(datetime.datetime.now().date(), datetime.time()), True)
                game._taskManager.addTask(task)
                print('QPTask新增成功')
                return True
            case 1:
                task = EXPTask(game, battle, count, datetime.datetime.combine(datetime.datetime.now().date(), datetime.time()), True)
                game._taskManager.addTask(task)
                print('EXPTask新增成功')
                return True
            case _:
                print('未知的類型')
                return False

        return False

    def Run(game: GameFGO):

        print('新增FGo工作')
        
        print('類型:')
        print('0: 活動關卡周回')
        print('1: 每日周回任務')

        try:
            taskType = int(input('輸入類型: '))
        except:
            print('非法輸入!')
            return False

        match taskType:
            case 0:
                return AddTaskUI.addActivityTask(game)
            case 1:
                return AddTaskUI.addDailyTask(game)
            case _:
                print('未知的工作類型')
                return False


