import mock
import unittest

from vcdriver.exceptions import SshError, DownloadError, UploadError
from vcdriver.vm import VirtualMachine, virtual_machines


class TestVm(unittest.TestCase):
    def setUp(self):
        self.vm = VirtualMachine()

    @mock.patch('vcdriver.vm.session_context')
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
            session_context
    ):
        self.vm.create()
        self.vm.create()
        self.assertIsNotNone(self.vm.__getattribute__('_vm_object'))
        self.assertEqual(wait_for_vcenter_task.call_count, 1)

    @mock.patch('vcdriver.vm.session_context')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_virtual_machine_destroy(
            self,
            wait_for_vcenter_task,
            session_context
    ):
        vm_object_mock = mock.MagicMock()
        vm_object_mock.PowerOffVM_Task = lambda: True
        vm_object_mock.Destroy_Task = lambda: True
        self.vm.__setattr__('_vm_object', vm_object_mock)
        self.vm.destroy()
        self.vm.destroy()
        self.assertIsNone(self.vm.__getattribute__('_vm_object'))
        self.assertEqual(wait_for_vcenter_task.call_count, 2)

    @mock.patch('vcdriver.vm.session_context')
    @mock.patch('vcdriver.vm.get_vcenter_object')
    def test_virtual_machine_find(self, get_vcenter_object, session_context):
        self.vm.find()
        self.vm.find()
        self.assertIsNotNone(self.vm.__getattribute__('_vm_object'))
        self.assertEqual(get_vcenter_object.call_count, 1)

    @mock.patch('vcdriver.vm.session_context')
    @mock.patch('vcdriver.vm.wait_for_dhcp_server')
    def test_virtual_machine_ip(self, wait_for_dhcp_server, session_context):
        wait_for_dhcp_server.return_value = '10.0.0.1'
        self.assertEqual(self.vm.ip(), None)
        self.vm.__setattr__('_vm_object', 'Something')
        self.assertEqual(self.vm.ip(), '10.0.0.1')

    @mock.patch('vcdriver.vm.sudo')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_ssh_success(self, run, sudo):
        result_mock = mock.MagicMock()
        result_mock.return_code = 3
        result_mock.failed = False
        run.return_value = result_mock
        sudo.return_value = result_mock
        self.assertEqual(
            self.vm.ssh('whatever', use_sudo=False), 3
        )
        self.assertEqual(
            self.vm.ssh('whatever', use_sudo=True), 3
        )

    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_ssh_fail(self, run):
        with self.assertRaises(SshError):
            self.vm.ssh('whatever', use_sudo=False)

    @mock.patch('vcdriver.vm.put')
    def test_virtual_machine_upload_success(self, put):
        result_mock = mock.MagicMock()
        result_mock.failed = False
        put.return_value = result_mock
        self.assertEqual(self.vm.upload('from', 'to'), result_mock)

    @mock.patch('vcdriver.vm.put')
    def test_virtual_machine_upload_fail(self, put):
        with self.assertRaises(UploadError):
            self.vm.upload('from', 'to')

    @mock.patch('vcdriver.vm.get')
    def test_virtual_machine_download_success(self, get):
        result_mock = mock.MagicMock()
        result_mock.failed = False
        get.return_value = result_mock
        self.assertEqual(self.vm.download('from', 'to'), result_mock)

    @mock.patch('vcdriver.vm.get')
    def test_virtual_machine_download_fail(self, get):
        with self.assertRaises(DownloadError):
            self.vm.download('from', 'to')

    @mock.patch.object(VirtualMachine, 'create')
    @mock.patch.object(VirtualMachine, 'destroy')
    def test_virtual_machines_success(self, destroy, create):
        with virtual_machines([self.vm]):
            pass
        create.assert_called_once_with()
        destroy.assert_called_once_with()

    @mock.patch.object(VirtualMachine, 'create')
    @mock.patch.object(VirtualMachine, 'destroy')
    def test_virtual_machines_fail(self, destroy, create):
        with self.assertRaises(Exception):
            with virtual_machines([self.vm]):
                raise Exception
        create.assert_called_once_with()
        destroy.assert_called_once_with()
