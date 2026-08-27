
import subprocess
import unittest
from unittest import mock

from core.device.device import Device


class DeviceCheckOutputRetryTests(unittest.TestCase):
    """adb's connection to the device can transiently drop ("device
    offline") independent of whether the emulator/app is actually fine -
    observed live: GameFGO.restart()'s killApp() failed outright with no
    recovery anywhere in the call chain. checkOutput() now retries once
    via an adb server bounce + reconnect (Device.restart()) before
    giving up."""

    def _buildDevice(self):
        with mock.patch.object(Device, '_buildEmulator', lambda self, t, c: None):
            with mock.patch.object(Device, '_buildScreenCap', lambda self, t: 'FAKE_SCREENCAP'):
                with mock.patch.object(Device, 'connect', lambda self, d: None):
                    return Device('127.0.0.1:16480', Device.ScreenCapType.ADB, Device.EmulatorType.NONE)

    def test_retries_once_via_restart_on_failure(self):
        device = self._buildDevice()
        calls = {'n': 0}

        def flaky(cmd, shell=True):
            calls['n'] += 1
            if calls['n'] == 1:
                raise subprocess.CalledProcessError(1, cmd)
            return b'ok'

        restartCalls = {'n': 0}

        def fakeRestart(self):
            restartCalls['n'] += 1

        with mock.patch('subprocess.check_output', side_effect=flaky):
            with mock.patch.object(Device, 'restart', fakeRestart):
                result = device.checkOutput('shell am force-stop com.example')

        self.assertEqual(result, b'ok')
        self.assertEqual(calls['n'], 2)
        self.assertEqual(restartCalls['n'], 1)

    def test_raises_after_exhausting_retry(self):
        device = self._buildDevice()

        def alwaysFails(cmd, shell=True):
            raise subprocess.CalledProcessError(1, cmd)

        with mock.patch('subprocess.check_output', side_effect=alwaysFails):
            with mock.patch.object(Device, 'restart', lambda self: None):
                with self.assertRaises(subprocess.CalledProcessError):
                    device.checkOutput('shell am force-stop com.example')

    def test_connect_does_not_recurse_through_checkoutput_retry(self):
        # connect()/restart() pass retries=0 internally - a failing
        # connect() must not trigger checkOutput's retry-via-restart(),
        # which would call connect() again and recurse indefinitely.
        device = self._buildDevice()
        calls = {'n': 0}

        def alwaysFails(cmd, shell=True):
            calls['n'] += 1
            raise subprocess.CalledProcessError(1, cmd)

        with mock.patch('subprocess.check_output', side_effect=alwaysFails):
            with self.assertRaises(subprocess.CalledProcessError):
                device.connect('127.0.0.1:9999')

        self.assertEqual(calls['n'], 1)


if __name__ == '__main__':
    unittest.main()
