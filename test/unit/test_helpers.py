import mock
import pytest
from pyVmomi import vim, vmodl

from vcdriver.exceptions import (
    NoObjectFound,
    TooManyObjectsFound,
    TimeoutError,
    IpError,
)
from vcdriver.helpers import (
    get_all_vcenter_objects,
    get_vcenter_object_by_name,
    timeout_loop,
    validate_ip,
    validate_ipv4,
    validate_ipv6,
    wait_for_vcenter_task,
)


def test_all_vcenter_objects():
    view_mock = mock.MagicMock()
    view_mock.view = ['one', 2, None]
    content_mock = mock.MagicMock()
    content_mock.viewManager.CreateContainerView = mock.MagicMock(
        return_value=view_mock
    )
    connection_mock = mock.MagicMock()
    connection_mock.RetrieveContent = mock.MagicMock(
        return_value=content_mock
    )
    assert get_all_vcenter_objects(connection_mock, mock.MagicMock) == [
        'one', 2, None
    ]


def test_get_vcenter_object_by_name():
    apple = mock.MagicMock()
    orange_1 = mock.MagicMock()
    orange_2 = mock.MagicMock()
    banana = mock.MagicMock()
    mango = object()  # does not have name attr
    apple.name = 'apple'
    orange_1.name = 'orange'
    orange_2.name = 'orange'
    type(banana).name = mock.PropertyMock(
        side_effect=vmodl.fault.ManagedObjectNotFound
    )
    view_mock = mock.MagicMock()
    view_mock.view = [apple, orange_1, orange_2, banana, mango]
    content_mock = mock.MagicMock()
    content_mock.viewManager.CreateContainerView = mock.MagicMock(
        return_value=view_mock
    )
    connection_mock = mock.MagicMock()
    connection_mock.RetrieveContent = mock.MagicMock(
        return_value=content_mock
    )
    assert get_vcenter_object_by_name(
        connection_mock, mock.MagicMock, 'apple'
    ) == apple
    with pytest.raises(NoObjectFound):
        get_vcenter_object_by_name(
            connection_mock, mock.MagicMock, 'mango'
        )
    with pytest.raises(NoObjectFound):
        get_vcenter_object_by_name(
            connection_mock, mock.MagicMock, 'grapes'
        )
    with pytest.raises(NoObjectFound):
        get_vcenter_object_by_name(
            connection_mock, mock.MagicMock, 'banana'
        )
    with pytest.raises(TooManyObjectsFound):
        get_vcenter_object_by_name(
            connection_mock, mock.MagicMock, 'orange'
        )

    with pytest.raises(TooManyObjectsFound):
        get_vcenter_object_by_name(
            connection_mock, mock.MagicMock, 'orange'
        )


def test_timeout_loop_success():
    timeout_loop(1, '', 1, False, lambda: True)


def test_timeout_loop_fail():
    with pytest.raises(TimeoutError):
        timeout_loop(1, '', 1, False, lambda: False)


def test_validate_ip_success_version_4():
    assert validate_ip('127.0.0.1') == {
        'ip': '127.0.0.1', 'version': 4
    }


def test_validate_ip_success_version_6():
    assert validate_ip('fe80::250:56ff:febf:1a0a') == {
        'ip': 'fe80::250:56ff:febf:1a0a', 'version': 6
    }


def test_validate_ip_fail():
    with pytest.raises(IpError):
        validate_ip('wrong')


def test_validate_ipv4_success():
    assert validate_ipv4('127.0.0.1'), True


def test_validate_ipv4_fail():
    assert not validate_ipv4('fe80::250:56ff:febf:1a0a')


@mock.patch('vcdriver.helpers.socket.inet_pton')
def test_validate_ipv4_no_inet_pton_success(inet_pton):
    inet_pton.side_effect = AttributeError
    assert validate_ipv4('127.0.0.1')


@mock.patch('vcdriver.helpers.socket.inet_pton')
def test_validate_ipv4_no_inet_pton_fail(inet_pton):
    inet_pton.side_effect = AttributeError
    assert not validate_ipv4('fe80::250:56ff:febf:1a0a')


def test_validate_ipv6_success():
    assert validate_ipv6('fe80::250:56ff:febf:1a0a')


def test_validate_ipv6_fail():
    assert not validate_ipv6('127.0.0.1')


def test_wait_for_vcenter_task_wait_for_success():
    task = mock.Mock(vim.Task)

    class TaskInfoTimeline:
        def __init__(self, states, result):
            self.result = result
            self._state_iter = iter(states)

        @property
        def state(self):
            return next(self._state_iter)
    task.info = TaskInfoTimeline(
        result='hello', states=(
            vim.TaskInfo.State.queued, vim.TaskInfo.State.running,
            # Need success twice (ATM) since it is looked up again after poll
            # loop
            vim.TaskInfo.State.success, vim.TaskInfo.State.success))
    assert wait_for_vcenter_task(
        task, 'description', timeout=2, _poll_interval=0) == 'hello'
    with pytest.raises(StopIteration):
        task.info.state


def test_wait_for_vcenter_task_fail():
    task = mock.MagicMock()
    task.info.state = vim.TaskInfo.State.error
    task.info.error = Exception
    with pytest.raises(Exception):
        wait_for_vcenter_task(task, 'description', timeout=1)


def test_wait_for_vcenter_task_fail_no_exception():
    task = mock.MagicMock()
    task.info.state = vim.TaskInfo.State.error
    task.info.error = None
    wait_for_vcenter_task(task, 'description', timeout=1)


def test_wait_for_vcenter_task_timeout():
    task = mock.MagicMock()
    task.info.state = vim.TaskInfo.State.running
    with pytest.raises(TimeoutError):
        wait_for_vcenter_task(task, 'description', timeout=1)
