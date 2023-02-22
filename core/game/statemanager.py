
import time

from ..logger import Logger

from .state import State
from .gamedata import GameData

class StateManager:

    # after open the game
    def __init__(self, data: GameData) -> None:
        self._enteredStates = list()   # the stack of entered states
        self._states = dict()          # all of the state in this game
        self._data = data


    def init(self, initState: State):
        self._initState = initState
        self._states[initState.getName()] = initState
        self._enteredStates.append(self._initState)
        self._data.currentState = self._initState.getName()
    
    def addState(self, state: State):
        Logger.info('adding state ' + state.getName())
        self._states[state.getName()] = state
    
    def goto(self, name: str):

        if name is self._data.currentState:
            return True

        wishState = self._states[name]

        if wishState is None:
            Logger.error('Unknown state name:' + name + ', cannot goto.')
            return False

        Logger.info('Goto state ' + name + '...')

        parentList = list()
        
        parentStateName = wishState.getParentName()
        
        while (parentStateName != 'None'):
            Logger.trace('Found parent ' + parentStateName)
            parentState = self._states[parentStateName]
            parentList.append(parentState)
            parentStateName = parentState.getParentName()

        dontgobackCount = 0
        for state in self._enteredStates:

            if state.getName() is name:
                gobackCount = len(self._enteredStates) - dontgobackCount - 1
                for i in range(gobackCount):
                    popState = self._enteredStates.pop()
                    if popState.goback():
                        self._data.currentState = self._enteredStates[len(self._enteredStates) - 1].getName()
                
                # wait for stable
                timer = 0
                while timer <= 10:
                    if state.detect():
                        Logger.trace('Backing to ' + name + ' state')
                        time.sleep(1)
                        return True
                    time.sleep(1)
                    timer += 1
                return False

            foundParent = False
            parentNo = 0
            for parentState in parentList:
                if state.getName() is parentState.getName():
                    foundParent = True
                    break
                parentNo += 1
            
            if foundParent:
                gobackCount = len(self._enteredStates) - dontgobackCount - 1
                for i in range(parentNo - 1, -1, -1):
                    enterState = parentList[i]
                    print('Entering parent state: ' + enterState.getName())
                    if not enterState.enter():
                        Logger.error('Failed to goto the parnet state: ' + enterState.getName())
                        return False
                    self._enteredStates.append(enterState)
                    self._data.currentState = enterState.getName()
                if not wishState.enter():
                    Logger.error('Failed to goto the wish state: ' + wishState.getName())
                    return False
                self._enteredStates.append(wishState)
                self._data.currentState = wishState.getName()
                return True

            dontgobackCount += 1
        
        # 應該不會走到這裡
        return False




