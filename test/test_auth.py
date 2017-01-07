import mock
import unittest
import uuid

from vcdriver import auth


class ConnectionMock(object):
    def __init__(self):
        self.__setattr__('content', mock.MagicMock())
        setattr(self.content, 'sessionManager', mock.MagicMock())
        setattr(
            self.content.sessionManager,
            'currentSession',
            mock.MagicMock()
        )
        setattr(
            self.content.sessionManager.currentSession,
            'key',
            str(uuid.uuid4())
        )


class TestAuth(unittest.TestCase):
    @mock.patch('vcdriver.auth.connect.SmartConnect')
    @mock.patch('vcdriver.auth.connect.Disconnect')
    @mock.patch('vcdriver.auth.atexit.register')
    def test_session(self, register, disconnect, connect):
        auth.Session().close()
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(disconnect.call_count, 1)
