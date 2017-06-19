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
])
def connection(
        vcdriver_host, vcdriver_port, vcdriver_username, vcdriver_password
):
    """
    Open the session if it does not exist and return the connection
    :param vcdriver_host: Vsphere host
    :param vcdriver_port: Vsphere port
    :param vcdriver_username: Vsphere username
    :param vcdriver_password: Vsphere password

    :return
    """
    global _session_id, _connection_obj
    if not _connection_obj:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        _connection_obj = SmartConnect(
            host=vcdriver_host,
            port=vcdriver_port,
            user=vcdriver_username,
            pwd=vcdriver_password,
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
