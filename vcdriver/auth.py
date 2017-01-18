import ssl

from pyVim import connect

from vcdriver.config import HOST, PORT, USERNAME, PASSWORD


class session_context(object):
    def __init__(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE
        self.connection = connect.SmartConnect(
            host=HOST,
            port=PORT,
            user=USERNAME,
            pwd=PASSWORD,
            sslContext=context
        )
        self.id = self.connection.content.sessionManager.currentSession.key
        print('Vcenter session opened with ID {}'.format(self.id))

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        connect.Disconnect(self.connection)
        print('Vcenter session with ID {} closed'.format(self.id))
