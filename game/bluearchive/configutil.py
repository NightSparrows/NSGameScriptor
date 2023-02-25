
import datetime
import json

from core.logger import Logger
from core.game.game import Game
from game.bluearchive.task.hardquest import HardQuestTask
from game.bluearchive.task.contest import ContestTask

class ConfigUtil:

    def GetDatetimeFromString(dateString: str):
        return datetime.datetime.strptime(dateString, '%y/%m/%d %H:%M:%S')

    def GetStringFromDateTime(date: datetime):
        return datetime.datetime.strftime(date, '%y/%m/%d %H:%M:%S')

    def GetDefault():

        configData = {
            'device': 'emulator-5554',
            'task' : [
                {
                    'type': 'HardQuest',
                    'areaNo': 1,
                    'levelNo': 1,
                    'date': '23/02/24 12:00:00',
                    'enable': False
                }
            ]
        }

        return configData
    
    def Deserialize(game):
        data = dict()

        data['device'] = game._device._connectDevice

        data['task'] = []
        for task in game._taskManager._tasks:
            taskData = dict()
            taskType = task.getName()
            if taskType == 'HardQuest':
                taskData['type'] = task.getName()
                taskData['areaNo'] = task._areaNo
                taskData['levelNo'] = task._levelNo
            elif taskType == 'contest':
                taskData['type'] = task.getName()
            else:
                continue

            taskData['enable'] = task.isEnable()
            taskData['date'] = ConfigUtil.GetStringFromDateTime(task.getDate())
            data['task'].append(taskData)
        
        return json.dumps(data)

    def Serialize(game: Game, config):

        taskConfig = config['task']

        for task in taskConfig:
            type = task['type']

            if type == 'HardQuest':     # 為打困難碎片
                t = HardQuestTask(game._stateManager, game.mainQuestState, task['areaNo'], task['levelNo'], ConfigUtil.GetDatetimeFromString(task['date']), task['enable'])
                Logger.info('[載入工作] 困難圖')
            elif type == 'contest':
                t = ContestTask(game, ConfigUtil.GetDatetimeFromString(task['date']), task['enable'])
                Logger.info('[載入工作] 戰術大賽每日')
            else:
                Logger.warn('未知的工作: ' + type)
                continue

            game._taskManager.addTask(t)


        return True

