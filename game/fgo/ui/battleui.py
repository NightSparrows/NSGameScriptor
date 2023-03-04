

from core.util.stringutil import StringUtil

from game.fgo.gamefgo import GameFGO

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
        
        print('職階選擇(1~10)(預設5)')
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

        while True:

            cmdLine = input('>')

            if cmdLine == 'q' or cmdLine == 'quit':
                break

            cmdArgs = cmdLine.split(' ')

            

        
        return

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
                pass
            elif cmd == 'list':
                BattleUI.CmdList(game)
            else:
                print('Unknown command.')

            

