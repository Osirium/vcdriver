import atexit
import ssl
from pyVim import connect

import config


def get_connection():
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_NONE
    connection = connect.SmartConnect(
        host=config.HOST,
        port=config.PORT,
        user=config.USERNAME,
        pwd=config.PASSWORD,
        sslContext=context
    )
    atexit.register(connect.Disconnect, connection)
    print('Successfully connected to Vcenter with session ID {}'.format(
        connection.content.sessionManager.currentSession.key
    ))
    return connection
