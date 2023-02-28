
import datetime

from core.util.stringutil import StringUtil

from game.fgo.gamefgo import GameFGO
from game.fgo.ui.util.listutil import ListUtil

from game.fgo.task.activitytask import ActivityTask

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

        ListUtil.ListBattleInfo(game)

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


    def Run(game: GameFGO):

        print('新增FGo工作')
        
        print('類型:')
        print('0: 活動關卡周回')

        try:
            taskType = int(input('輸入類型: '))
        except:
            print('非法輸入!')
            return False

        match taskType:
            case 0:
                return AddTaskUI.addActivityTask(game)
            case _:
                print('未知的工作類型')
                return False


