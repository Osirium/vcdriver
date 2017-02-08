import mock
import unittest

from pyVmomi import vim

from vcdriver.exceptions import (
    NoObjectFound,
    TooManyObjectsFound,
    TimeoutError,
    DhcpError,
    Ipv4Error
)
from vcdriver.helpers import (
    get_vcenter_object,
    timeout_loop,
    validate_ipv4,
    wait_for_vcenter_task,
)


class TestHelpers(unittest.TestCase):
    def test_get_object(self):
        apple = mock.MagicMock()
        orange_1 = mock.MagicMock()
        orange_2 = mock.MagicMock()
        apple.name = 'apple'
        orange_1.name = 'orange'
        orange_2.name = 'orange'
        view_mock = mock.MagicMock()
        view_mock.view = [apple, orange_1, orange_2]
        content_mock = mock.MagicMock()
        content_mock.viewManager.CreateContainerView = mock.MagicMock(
            return_value=view_mock
        )
        connection_mock = mock.MagicMock()
        connection_mock.RetrieveContent = mock.MagicMock(
            return_value=content_mock
        )
        self.assertEqual(
            get_vcenter_object(connection_mock, mock.MagicMock, 'apple'),
            apple
        )
        with self.assertRaises(NoObjectFound):
            get_vcenter_object(connection_mock, mock.MagicMock, 'grapes'),
        with self.assertRaises(TooManyObjectsFound):
            get_vcenter_object(connection_mock, mock.MagicMock, 'orange')

    def test_timeout_loop_success(self):
        timeout_loop(1, '', lambda: True)

    def test_timeout_loop_fail(self):
        with self.assertRaises(TimeoutError):
            timeout_loop(1, '', lambda: False)

    def test_validate_ipv4_success(self):
        self.assertEqual(validate_ipv4('127.0.0.1'), '127.0.0.1')

    @mock.patch('vcdriver.helpers.socket.inet_pton')
    def test_validate_ipv4_success_no_inet_pton(self, inet_pton):
        inet_pton.side_effect = AttributeError
        self.assertEqual(validate_ipv4('127.0.0.1'), '127.0.0.1')

    def test_validate_ipv4_fail(self):
        with self.assertRaises(Ipv4Error):
            validate_ipv4('fe80::250:56ff:febf:1a0a')

    @mock.patch('vcdriver.helpers.socket.inet_pton')
    def test_validate_ipv4_fail_no_inet_pton(self, inet_pton):
        inet_pton.side_effect = AttributeError
        with self.assertRaises(Ipv4Error):
            validate_ipv4('fe80::250:56ff:febf:1a0a')

    def test_validate_ipv4_fail_link_local_address(self):
        with self.assertRaises(DhcpError):
            validate_ipv4('169.254.1.1')

    def test_wait_for_vcenter_task_success(self):
        task = mock.MagicMock()
        task.info.state = vim.TaskInfo.State.success
        task.info.result = 'hello'
        self.assertEqual(
            wait_for_vcenter_task(task, 'description', timeout=1),
            'hello'
        )

    def test_wait_for_vcenter_task_fail(self):
        task = mock.MagicMock()
        task.info.state = 'Error'
        task.info.error = Exception
        with self.assertRaises(Exception):
            wait_for_vcenter_task(task, 'description', timeout=1)

    def test_wait_for_vcenter_task_fail_no_exception(self):
        task = mock.MagicMock()
        task.info.state = 'Error'
        task.info.error = None
        wait_for_vcenter_task(task, 'description', timeout=1)

    def test_wait_for_vcenter_task_timeout(self):
        task = mock.MagicMock()
        task.info.state = vim.TaskInfo.State.running
        with self.assertRaises(TimeoutError):
            wait_for_vcenter_task(task, 'description', timeout=1)
