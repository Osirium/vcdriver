import atexit
import ssl
from pyVim import connect

import config


class Session(object):
    def __init__(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE
        self.connection = connect.SmartConnect(
            host=config.HOST,
            port=config.PORT,
            user=config.USERNAME,
            pwd=config.PASSWORD,
            sslContext=context
        )
        self.id = self.connection.content.sessionManager.currentSession.key
        print('Connected to Vcenter with session ID {}'.format(self.id))
        atexit.register(self.close)

    def close(self):
        print('Closing session ID {}'.format(self.id))
        connect.Disconnect(self.connection)
