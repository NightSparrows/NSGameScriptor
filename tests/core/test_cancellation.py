
import unittest
from unittest import mock

from core.util.cancellation import CancellationToken, CancelledException


class CancellationTokenTests(unittest.TestCase):

    def test_sleep_completes_normally_when_not_cancelled(self):
        token = CancellationToken()
        with mock.patch('time.sleep') as sleepMock:
            token.sleep(0.2, interval=0.05)
        # 0.2s in 0.05s steps is ~4 real time.sleep calls (float drift can
        # make it 5) and no exception either way
        self.assertIn(sleepMock.call_count, (4, 5))

    def test_check_point_raises_after_cancel(self):
        token = CancellationToken()
        token.cancel()
        with self.assertRaises(CancelledException):
            token.checkPoint()

    def test_sleep_raises_immediately_if_already_cancelled(self):
        token = CancellationToken()
        token.cancel()
        with mock.patch('time.sleep') as sleepMock:
            with self.assertRaises(CancelledException):
                token.sleep(5)
        sleepMock.assert_not_called()

    def test_sleep_raises_mid_sleep_once_cancelled(self):
        token = CancellationToken()
        calls = []

        def fakeSleep(seconds):
            calls.append(seconds)
            if len(calls) == 2:
                token.cancel()

        with mock.patch('time.sleep', side_effect=fakeSleep):
            with self.assertRaises(CancelledException):
                token.sleep(1.0, interval=0.1)

        # cancelled after the 2nd chunk - shouldn't have slept the full
        # 10 chunks a 1.0s/0.1s sleep would otherwise take
        self.assertEqual(len(calls), 2)

    def test_reset_clears_cancellation(self):
        token = CancellationToken()
        token.cancel()
        self.assertTrue(token.isCancelled())
        token.reset()
        self.assertFalse(token.isCancelled())
        token.checkPoint()  # should not raise


if __name__ == '__main__':
    unittest.main()
