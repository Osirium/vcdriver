import atexit
import ssl

from pyVim.connect import SmartConnect, Disconnect

from vcdriver.config import required


_session_id = None
_connection_obj = None


def close():
    """ Close the session if exists """
    global _session_id, _connection_obj
    if _connection_obj:
        Disconnect(_connection_obj)
        print('Vcenter session with ID {} closed'.format(_session_id))
        _session_id = None
        _connection_obj = None


@required([
    ('Vsphere Session', 'VCDRIVER_HOST'),
    ('Vsphere Session', 'VCDRIVER_PORT'),
    ('Vsphere Session', 'VCDRIVER_USERNAME'),
    ('Vsphere Session', 'VCDRIVER_PASSWORD'),
])
def connection(**kwargs):
    """ Open the session if it does not exist and return the connection """
    global _session_id, _connection_obj
    if not _connection_obj:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        _connection_obj = SmartConnect(
            host=kwargs['VCDRIVER_HOST'],
            port=kwargs['VCDRIVER_PORT'],
            user=kwargs['VCDRIVER_USERNAME'],
            pwd=kwargs['VCDRIVER_PASSWORD'],
            sslContext=context
        )
        _session_id = _connection_obj.content.sessionManager.currentSession.key
        print('Vcenter session opened with ID {}'.format(_session_id))
        atexit.register(close)
    return _connection_obj


def id():
    """ Return the session id """
    global _session_id
    return _session_id
