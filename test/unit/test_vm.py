import mock
import unittest

from pyVmomi import vim
import winrm

from vcdriver.exceptions import SshError, DownloadError, UploadError
from vcdriver.vm import VirtualMachine, virtual_machines


class TestVm(unittest.TestCase):
    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get_vcenter_object')
    @mock.patch('vcdriver.vm.vim.vm.CloneSpec')
    @mock.patch('vcdriver.vm.vim.vm.RelocateSpec')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    @mock.patch('vcdriver.vm.wait_for_dhcp_server')
    def test_virtual_machine_create(
            self,
            wait_for_dhcp_server,
            wait_for_vcenter_task,
            relocate_spec,
            clone_spec,
            get_vcenter_object,
            session
    ):
        vm = VirtualMachine()
        vm.create()
        vm.create()
        self.assertIsNotNone(vm.__getattribute__('_vm_object'))
        self.assertEqual(wait_for_vcenter_task.call_count, 1)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_virtual_machine_destroy_machine_on(
            self,
            wait_for_vcenter_task,
            session
    ):
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        vm.__setattr__('_vm_object', vm_object_mock)
        vm.destroy()
        vm.destroy()
        self.assertIsNone(vm.__getattribute__('_vm_object'))
        self.assertEqual(wait_for_vcenter_task.call_count, 2)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_virtual_machine_destroy_machine_off(
            self,
            wait_for_vcenter_task,
            session
    ):
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        vm_object_mock.PowerOffVM_Task = mock.MagicMock(
            side_effect=vim.fault.InvalidPowerState
        )
        vm.__setattr__('_vm_object', vm_object_mock)
        vm.destroy()
        vm.destroy()
        self.assertIsNone(vm.__getattribute__('_vm_object'))
        self.assertEqual(wait_for_vcenter_task.call_count, 1)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get_vcenter_object')
    def test_virtual_machine_find(self, get_vcenter_object, session):
        vm = VirtualMachine()
        vm.find()
        vm.find()
        self.assertIsNotNone(vm.__getattribute__('_vm_object'))
        self.assertEqual(get_vcenter_object.call_count, 1)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.wait_for_dhcp_server')
    def test_virtual_machine_ip(self, wait_for_dhcp_server, session):
        vm = VirtualMachine()
        wait_for_dhcp_server.return_value = '10.0.0.1'
        self.assertEqual(vm.ip(), None)
        vm.__setattr__('_vm_object', 'Something')
        self.assertEqual(vm.ip(), '10.0.0.1')
        self.assertEqual(vm.ip(), '10.0.0.1')
        self.assertEqual(vm.ip(use_cache=False), '10.0.0.1')
        self.assertEqual(wait_for_dhcp_server.call_count, 2)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.sudo')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_ssh_success(self, run, sudo, session):
        vm = VirtualMachine()
        result_mock = mock.MagicMock()
        result_mock.return_code = 3
        result_mock.failed = False
        run.return_value = result_mock
        sudo.return_value = result_mock
        self.assertEqual(
            vm.ssh('whatever', use_sudo=False).return_code, 3
        )
        self.assertEqual(
            vm.ssh('whatever', use_sudo=True).return_code, 3
        )

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_ssh_failed(self, run, session):
        vm = VirtualMachine()
        with self.assertRaises(SshError):
            vm.ssh('whatever', use_sudo=False)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch.object(winrm.Session, 'run_cmd')
    def test_virtual_machine_winrm_cmd(self, winrm_session, session):
        vm = VirtualMachine(username='user', password='pass')
        vm.__setattr__('ip', lambda: '127.0.0.1')
        vm.winrm_cmd('cmd', 1, 2, 3)
        winrm_session.assert_called_once_with('cmd', 1, 2, 3)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch.object(winrm.Session, 'run_ps')
    def test_virtual_machine_winrm_ps(self, winrm_session, session):
        vm = VirtualMachine(username='user', password='pass')
        vm.__setattr__('ip', lambda: '127.0.0.1')
        vm.winrm_ps('script')
        winrm_session.assert_called_once_with('script')

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.put')
    def test_virtual_machine_upload_success(self, put, session):
        vm = VirtualMachine()
        result_mock = mock.MagicMock()
        result_mock.failed = False
        put.return_value = result_mock
        self.assertEqual(vm.upload('from', 'to'), result_mock)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.put')
    def test_virtual_machine_upload_fail(self, put, session):
        vm = VirtualMachine()
        with self.assertRaises(UploadError):
            vm.upload('from', 'to')

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.put')
    def test_virtual_machine_upload_fail_with_value_error(self, put, session):
        vm = VirtualMachine()
        put.side_effect = ValueError
        with self.assertRaises(UploadError):
            vm.upload('from', 'to')

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get')
    def test_virtual_machine_download_success(self, get, session):
        vm = VirtualMachine()
        result_mock = mock.MagicMock()
        result_mock.failed = False
        get.return_value = result_mock
        self.assertEqual(vm.download('from', 'to'), result_mock)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get')
    def test_virtual_machine_download_fail(self, get, session):
        vm = VirtualMachine()
        with self.assertRaises(DownloadError):
            vm.download('from', 'to')

    @mock.patch('vcdriver.vm.Session')
    @mock.patch.object(VirtualMachine, 'create')
    @mock.patch.object(VirtualMachine, 'destroy')
    def test_virtual_machines_success(self, destroy, create, session):
        vm = VirtualMachine()
        with virtual_machines([vm]):
            pass
        create.assert_called_once_with()
        destroy.assert_called_once_with()

    @mock.patch('vcdriver.vm.Session')
    @mock.patch.object(VirtualMachine, 'create')
    @mock.patch.object(VirtualMachine, 'destroy')
    def test_virtual_machines_fail(self, destroy, create, session):
        vm = VirtualMachine()
        with self.assertRaises(Exception):
            with virtual_machines([vm]):
                raise Exception
        create.assert_called_once_with()
        destroy.assert_called_once_with()

    @mock.patch('vcdriver.vm.Session')
    def test_virtual_machine_print_summary(self, session):
        VirtualMachine().print_summary()
