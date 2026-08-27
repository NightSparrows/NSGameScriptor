
import unittest
from unittest import mock

from core.game.state import State
from core.game.gamedata import GameData
from core.game.statemanager import StateManager


class FakeState(State):
    """Test double: no device/screenshots, just records calls and returns
    configurable results, so the traversal logic in StateManager.goto() can
    be verified without a real emulator."""

    def __init__(self, name: str, parentName: str = None) -> None:
        super().__init__(name)
        self._parentName = parentName
        self.enterResult = True
        self.gobackResult = True
        self.detectResult = True
        self.enterCalls = 0
        self.gobackCalls = 0
        self.detectCalls = 0

    def getParentName(self):
        return self._parentName

    def enter(self):
        self.enterCalls += 1
        return self.enterResult

    def goback(self):
        self.gobackCalls += 1
        return self.gobackResult

    def detect(self):
        self.detectCalls += 1
        return self.detectResult


class StateManagerTests(unittest.TestCase):

    def setUp(self):
        # goto() sleeps for real seconds along a couple of its paths -
        # not needed for these tests to be correct, just to run fast.
        patcher = mock.patch('core.game.statemanager.time.sleep')
        self.addCleanup(patcher.stop)
        patcher.start()

        self.data = GameData()
        self.sm = StateManager(self.data)
        self.lobby = FakeState('Lobby')
        self.sm.init(self.lobby)

    def enteredNames(self):
        return [s.getName() for s in self.sm._enteredStates]

    def test_direct_child_from_init_state(self):
        activity = FakeState('Activity', 'Lobby')
        self.sm.addState(activity)

        self.assertTrue(self.sm.goto('Activity'))
        self.assertEqual(activity.enterCalls, 1)
        self.assertEqual(self.data.currentState, 'Activity')
        self.assertEqual(self.enteredNames(), ['Lobby', 'Activity'])

    def test_backtrack_then_descend_through_shared_ancestor(self):
        # FGO's actual shape: Activity is a direct child of Lobby; Daily is
        # a child of Gate, which is a child of Lobby. Activity -> Daily
        # must back out to Lobby, then descend Gate -> Daily. This is
        # exactly the case the old buggy loop got wrong.
        activity = FakeState('Activity', 'Lobby')
        gate = FakeState('Gate', 'Lobby')
        daily = FakeState('Daily', 'Gate')
        self.sm.addState(activity)
        self.sm.addState(gate)
        self.sm.addState(daily)

        self.assertTrue(self.sm.goto('Activity'))
        self.assertTrue(self.sm.goto('Daily'))

        self.assertEqual(activity.gobackCalls, 1)
        self.assertEqual(gate.enterCalls, 1)
        self.assertEqual(daily.enterCalls, 1)
        self.assertEqual(self.data.currentState, 'Daily')
        self.assertEqual(self.enteredNames(), ['Lobby', 'Gate', 'Daily'])

    def test_already_current_is_a_noop(self):
        self.assertTrue(self.sm.goto('Lobby'))
        self.assertEqual(self.lobby.enterCalls, 0)
        self.assertEqual(self.lobby.detectCalls, 0)

    def test_goto_ancestor_already_entered_confirms_via_detect(self):
        gate = FakeState('Gate', 'Lobby')
        daily = FakeState('Daily', 'Gate')
        self.sm.addState(gate)
        self.sm.addState(daily)

        self.assertTrue(self.sm.goto('Gate'))
        self.assertTrue(self.sm.goto('Daily'))

        result = self.sm.goto('Gate')

        self.assertTrue(result)
        self.assertEqual(daily.gobackCalls, 1)
        self.assertEqual(gate.enterCalls, 1)  # not re-entered, just confirmed
        self.assertGreaterEqual(gate.detectCalls, 1)
        self.assertEqual(self.data.currentState, 'Gate')
        self.assertEqual(self.enteredNames(), ['Lobby', 'Gate'])

    def test_unknown_state_name_fails_cleanly(self):
        self.assertFalse(self.sm.goto('DoesNotExist'))

    def test_detect_current_state_returns_first_match(self):
        activity = FakeState('Activity', 'Lobby')
        self.lobby.detectResult = False
        activity.detectResult = True
        self.sm.addState(activity)

        self.assertEqual(self.sm.detectCurrentState(), 'Activity')

    def test_detect_current_state_returns_none_when_nothing_matches(self):
        self.lobby.detectResult = False
        self.assertIsNone(self.sm.detectCurrentState())


if __name__ == '__main__':
    unittest.main()
