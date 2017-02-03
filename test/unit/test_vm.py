import mock
import unittest

from pyVmomi import vim
import winrm

from vcdriver.exceptions import (
    SshError,
    DownloadError,
    UploadError,
    WinRmError
)
from vcdriver.vm import VirtualMachine, virtual_machines


class TestVm(unittest.TestCase):
    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get_vcenter_object')
    @mock.patch('vcdriver.vm.vim.vm.CloneSpec')
    @mock.patch('vcdriver.vm.vim.vm.RelocateSpec')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    @mock.patch('vcdriver.vm.wait_for_dhcp_service')
    def test_virtual_machine_create(
            self,
            wait_for_dhcp_service,
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
    @mock.patch('vcdriver.vm.wait_for_dhcp_service')
    def test_virtual_machine_ip(self, wait_for_dhcp_service, session):
        vm = VirtualMachine()
        wait_for_dhcp_service.return_value = '10.0.0.1'
        self.assertEqual(vm.ip(), None)
        vm.__setattr__('_vm_object', 'Something')
        self.assertEqual(vm.ip(), '10.0.0.1')
        self.assertEqual(vm.ip(), '10.0.0.1')
        self.assertEqual(vm.ip(use_cache=False), '10.0.0.1')
        self.assertEqual(wait_for_dhcp_service.call_count, 2)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.wait_for_ssh_service')
    def test_virtual_machine_check_ssh_service(
            self, wait_for_ssh_service, session
    ):
        vm = VirtualMachine()
        self.assertEqual(vm.__getattribute__('_ssh_ready'), False)
        vm.check_ssh_service(use_cache=True)
        self.assertEqual(vm.__getattribute__('_ssh_ready'), True)
        vm.check_ssh_service(use_cache=True)
        vm.check_ssh_service(use_cache=False)
        self.assertEqual(vm.__getattribute__('_ssh_ready'), True)
        self.assertEqual(wait_for_ssh_service.call_count, 2)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.wait_for_winrm_service')
    def test_virtual_machine_check_winrm_service(
            self, wait_for_winrm_service, session
    ):
        vm = VirtualMachine()
        self.assertEqual(vm.__getattribute__('_winrm_ready'), False)
        vm.check_winrm_service(use_cache=True)
        self.assertEqual(vm.__getattribute__('_winrm_ready'), True)
        vm.check_winrm_service(use_cache=True)
        vm.check_winrm_service(use_cache=False)
        self.assertEqual(vm.__getattribute__('_winrm_ready'), True)
        self.assertEqual(wait_for_winrm_service.call_count, 2)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.sudo')
    @mock.patch('vcdriver.vm.run')
    @mock.patch.object(VirtualMachine, 'check_ssh_service')
    def test_virtual_machine_ssh_success(
            self, check_ssh_service, run, sudo, session
    ):
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
    @mock.patch.object(VirtualMachine, 'check_ssh_service')
    def test_virtual_machine_ssh_fail(self, check_ssh_service, run, session):
        vm = VirtualMachine()
        with self.assertRaises(SshError):
            vm.ssh('whatever', use_sudo=False)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.put')
    @mock.patch.object(VirtualMachine, 'check_ssh_service')
    def test_virtual_machine_upload_success(
            self, check_ssh_service, put, session
    ):
        vm = VirtualMachine()
        result_mock = mock.MagicMock()
        result_mock.failed = False
        put.return_value = result_mock
        self.assertEqual(vm.upload('from', 'to'), result_mock)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.put')
    @mock.patch.object(VirtualMachine, 'check_ssh_service')
    def test_virtual_machine_upload_fail(
            self, check_ssh_service, put, session
    ):
        vm = VirtualMachine()
        with self.assertRaises(UploadError):
            vm.upload('from', 'to')

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get')
    @mock.patch.object(VirtualMachine, 'check_ssh_service')
    def test_virtual_machine_download_success(
            self, check_ssh_service, get, session
    ):
        vm = VirtualMachine()
        result_mock = mock.MagicMock()
        result_mock.failed = False
        get.return_value = result_mock
        self.assertEqual(vm.download('from', 'to'), result_mock)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get')
    @mock.patch.object(VirtualMachine, 'check_ssh_service')
    def test_virtual_machine_download_fail(
            self, check_ssh_service, get, session
    ):
        vm = VirtualMachine()
        with self.assertRaises(DownloadError):
            vm.download('from', 'to')

    @mock.patch('vcdriver.vm.Session')
    @mock.patch.object(winrm.Session, 'run_ps')
    @mock.patch.object(VirtualMachine, 'check_winrm_service')
    @mock.patch.object(VirtualMachine, 'ip')
    def test_virtual_machine_winrm_success(
            self, ip, check_winrm_service, run_ps, session
    ):
        ip.return_value = '127.0.0.1'
        run_ps.return_value.status_code = 0
        vm = VirtualMachine(winrm_username='user', winrm_password='pass')
        vm.winrm('script')
        run_ps.assert_called_once_with('script')

    @mock.patch('vcdriver.vm.Session')
    @mock.patch.object(winrm.Session, 'run_ps')
    @mock.patch.object(VirtualMachine, 'check_winrm_service')
    @mock.patch.object(VirtualMachine, 'ip')
    def test_virtual_machine_winrm_fail(
            self, ip, check_winrm_service, run_ps, session
    ):
        ip.return_value = '127.0.0.1'
        run_ps.return_value.status_code = 1
        vm = VirtualMachine(winrm_username='user', winrm_password='pass')
        with self.assertRaises(WinRmError):
            vm.winrm('script')

    @mock.patch('vcdriver.vm.Session')
    def test_virtual_machine_print_summary(self, session):
        VirtualMachine().print_summary()

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
