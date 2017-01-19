import mock
import unittest

from vcdriver.auth import Session


class TestAuth(unittest.TestCase):
    @mock.patch('vcdriver.auth.connect.SmartConnect')
    @mock.patch('vcdriver.auth.connect.Disconnect')
    def test_session(self, disconnect, connect):
        Session().close()
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(disconnect.call_count, 1)
