
from ..logger import Logger

from .state import State
from .gamedata import GameData

class StateManager:

    # after open the game
    def __init__(self, data: GameData, initState: State) -> None:
        self._enteredStates = list(type=State)   # the stack of entered states
        self._states = dict(type=State)          # all of the state in this game
        self._data = data

        self._initState = initState
        self._states[initState.getName()] = initState

    def init(self):
        self._enteredStates.append(self._initState)
    
    def addState(self, state: State):
        Logger.info('adding state ' + state.getName())
        self._states[state.getName()] = state
    
    def goto(self, name: str):

        wishState = self._states[name]

        if wishState is None:
            Logger.error('Unknown state name:' + name + ', cannot goto.')
            return False

        Logger.info('Goto state ' + name + '...')

        parentList = list(type=State)
        
        parentStateName = wishState.getParentName()
        
        while (parentStateName != 'None'):
            parentState = self._states[parentStateName]
            parentList.append(parentState)

        dontgobackCount = 0
        for state in self._enteredStates:

            if state.getName() is name:
                gobackCount = len(self._enteredStates) - dontgobackCount - 1
                for i in range(gobackCount):
                    popState = self._enteredStates.pop()
                    popState.goback()
                return True

            foundParent = False
            parentNo = 0
            for parentState in parentList:
                if state.getName() is parentState.getName():
                    foundParent = True
                    break
                parentNo += 1
            
            if foundParent:
                gobackCount = len(self._enteredStates) - dontgobackCount - 1
                for i in range(parentNo + 1, len(parentList) - 1):
                    enterState = parentList[i]
                    if not enterState.enter():
                        Logger.error('Failed to goto the parnet state: ' + enterState.getName())
                        return False
                if not wishState.enter():
                    Logger.error('Failed to goto the wish state: ' + wishState.getName())
                    return False
                return True

            dontgobackCount += 1
        
        # 應該不會走到這裡
        return False




