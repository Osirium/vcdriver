import mock
import unittest

from vcdriver.session import connection, close, id


class TestAuth(unittest.TestCase):
    @mock.patch('vcdriver.session.SmartConnect')
    @mock.patch('vcdriver.session.Disconnect')
    def test_session(self, disconnect, connect):
        connection(
            VCDRIVER_USERNAME='something', VCDRIVER_PASSWORD='something',
            VCDRIVER_HOST='something', VCDRIVER_PORT='something'
        )
        connection(
            VCDRIVER_USERNAME='something', VCDRIVER_PASSWORD='something',
            VCDRIVER_HOST='something', VCDRIVER_PORT='something'
        )
        id()
        close()
        close()
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(disconnect.call_count, 1)
