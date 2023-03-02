

from core.util.stringutil import StringUtil

from game.fgo.gamefgo import GameFGO

class BattleUI:

    def CmdAdd(game: GameFGO):

        # {"name": "ArtParty", "partyNumber": 10, "classChoosing": 5, "friendServantName": "altriaCaster", "skill": [true, true, true], "script": "skill 2 1\nskill 2 2\nskill 2 3\nskill 1 1\nskill 1 2 2\nskill 1 3 2\nskill 3 1\nskill 3 2 2\nskill 3 3 2\ncard c2 r r\ncard c2 r r\ncard c2 r r\ncard r r r\n"}

        print('不要有空格')
        battleName = input('Battle名稱(英文)>')

        while True:

            cmdLine = input('>')


        raise NotImplementedError()

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

            

