
import datetime
import json
import os
import shutil

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

SERVANT_DIR = './assets/fgo/servant'
DEFAULT_FRIEND_CLASS = 5        # 術職

# Searialize settings file
class ConfigUtil:

    # 讀取設定檔, 建立 Device/GameFGO 並套用設定 (供 CLI 與 GUI 共用)
    def LoadGame(configPath: str = 'settings/fgo') -> GameFGO:

        configData = ''
        fromFile = False
        try:
            with open(configPath + '/config.json', encoding='utf-8') as f:
                configData = json.load(f)

                if not configData['screencap']:
                    configData['screencap'] = 0                     # make ascreencap default for version issue
            fromFile = True
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

        isLegacy = fromFile and ConfigUtil.IsLegacyConfig(configData)

        screencapType = Device.ScreenCapType(configData['screencap'])

        if 'emulator' in configData:
            emulatorType = Device.EmulatorType(configData['emulator'])
        else:
            # 舊設定檔沒有這個欄位 - 沿用以前的推測邏輯做一次性遷移預設值,
            # 下次儲存後就會變成明確欄位
            emulatorType = Device.EmulatorType.MUMU if screencapType == Device.ScreenCapType.NEMUIPC else Device.EmulatorType.NONE

        emulatorPath = configData.get('emulatorPath') or None

        device = Device(configData['device'], screencapType, emulatorType, emulatorPath)
        game = GameFGO(device)
        ConfigUtil.Serialize(game, configData)

        if isLegacy:
            ConfigUtil.MigrateLegacyConfig(game, configPath)

        return game

    # 舊版設定檔每個 battle 都有 classChoosing (好友職階), 新版改由從者資料夾的 info.json 決定
    def HasLegacyFriendClass(configData) -> bool:
        return any('classChoosing' in b for b in configData.get('battle', []))

    # 舊版設定檔的 apple 是單一字串 (例如 'gold'), 新版是依優先順序排列的 list (例如 ['bronze', 'silver'])
    def HasLegacyApple(configData) -> bool:
        return isinstance(configData.get('apple'), str)

    def IsLegacyConfig(configData) -> bool:
        return ConfigUtil.HasLegacyFriendClass(configData) or ConfigUtil.HasLegacyApple(configData)

    # 把舊版設定檔備份後, 以新格式覆寫
    # 備份檔已存在 (之前升級過) 就換一個編號, 不覆蓋舊的備份
    def MigrateLegacyConfig(game: GameFGO, configPath: str):
        configFile = configPath + '/config.json'
        backupFile = configFile + '.bak-legacy'
        number = 2
        while os.path.exists(backupFile):
            backupFile = configFile + '.bak-legacy-' + str(number)
            number += 1
        try:
            shutil.copyfile(configFile, backupFile)
            with open(configFile, 'w', encoding='utf-8') as f:
                f.write(ConfigUtil.Deserialize(game))
            Logger.info('舊版設定檔已轉換為新格式 (備份: ' + backupFile + ')')
        except Exception as e:
            Logger.error('轉換舊版設定檔失敗: ' + str(e))

    # 讀取 assets/fgo/servant/<name>/info.json, 格式: {"class": 5, "AppName": "顯示名稱"}
    # 檔案不存在或格式錯誤時回傳空 dict
    def GetServantInfo(servantName: str) -> dict:
        infoPath = SERVANT_DIR + '/' + servantName + '/info.json'
        try:
            with open(infoPath, encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            Logger.warn('讀取從者資料失敗 (' + infoPath + '): ' + str(e))
            return {}

    # 好友從者的顯示名稱, 沒有設定 AppName 就用資料夾名稱
    def GetServantAppName(servantName: str) -> str:
        return ConfigUtil.GetServantInfo(servantName).get('AppName') or servantName

    # 列出所有好友從者: [(資料夾名稱, 顯示名稱), ...]
    def ListServants() -> list:
        if not os.path.isdir(SERVANT_DIR):
            return []
        return [
            (folder, ConfigUtil.GetServantAppName(folder))
            for folder in sorted(os.listdir(SERVANT_DIR))
            if os.path.isdir(os.path.join(SERVANT_DIR, folder))
        ]

    # 好友從者的職階(助戰頁籤索引)
    # legacyClass: 舊版設定檔的 classChoosing, 從者沒有設定 class 時才會使用
    def GetServantClass(servantName: str, legacyClass: int | None = None) -> int:
        try:
            return int(ConfigUtil.GetServantInfo(servantName)['class'])
        except Exception:
            fallback = legacyClass if legacyClass is not None else DEFAULT_FRIEND_CLASS
            Logger.warn('從者 ' + servantName + ' 沒有設定職階 (info.json), 使用職階 ' + str(fallback))
            return fallback

    # 建立 Battle 用的 friendInfo
    def MakeFriendInfo(servantName: str, legacyClass: int | None = None) -> dict:
        return {
            'name': servantName,
            'class': ConfigUtil.GetServantClass(servantName, legacyClass),
            'nameImage': cv2.imread(SERVANT_DIR + '/' + servantName + '/name.png'),
            'skill1': cv2.imread(SERVANT_DIR + '/' + servantName + '/skill1.png'),
            'skill2': cv2.imread(SERVANT_DIR + '/' + servantName + '/skill2.png'),
            'skill3': cv2.imread(SERVANT_DIR + '/' + servantName + '/skill3.png'),
        }

    def GetDefault():

        configData = {
            'device': 'emulator-5554',
            'screencap': 1,
            'emulator': 0,
            'emulatorPath': '',
            'battle': [
                {
                    'name': 'ArtParty',
                    'partyNumber': 10,
                    'friendServantName': 'altriaCaster',
                    'skill': [True, True, True],
                    'script': 'skill 2 1\nskill 2 2\nskill 2 3\nskill 1 1\nskill 1 2 2\nskill 1 3 2\nskill 3 1\nskill 3 2 2\nskill 3 3 2\ncard c2 r r\ncard c2 r r\ncard c2 r r\ncard r r r\n'

                }
            ],
            'task': [],
            'apple': list(Apple.DEFAULT_SEQUENCE)
        }

        return configData
    
    def Deserialize(game: GameFGO):
        data = dict()

        data['device'] = game._device._connectDevice

        data['screencap'] = game._device._screenCapType.value
        data['emulator'] = game._device._emulatorType.value
        data['emulatorPath'] = game._device._emulatorPath or ''

        data['battle'] = []
        for key in game._battles:
            battle = game._battles[key]
            battleData = dict()
            battleData['name'] = key
            battleData['partyNumber'] = battle._partyNumber
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
        
        data['apple'] = list(Apple.s_appleSequence)
        

        return json.dumps(data, indent=4, ensure_ascii=False)

    def Serialize(game: GameFGO, config):

        game._device._connectDevice = config['device']
        game._device._screenCapType = Device.ScreenCapType(config['screencap'])
        game._device._emulatorPath = config.get('emulatorPath') or None
        Apple.s_appleSequence = Apple.normalizeSequence(config.get('apple'))

        for battleData in config['battle']:
            friendInfo = ConfigUtil.MakeFriendInfo(battleData['friendServantName'], battleData.get('classChoosing'))
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

