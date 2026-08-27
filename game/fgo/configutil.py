
import datetime
import json

import cv2

from core.logger import Logger
from core.util.serializeutil import SerializeUtil
from core.device.device import Device

from game.fgo.gamefgo import GameFGO
from game.fgo.battle.battle import Battle

from game.fgo.task.activitytask import ActivityTask
from game.fgo.task.qptask import QPTask
from game.fgo.task.exptask import EXPTask

from game.fgo.battle.apple import Apple

# Searialize settings file
class ConfigUtil:

    # 讀取設定檔, 建立 Device/GameFGO 並套用設定 (供 CLI 與 GUI 共用)
    def LoadGame(configPath: str = 'settings/fgo') -> GameFGO:

        configData = ''
        try:
            with open(configPath + '/config.json', encoding='utf-8') as f:
                configData = json.load(f)

                if not configData['screencap']:
                    configData['screencap'] = 0                     # make ascreencap default for version issue
        except FileNotFoundError as e:
            Logger.warn('No config file found')
            configData = ConfigUtil.GetDefault()
        except IsADirectoryError as e:
            Logger.warn('wired. Is a directory file')
            configData = ConfigUtil.GetDefault()
        except PermissionError as e:
            Logger.warn('You don\'t have permission to access config file.')
            configData = ConfigUtil.GetDefault()
        except json.JSONDecodeError as e:
            Logger.error('Json decoding error: {e}')
            configData = ConfigUtil.GetDefault()
        except TypeError as e:
            Logger.error('Json Type error: {e}')
            configData = ConfigUtil.GetDefault()
        except Exception as e:
            # 沒有檔案
            Logger.warn('Unknown error: ' + str(e))
            configData = ConfigUtil.GetDefault()

        screencapType = Device.ScreenCapType(configData['screencap'])

        if 'emulator' in configData:
            emulatorType = Device.EmulatorType(configData['emulator'])
        else:
            # 舊設定檔沒有這個欄位 - 沿用以前的推測邏輯做一次性遷移預設值,
            # 下次儲存後就會變成明確欄位
            emulatorType = Device.EmulatorType.MUMU if screencapType == Device.ScreenCapType.NEMUIPC else Device.EmulatorType.NONE

        device = Device(configData['device'], screencapType, emulatorType)
        game = GameFGO(device)
        ConfigUtil.Serialize(game, configData)

        return game

    def GetDefault():

        configData = {
            'device': 'emulator-5554',
            'screencap': 1,
            'emulator': 0,
            'battle': [
                {
                    'name': 'ArtParty',
                    'partyNumber': 10,
                    'classChoosing': 5,
                    'friendServantName': 'altriaCaster',
                    'skill': [True, True, True],
                    'script': 'skill 2 1\nskill 2 2\nskill 2 3\nskill 1 1\nskill 1 2 2\nskill 1 3 2\nskill 3 1\nskill 3 2 2\nskill 3 3 2\ncard c2 r r\ncard c2 r r\ncard c2 r r\ncard r r r\n'

                }
            ],
            'task': [],
            'apple': 'gold'
        }

        return configData
    
    def Deserialize(game: GameFGO):
        data = dict()

        data['device'] = game._device._connectDevice

        data['screencap'] = game._device._screenCapType.value
        data['emulator'] = game._device._emulatorType.value

        data['battle'] = []
        for key in game._battles:
            battle = game._battles[key]
            battleData = dict()
            battleData['name'] = key
            battleData['partyNumber'] = battle._partyNumber
            battleData['classChoosing'] = battle._friendInfo['class']
            battleData['friendServantName'] = battle._friendInfo['name']
            battleData['skill'] = battle._skill
            battleData['script'] = battle._script
            battleData['craftEssenceNo'] = battle._craftEssenceNo

            data['battle'].append(battleData)


        data['task'] = []
        for task in game._taskManager._tasks:
            taskData = dict()
            taskData['type'] = task.getName()
            taskData['date'] = SerializeUtil.GetStringFromDateTime(task.getDate())
            taskData['enable'] = task.isEnable()
            if task.getName() == 'ActivityTask':
                taskData['areaName'] = task._areaName
                taskData['levelName'] = task._levelName
                taskData['count'] = task._count
                taskData['interval'] = task._interval.total_seconds()

                for key in game._battles:
                    if game._battles[key] == task._battle:
                        taskData['battleKey'] = key
                        break
                # end
            elif task.getName() == 'qptask':
                taskData['count'] = task._count
                taskData['battleKey'] = game.getKeyFromBattle(task._battle)
            elif task.getName() == 'exptask':
                taskData['count'] = task._count
                taskData['battleKey'] = game.getKeyFromBattle(task._battle)
            else:
                Logger.error('Unknown FGO task type')

            data['task'].append(taskData)
        
        data['apple'] = Apple.s_appleTypeName
        

        return json.dumps(data, indent=4, ensure_ascii=False)

    def Serialize(game: GameFGO, config):

        game._device._connectDevice = config['device']
        game._device._screenCapType = Device.ScreenCapType(config['screencap'])
        try:
            Apple.s_appleTypeName = config['apple']
        except Exception as e:
            Apple.s_appleTypeName = 'gold'

        for battleData in config['battle']:
            friend = battleData['friendServantName']
            friendInfo= {
                'name' : friend,
                'class' : battleData['classChoosing'],            # TODO: 我懶得設定以後再說，預設術職
                'nameImage' : cv2.imread('./assets/fgo/servant/' + friend + '/name.png'),
                'skill1' : cv2.imread('./assets/fgo/servant/' + friend + '/skill1.png'),
                'skill2' : cv2.imread('./assets/fgo/servant/' + friend + '/skill2.png'),
                'skill3' : cv2.imread('./assets/fgo/servant/' + friend + '/skill3.png')
            }
            craftEssenceNo = -1
            try:
                if battleData['craftEssenceNo'] != None:
                    craftEssenceNo = battleData['craftEssenceNo']
            except Exception as e:
                Logger.warn('無禮裝設定')
            battle = Battle(
                game._device,
                battleData['name'],
                battleData['partyNumber'],
                friendInfo,
                battleData['skill'],
                battleData['script'],
                craftEssenceNo
            )
            game._battles[battleData['name']] = battle

        #taskConfig = config['task']
        for taskData in config['task']:
            date = SerializeUtil.GetDatetimeFromString(taskData['date'])
            enable = taskData['enable']
            match taskData['type']:
                case 'ActivityTask':
                    areaName = taskData['areaName']
                    levelID = taskData['levelName']
                    count = taskData['count']
                    interval = datetime.timedelta(seconds=taskData['interval'])

                    for key in game._battles:
                        if key == taskData['battleKey']:
                            battle = game._battles[key]
                            break
                    
                    task = ActivityTask(game._stateManager, game, areaName, levelID, battle, count, interval, date, enable)
                    game._taskManager.addTask(task)

                case 'qptask':
                    count = taskData['count']
                    battle = game.getBattleFromKey(taskData['battleKey'])

                    task = QPTask(game, battle, count, date, enable)
                    game._taskManager.addTask(task)

                case 'exptask':
                    count = taskData['count']
                    battle = game.getBattleFromKey(taskData['battleKey'])

                    task = EXPTask(game, battle, count, date, enable)
                    game._taskManager.addTask(task)

                case _:
                    pass


        return True

