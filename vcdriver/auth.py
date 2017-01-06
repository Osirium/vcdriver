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
        print('\nVcenter session opened with ID {}'.format(self.id))
        atexit.register(self.close)

    def close(self):
        connect.Disconnect(self.connection)
        print('Vcenter session with ID {} closed'.format(self.id))

