
import json
import unittest
from unittest import mock

from core.device.emulator.mumuEmulator import MumuEmulator


ALL_INSTANCES = json.dumps({
    '0': {'index': '0', 'name': 'Blank', 'is_process_started': False, 'player_state': ''},
    '3': {'index': '3', 'name': 'FGO', 'adb_port': 16480, 'is_process_started': False, 'player_state': ''},
}).encode('utf-8')

# stopped instances don't report adb_port at all - confirmed live. Index 3
# maps to port 16480 via MuMu's 16384+index*32 formula (also confirmed
# live), which findVmIndex() falls back to when no live port match exists.
STOPPED_INSTANCES = json.dumps({
    '0': {'index': '0', 'name': 'Blank'},
    '3': {'index': '3', 'name': 'FGO'},
}).encode('utf-8')


def infoFor(vmindex: str, ready: bool) -> bytes:
    # matches the real is_process_started + player_state=='start_finished'
    # combination MumuEmulator.isRunning() checks - is_android_started
    # isn't used, it was observed unreliable live.
    return json.dumps({
        'index': vmindex,
        'is_process_started': ready,
        'player_state': 'start_finished' if ready else '',
    }).encode('utf-8')


class MumuEmulatorTests(unittest.TestCase):

    def test_find_vm_index_matches_adb_port(self):
        with mock.patch('subprocess.check_output', return_value=ALL_INSTANCES) as m:
            self.assertEqual(MumuEmulator.findVmIndex(16480), 3)
            m.assert_called_once()

    def test_find_vm_index_returns_minus_one_when_not_found(self):
        with mock.patch('subprocess.check_output', return_value=ALL_INSTANCES):
            self.assertEqual(MumuEmulator.findVmIndex(9999), -1)

    def test_find_vm_index_falls_back_to_port_formula_for_stopped_instance(self):
        # this is the scenario that actually broke live: the emulator was
        # fully off, so its info had no adb_port to match against at all
        with mock.patch('subprocess.check_output', return_value=STOPPED_INSTANCES):
            self.assertEqual(MumuEmulator.findVmIndex(16480), 3)

    def test_find_vm_index_formula_fallback_requires_registered_index(self):
        # port 16416 fits the formula (index 1) but index 1 isn't actually
        # registered in this instance list - must not be trusted blindly
        with mock.patch('subprocess.check_output', return_value=STOPPED_INSTANCES):
            self.assertEqual(MumuEmulator.findVmIndex(16416), -1)

    def test_find_vm_index_returns_minus_one_for_non_formula_port(self):
        with mock.patch('subprocess.check_output', return_value=STOPPED_INSTANCES):
            self.assertEqual(MumuEmulator.findVmIndex(12345), -1)

    def _makeEmulator(self):
        with mock.patch('subprocess.check_output', return_value=ALL_INSTANCES):
            return MumuEmulator('127.0.0.1:16480')

    def test_construction_raises_when_port_unknown(self):
        with mock.patch('subprocess.check_output', return_value=ALL_INSTANCES):
            with self.assertRaises(RuntimeError):
                MumuEmulator('127.0.0.1:1')

    def test_is_running_reflects_info(self):
        emulator = self._makeEmulator()
        with mock.patch('subprocess.check_output', return_value=infoFor('3', True)):
            self.assertTrue(emulator.isRunning())
        with mock.patch('subprocess.check_output', return_value=infoFor('3', False)):
            self.assertFalse(emulator.isRunning())

    def test_wait_until_ready_short_circuits_if_already_running(self):
        emulator = self._makeEmulator()
        with mock.patch('subprocess.check_output', return_value=infoFor('3', True)) as m:
            self.assertTrue(emulator.waitUntilReady(timeout=5))
            # only the isRunning() check, no launch/poll calls
            m.assert_called_once()

    def test_wait_until_ready_launches_then_polls_until_started(self):
        emulator = self._makeEmulator()
        # sequence: isRunning()->False, launch()->ok, then poll: False, False, True
        responses = [
            infoFor('3', False),   # isRunning() check
            b'',                    # launch() control call (no json parsing needed)
            infoFor('3', False),   # poll 1
            infoFor('3', True),    # poll 2
        ]
        with mock.patch('subprocess.check_output', side_effect=responses):
            with mock.patch('time.sleep'):
                self.assertTrue(emulator.waitUntilReady(timeout=90))

    def test_wait_until_ready_times_out(self):
        emulator = self._makeEmulator()
        with mock.patch('subprocess.check_output', return_value=infoFor('3', False)):
            with mock.patch('time.sleep'):
                self.assertFalse(emulator.waitUntilReady(timeout=3))

    def test_custom_install_path_used_for_manager_exe(self):
        customPath = 'D:\\Games\\MuMuPlayer'
        with mock.patch('subprocess.check_output', return_value=ALL_INSTANCES) as m:
            emulator = MumuEmulator('127.0.0.1:16480', customPath)
            self.assertEqual(emulator._managerExe, customPath + '\\nx_main\\MumuManager')
            calledExe = m.call_args[0][0][0]
            self.assertEqual(calledExe, customPath + '\\nx_main\\MumuManager')

    def test_find_vm_index_missing_manager_exe_raises_runtime_error(self):
        with mock.patch('subprocess.check_output', side_effect=FileNotFoundError()):
            with self.assertRaises(RuntimeError):
                MumuEmulator.findVmIndex(16480, 'C:\\Nonexistent\\Path')

    def test_is_valid_install_path_checks_manager_exe(self):
        with mock.patch('os.path.isfile', return_value=True):
            self.assertTrue(MumuEmulator._isValidInstallPath('C:\\Foo'))
        with mock.patch('os.path.isfile', return_value=False):
            self.assertFalse(MumuEmulator._isValidInstallPath('C:\\Foo'))
        self.assertFalse(MumuEmulator._isValidInstallPath(''))

    def test_detect_install_path_prefers_registry_result(self):
        with mock.patch.object(MumuEmulator, '_installPathFromRegistry', return_value='C:\\FromRegistry'):
            with mock.patch.object(MumuEmulator, '_installPathFromCommonDrives', return_value='D:\\FromDrives') as drives:
                self.assertEqual(MumuEmulator.detectInstallPath(), 'C:\\FromRegistry')
                drives.assert_not_called()

    def test_detect_install_path_falls_back_to_common_drives(self):
        with mock.patch.object(MumuEmulator, '_installPathFromRegistry', return_value=''):
            with mock.patch.object(MumuEmulator, '_installPathFromCommonDrives', return_value='D:\\FromDrives'):
                self.assertEqual(MumuEmulator.detectInstallPath(), 'D:\\FromDrives')

    def test_detect_install_path_returns_empty_when_nothing_found(self):
        with mock.patch.object(MumuEmulator, '_installPathFromRegistry', return_value=''):
            with mock.patch.object(MumuEmulator, '_installPathFromCommonDrives', return_value=''):
                self.assertEqual(MumuEmulator.detectInstallPath(), '')

    def test_install_path_from_common_drives_returns_first_valid_match(self):
        def isfileSideEffect(path):
            return path == 'E:\\Program Files\\Netease\\MuMuPlayer\\nx_main\\MumuManager.exe'

        with mock.patch('os.path.isfile', side_effect=isfileSideEffect):
            self.assertEqual(
                MumuEmulator._installPathFromCommonDrives(),
                'E:\\Program Files\\Netease\\MuMuPlayer',
            )


if __name__ == '__main__':
    unittest.main()
