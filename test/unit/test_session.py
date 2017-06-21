import mock

from vcdriver.session import connection, close, id


@mock.patch('vcdriver.session.SmartConnect')
@mock.patch('vcdriver.session.Disconnect')
def test_session(disconnect, connect):
    connection(
        vcdriver_username='something', vcdriver_password='something',
        vcdriver_host='something', vcdriver_port='something'
    )
    connection(
        vcdriver_username='something', vcdriver_password='something',
        vcdriver_host='something', vcdriver_port='something'
    )
    id()
    close()
    close()
    assert connect.call_count == 1
    assert disconnect.call_count == 1
