
import time

from ..logger import Logger

from .state import State
from .gamedata import GameData

class StateManager:

    # after open the game
    def __init__(self, data: GameData) -> None:
        self._enteredStates = list()   # the stack of entered states, root first
        self._states = dict()          # all of the state in this game
        self._data = data


    def init(self, initState: State):
        self._states.clear()
        self._enteredStates.clear()
        self._initState = initState
        self._states[initState.getName()] = initState
        self._enteredStates.append(self._initState)
        self._data.currentState = self._initState.getName()

    def addState(self, state: State):
        Logger.info('adding state ' + state.getName())
        self._states[state.getName()] = state

    # loop every registered state's detect() and report the first match.
    # unlike goto(), this doesn't trust/use the navigation history at all -
    # it's a way to independently ask "what does the screen actually look
    # like right now".
    def detectCurrentState(self):
        for state in self._states.values():
            if state.detect():
                return state.getName()
        return None

    def goto(self, name: str) -> bool:

        if name == self._data.currentState:
            return True

        wishState = self._states.get(name)

        if wishState is None:
            Logger.error('Unknown state name:' + name + ', cannot goto.')
            return False

        Logger.info('Goto state ' + name + '...')

        # ancestors of the target, immediate parent first, root last
        ancestors = list()
        parentStateName = wishState.getParentName()
        while parentStateName is not None:
            Logger.trace('Found parent ' + parentStateName)
            parentState = self._states[parentStateName]
            ancestors.append(parentState)
            parentStateName = parentState.getParentName()

        targetChainNames = {name}
        targetChainNames.update(s.getName() for s in ancestors)

        # walk the actual navigation stack from the top down, looking for
        # the deepest entry that is either the target itself or one of its
        # ancestors - that's the point we can navigate from.
        pivotIndex = None
        for i in range(len(self._enteredStates) - 1, -1, -1):
            if self._enteredStates[i].getName() in targetChainNames:
                pivotIndex = i
                break

        if pivotIndex is None:
            # shouldn't happen: the init state has no parent and is always
            # entered at index 0, so it's always in every target's ancestry
            Logger.error('No path found to state: ' + name)
            return False

        # back out of everything above the pivot
        while len(self._enteredStates) - 1 > pivotIndex:
            popState = self._enteredStates.pop()
            Logger.info('Poped state ' + popState.getName())
            if not popState.goback():
                Logger.error('Failed to go back from state: ' + popState.getName())
                return False
            self._data.currentState = self._enteredStates[-1].getName()

        pivot = self._enteredStates[-1]

        if pivot.getName() == name:
            # already entered before - confirm the screen actually settled
            # back into it rather than trusting the navigation history blindly
            timer = 0
            while timer <= 10:
                if pivot.detect():
                    Logger.trace('Backing to ' + name + ' state')
                    time.sleep(1)
                    return True
                time.sleep(1)
                timer += 1
            return False

        # descend from just below the pivot down to the target. pivot is
        # guaranteed to be name itself (handled above) or one of ancestors
        # (guaranteed by how pivotIndex was found), so only the ancestors
        # *nearer to the target* than the pivot still need entering -
        # anything at or beyond the pivot's position is already satisfied.
        pivotAncestorIdx = next(i for i, s in enumerate(ancestors) if s.getName() == pivot.getName())
        toEnter = list(reversed(ancestors[:pivotAncestorIdx]))
        toEnter.append(wishState)

        for state in toEnter:
            if not state.enter():
                Logger.error('Failed to enter state: ' + state.getName())
                return False
            self._enteredStates.append(state)
            self._data.currentState = state.getName()
            Logger.info('Entered state: ' + state.getName())

        return True
