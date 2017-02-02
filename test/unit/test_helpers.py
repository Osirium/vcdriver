import mock
import unittest

from pyVmomi import vim
import winrm

from vcdriver.exceptions import (
    NoObjectFound,
    TooManyObjectsFound,
    TimeoutError
)
from vcdriver.helpers import (
    get_vcenter_object,
    wait_for_vcenter_task,
    wait_for_dhcp_server,
    wait_for_ssh_service,
    wait_for_winrm_service
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

    def test_wait_for_vcenter_task_timeout(self):
        task = mock.MagicMock()
        task.info.state = vim.TaskInfo.State.running
        with self.assertRaises(TimeoutError):
            wait_for_vcenter_task(task, 'description', timeout=1)

    def test_wait_for_dhcp_server_success(self):
        vm_object = mock.MagicMock()
        vm_object.summary.guest.ipAddress = '10.0.0.1'
        self.assertEqual(
            wait_for_dhcp_server(vm_object, timeout=1),
            '10.0.0.1'
        )

    def test_wait_for_dhcp_server_timeout(self):
        vm_object = mock.MagicMock()
        vm_object.summary.guest.ipAddress = None
        with self.assertRaises(TimeoutError):
            wait_for_dhcp_server(vm_object, timeout=1)

    @mock.patch('vcdriver.helpers.run')
    def test_wait_for_ssh_service_success(self, run):
        wait_for_ssh_service('', '', '', timeout=1)

    @mock.patch('vcdriver.helpers.run')
    def test_wait_for_ssh_service_timeout(self, run):
        run.side_effect = Exception
        with self.assertRaises(TimeoutError):
            wait_for_ssh_service('', '', '', timeout=1)

    @mock.patch.object(winrm.Session, 'run_cmd')
    def test_wait_for_winrm_service_success(self, run_cmd):
        wait_for_winrm_service('user', 'pass', 'ip', timeout=1)

    @mock.patch.object(winrm.Session, 'run_cmd')
    def test_wait_for_winrm_service_timeout(self, run_cmd):
        run_cmd.side_effect = Exception
        with self.assertRaises(TimeoutError):
            wait_for_winrm_service('user', 'pass', 'ip', timeout=1)
