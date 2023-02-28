
from game.fgo.gamefgo import GameFGO

from core.util.stringutil import StringUtil

class ListUtil:

    def ListBattleInfo(game: GameFGO):

        print(StringUtil.align('Key', 20))

        for battleKey in game._battles:
            battle = game._battles[battleKey]
            print(StringUtil.align(battleKey, 20))
        
        



