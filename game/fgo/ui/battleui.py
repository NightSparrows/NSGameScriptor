
import cv2

from core.logger import Logger

from core.util.stringutil import StringUtil

from game.fgo.gamefgo import GameFGO
from game.fgo.battle.battle import Battle

class BattleUI:

    def CmdAdd(game: GameFGO):

        # {"name": "ArtParty", "partyNumber": 10, "classChoosing": 5, "friendServantName": "altriaCaster", "skill": [true, true, true], "script": "skill 2 1\nskill 2 2\nskill 2 3\nskill 1 1\nskill 1 2 2\nskill 1 3 2\nskill 3 1\nskill 3 2 2\nskill 3 3 2\ncard c2 r r\ncard c2 r r\ncard c2 r r\ncard r r r\n"}

        print('不要有空格')
        battleName = input('Battle名稱(英數)>')

        for char in battleName:
            if char == ' ':
                print('錯誤: 名稱有空格')
                return
        
        try:
            partyNumber = int(input('隊伍編號(1~10)>'))
            if partyNumber < 1 or partyNumber > 10:
                print('不是1~10')
                return
        except:
            print('非法輸入')
            return
        
        print('職階選擇(0~10)(預設5)')
        classChooseStr = input('職階>')
        
        if classChooseStr == '':
            classChoosing = 5
        else:
            try:
                classChoosing = int(classChooseStr)
                if classChoosing < 1 or classChoosing > 10:
                    print('不是1~10')
                    return
            except:
                print('非法輸入')
                return

        print(StringUtil.align('ID', 5) + StringUtil.align('從者名稱', 20))
        i = 0
        for servantData in game._configData['friendServant']:
            print(StringUtil.align(str(i), 5) + StringUtil.align(servantData['AppName'], 20))
            i += 1
        
        print('輸入要使用的好友從者')
        try:
            servantID = int(input('ID>'))
            i = 0
            isFound = False
            
            for servantData in game._configData['friendServant']:
                if servantID == i:
                    isFound = True
                    friendServantName = servantData['name']
                    break
                i += 1
            
            if not isFound:       
                print('輸入未知的ID')
                return
 
        except:
            print('非法輸入')
            return

        # 預設3個true for skill  好了
        skill = [True, True, True]


        # Editing script
        scriptList = list()

        while True:

            cmdLine = input('戰鬥腳本>')

            if cmdLine == 'q' or cmdLine == 'quit':
                break

            cmdArgs = cmdLine.split(' ')

            cmd = cmdArgs[0]

            if cmd == 'a' or cmd == 'add':
                operateStr = BattleUI.GetOperateStr()
                if operateStr != '':
                    scriptList.append(operateStr)
            else:
                print('未知的指令')
# friendInfo= {
            # 'name' : friend,
            # 'class' : 5,            # TODO: 我懶得設定以後再說，預設術職
            # 'nameImage' : cv2.imread('.//assets//fgo//servant//' + friend + '//name.png'),
            # 'skill1' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill1.png'),
            # 'skill2' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill2.png'),
            # 'skill3' : cv2.imread('.//assets//fgo//servant//' + friend + '//skill3.png')
            # }
        friendInfo = {
            'name': friendServantName,
            'class': classChoosing,
            'nameImage': cv2.imread('.//assets//fgo//servant//' + friendServantName + '//name.png'),
            'skill1': cv2.imread('.//assets//fgo//servant//' + friendServantName + '//skill1.png'),
            'skill2': cv2.imread('.//assets//fgo//servant//' + friendServantName + '//skill2.png'),
            'skill3': cv2.imread('.//assets//fgo//servant//' + friendServantName + '//skill3.png'),
        }

        scriptStr = ''
        for script in scriptList:
            scriptStr += script

        battle = Battle(game._device, partyNumber, friendInfo, skill, scriptStr)
        
        game._battles[battleName] = battle
        print('新增成功')

        
        return

    def GetOperateStr():
        print('0: 使用技能')
        print('1: 使用卡')
        print('2: 使用禮裝')
        try:
            operateType = int(input('動作>'))
        except:
            print('非法輸入')
            return ''
        
        if operateType == 0:
            try:
                servantNo = int(input('選擇從者(1~3)>'))

                if servantNo < 1 or servantNo > 3:
                    print('不為1~3')
                    return ''
                
                skillNo = int(input('使用的技能(1~3)>'))

                if skillNo < 1 or skillNo > 3:
                    print('不為1~3')
                    return ''

                useCharNo = int(input('被使用的從者(1~3)(沒有:-1)>'))

                if useCharNo != -1 and (useCharNo < 1 or useCharNo > 3):
                    print('不為1~3或-1')
                    return ''
                
                scriptStr = 'skill ' + str(servantNo) + ' ' + str(skillNo)

                if useCharNo != -1:
                    scriptStr += ' ' + str(useCharNo)
                
                scriptStr += '\n'

                Logger.trace('[SCRIPT] ' + scriptStr)

                return scriptStr

            except:
                print('非法輸入')
                return ''
        elif operateType == 1:
            try:
                scriptStr = 'card'

                for i in range(3):
                    print('c[1~3]: 使用寶具')
                    print('r:      隨機選卡')
                    operateStr = input('動作>')
                    scriptStr += ' ' + operateStr

                scriptStr += '\n'

                Logger.trace('[SCRIPT] ' + scriptStr)

                return scriptStr

            except:
                print('非法輸入')
                return ''
        elif operateType == 2:
            pass
        else:
            print('錯誤: 未知的動作')
            return ''

    def CmdList(game: GameFGO):

        print(StringUtil.align('Key', 15) + StringUtil.align('好友從者', 20))
        for battleKey in game._battles:
            battle = game._battles[battleKey]
            print(StringUtil.align(battleKey, 15) + StringUtil.align(battle._friendInfo['name'], 20))


    def Run(game: GameFGO):

        print('Battle Editor')
        isRunning = True

        while isRunning:

            cmdLine = input('[Battle]>')

            if cmdLine == 'q' or cmdLine == 'quit':
                isRunning = False
                break

            cmdArgs = cmdLine.split(' ')

            cmd = cmdArgs[0]

            if cmd == 'add':
                BattleUI.CmdAdd(game)
            elif cmd == 'list':
                BattleUI.CmdList(game)
            else:
                print('Unknown command.')

            

