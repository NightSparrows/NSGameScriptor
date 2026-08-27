
import unittest
from unittest import mock

from core.device.device import Device
from core.device.emulator.emulator import Emulator


class FakeEmulator(Emulator):
    """Always reports running/launchable - only shutdown()/waitUntilReady()
    call counts matter for these tests."""

    def __init__(self) -> None:
        self.shutdownCalls = 0
        self.waitCalls = 0

    def isRunning(self) -> bool:
        return True

    def launch(self) -> bool:
        return True

    def shutdown(self) -> bool:
        self.shutdownCalls += 1
        return True

    def waitUntilReady(self, timeout: float = 90) -> bool:
        self.waitCalls += 1
        return True


class NotRunningEmulator(FakeEmulator):
    """isRunning() False - simulates the emulator not being up yet at
    Device construction time."""

    def isRunning(self) -> bool:
        return False


class DeviceEmulatorBootstrapTests(unittest.TestCase):
    """Device._connectAndBuildScreenCap(): an emulator that reports itself
    running but whose screencap backend still fails to connect (adb flaky,
    NemuIPC not accepting connections yet, ...) should trigger one
    restart+retry rather than failing Device construction outright."""

    def _buildDevice(self, buildScreenCap, emulator):
        with mock.patch.object(Device, '_buildScreenCap', buildScreenCap):
            with mock.patch.object(Device, '_buildEmulator', lambda self, t, c: emulator):
                with mock.patch.object(Device, 'connect', lambda self, d: None):
                    with mock.patch('time.sleep'):
                        return Device('127.0.0.1:16480', Device.ScreenCapType.NEMUIPC, Device.EmulatorType.MUMU)

    def test_retries_once_after_transient_failure(self):
        emulator = FakeEmulator()
        calls = {'n': 0}

        def flaky(self, screencapType):
            calls['n'] += 1
            if calls['n'] == 1:
                raise RuntimeError('simulated: not reachable yet')
            return 'FAKE_SCREENCAP'

        device = self._buildDevice(flaky, emulator)

        self.assertEqual(calls['n'], 2)
        self.assertEqual(emulator.shutdownCalls, 1)
        self.assertEqual(emulator.waitCalls, 1)  # only the retry's explicit relaunch wait
        self.assertEqual(device._screenCap, 'FAKE_SCREENCAP')

    def test_defers_connection_when_emulator_not_running_at_construction(self):
        # this is the scenario the user hit: opening the GUI/CLI with the
        # emulator not open at all shouldn't require it to be running -
        # Device should construct fine and defer connecting until
        # something actually calls ensureEmulatorRunning() (task
        # execution already does, via GameFGO.ensureReady()).
        emulator = NotRunningEmulator()
        calls = {'n': 0}

        def builder(self, screencapType):
            calls['n'] += 1
            return 'FAKE_SCREENCAP'

        device = self._buildDevice(builder, emulator)

        self.assertEqual(calls['n'], 0, 'should not have connected at construction time')
        self.assertIsNone(device._screenCap)

        with mock.patch.object(Device, '_buildScreenCap', builder):
            with mock.patch.object(Device, 'connect', lambda self, d: None):
                result = device.ensureEmulatorRunning()

        self.assertTrue(result)
        self.assertEqual(calls['n'], 1)
        self.assertEqual(device._screenCap, 'FAKE_SCREENCAP')

    def test_construction_never_raises_after_exhausting_retry(self):
        # a bad setting (wrong device/emulator path/...) must never crash
        # Device()/the GUI's __init__ outright - it should log which
        # setting to check and defer, so the app still opens and the real
        # error surfaces later at execution time (ensureEmulatorRunning()).
        emulator = FakeEmulator()

        def alwaysFails(self, screencapType):
            raise RuntimeError('simulated: never reachable')

        device = self._buildDevice(alwaysFails, emulator)

        self.assertEqual(emulator.shutdownCalls, 1)
        self.assertIsNone(device._screenCap)

    def test_construction_never_raises_when_no_emulator_configured(self):
        calls = {'n': 0}

        def alwaysFails(self, screencapType):
            calls['n'] += 1
            raise RuntimeError('simulated failure')

        with mock.patch.object(Device, '_buildScreenCap', alwaysFails):
            with mock.patch.object(Device, '_buildEmulator', lambda self, t, c: None):
                with mock.patch.object(Device, 'connect', lambda self, d: None):
                    device = Device('127.0.0.1:16480', Device.ScreenCapType.ADB, Device.EmulatorType.NONE)

        self.assertEqual(calls['n'], 1)
        self.assertIsNone(device._screenCap)

    def test_construction_survives_missing_manager_exe_with_no_emulator_lifecycle(self):
        # reproduces the live crash: emulator lifecycle isn't configured
        # (EmulatorType.NONE) but the screencap backend (NEMUIPC) still
        # needs MumuManager to resolve the vmindex, and the configured
        # install path doesn't exist on this machine - FileNotFoundError
        # from the real _buildScreenCap, not a mocked one.
        with mock.patch.object(Device, '_buildEmulator', lambda self, t, c: None):
            with mock.patch.object(Device, 'connect', lambda self, d: None):
                with mock.patch('subprocess.check_output', side_effect=FileNotFoundError()):
                    device = Device('127.0.0.1:16480', Device.ScreenCapType.NEMUIPC, Device.EmulatorType.NONE, 'C:\\Nonexistent\\Path')

        self.assertIsNone(device._screenCap)


if __name__ == '__main__':
    unittest.main()
