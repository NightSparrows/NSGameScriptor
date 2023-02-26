
import datetime
import json

import cv2

from core.logger import Logger
from core.util.serializeutil import SerializeUtil

from game.fgo.gamefgo import GameFGO
from game.fgo.battle.battle import Battle

class ConfigUtil:

    def GetDefault():

        configData = {
            'device': 'emulator-5554',
            'battle': [
                {
                    'name': 'ArtParty',
                    'partyNumber': 10,
                    'classChoosing': 5,
                    'friendServantName': 'altriaCaster',
                    'skill': [True, True, True],
                    'script': 'skill 2 1\nskill 2 2\nskill 2 3\nskill 1 1\nskill 1 2 2\nskill 1 3 2\nskill 3 1\nskill 3 2 2\nskill 3 3 2\ncard c2 r r\ncard c2 r r\ncard c2 r r\ncard r r r\n'

                }
            ]
        }

        return configData
    
    def Deserialize(game: GameFGO):
        data = dict()

        data['device'] = game._device._connectDevice


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


        data['task'] = []
        return json.dumps(data)

    def Serialize(game: GameFGO, config):

        game._device._connectDevice = config['device']

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
            battle = Battle(
                game._device,
                battleData['partyNumber'],
                friendInfo,
                battleData['skill'],
                battleData['script']
            )
            game._battles[battleData['name']] = battle

        #taskConfig = config['task']

        return True

