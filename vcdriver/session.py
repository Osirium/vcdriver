import atexit
import ssl

from pyVim.connect import SmartConnect, Disconnect

from vcdriver.config import configurable


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


@configurable([
    ('Vsphere Session', 'vcdriver_host'),
    ('Vsphere Session', 'vcdriver_port'),
    ('Vsphere Session', 'vcdriver_username'),
    ('Vsphere Session', 'vcdriver_password'),
    ('Vsphere Session', 'vcdriver_idle_timeout'),
])
def connection(**kwargs):
    """ Open the session if it does not exist and return the connection """
    global _session_id, _connection_obj
    if not _connection_obj:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        _connection_obj = SmartConnect(
            host=kwargs['vcdriver_host'],
            port=kwargs['vcdriver_port'],
            user=kwargs['vcdriver_username'],
            pwd=kwargs['vcdriver_password'],
            connectionPoolTimeout=int(kwargs['vcdriver_idle_timeout']),
            sslContext=context
        )
        _session_id = _connection_obj.content.sessionManager.currentSession.key
        print('Vcenter session opened with ID {}'.format(_session_id))
        atexit.register(close)
    return _connection_obj


def id():
    """
    Get the session id

    :return: The session id
    """
    global _session_id
    return _session_id
