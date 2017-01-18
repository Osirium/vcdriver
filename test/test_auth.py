import mock
import unittest

from vcdriver.auth import session_context


class TestAuth(unittest.TestCase):
    @mock.patch('vcdriver.auth.connect.SmartConnect')
    @mock.patch('vcdriver.auth.connect.Disconnect')
    def test_session(self, disconnect, connect):
        with session_context():
            pass
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(disconnect.call_count, 1)
