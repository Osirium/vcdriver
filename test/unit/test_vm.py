import mock
import unittest

from pyVmomi import vim
import winrm

from vcdriver.exceptions import (
    NoObjectFound,
    TooManyObjectsFound,
    SshError,
    DownloadError,
    UploadError,
    WinRmError,
    TimeoutError,
    MissingCredentialsError
)
from vcdriver.vm import (
    VirtualMachine,
    virtual_machines,
    get_all_virtual_machines,
)


class TestVm(unittest.TestCase):
    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.get_vcenter_object_by_name')
    @mock.patch('vcdriver.vm.vim.vm.CloneSpec')
    @mock.patch('vcdriver.vm.vim.vm.RelocateSpec')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_virtual_machine_create(
            self,
            wait_for_vcenter_task,
            relocate_spec,
            clone_spec,
            get_vcenter_object_by_name,
            connection
    ):
        vm = VirtualMachine()
        vm.create()
        vm.create()
        self.assertIsNotNone(vm.__getattribute__('_vm_object'))
        self.assertEqual(wait_for_vcenter_task.call_count, 1)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_virtual_machine_destroy_vm_on(
            self, wait_for_vcenter_task, connection
    ):
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        vm.__setattr__('_vm_object', vm_object_mock)
        vm.destroy()
        vm.destroy()
        self.assertIsNone(vm.__getattribute__('_vm_object'))
        self.assertEqual(wait_for_vcenter_task.call_count, 2)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_virtual_machine_destroy_vm_off(
            self, wait_for_vcenter_task, connection
    ):
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        vm.__setattr__('_vm_object', vm_object_mock)
        wait_for_vcenter_task.side_effect = [vim.fault.InvalidPowerState, None]
        vm.destroy()
        vm.destroy()
        self.assertIsNone(vm.__getattribute__('_vm_object'))
        self.assertEqual(wait_for_vcenter_task.call_count, 2)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.get_vcenter_object_by_name')
    def test_virtual_machine_find(
            self, get_vcenter_object_by_name, connection
    ):
        vm = VirtualMachine()
        vm.find()
        vm.find()
        self.assertIsNotNone(vm.__getattribute__('_vm_object'))
        self.assertEqual(get_vcenter_object_by_name.call_count, 1)

    @mock.patch('vcdriver.vm.connection')
    def test_virtual_machine_reboot(self, connection):
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        reboot_mock = mock.MagicMock()
        vm_object_mock.RebootGuest = reboot_mock
        vm.reboot()
        vm.__setattr__('_vm_object', vm_object_mock)
        vm.reboot()
        self.assertEqual(reboot_mock.call_count, 1)

    @mock.patch('vcdriver.vm.connection')
    def test_virtual_machine_reboot_wrong_power_state(self, connection):
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        reboot_mock = mock.MagicMock()
        reboot_mock.side_effect = vim.fault.InvalidPowerState
        vm_object_mock.RebootGuest = reboot_mock
        vm.reboot()
        vm.__setattr__('_vm_object', vm_object_mock)
        vm.reboot()
        self.assertEqual(reboot_mock.call_count, 1)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_virtual_machine_reset(self, wait_for_vcenter_task, connection):
        vm = VirtualMachine()
        vm.reset()
        vm_object_mock = mock.MagicMock()
        vm.__setattr__('_vm_object', vm_object_mock)
        vm.reset()
        self.assertEqual(wait_for_vcenter_task.call_count, 1)

    @mock.patch('vcdriver.vm.connection')
    def test_virtual_machine_ip(self, connection):
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        self.assertEqual(vm.ip(), None)
        vm.__setattr__('_vm_object', vm_object_mock)
        self.assertEqual(vm.ip(), '127.0.0.1')
        self.assertEqual(vm.ip(), '127.0.0.1')

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.timeout_loop')
    @mock.patch('vcdriver.vm.validate_ip')
    def test_virtual_machine_ip_with_dhcp_wait(
            self, validate_ip, timeout_loop, connection
    ):
        vm = VirtualMachine()
        validate_ip.side_effect = lambda x: x
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = None
        vm.__setattr__('_vm_object', vm_object_mock)
        self.assertEqual(vm.ip(), None)

    @mock.patch('vcdriver.vm.connection')
    def test_virtual_machine_ip_timeout(self, connection):
        vm = VirtualMachine(timeout=1)
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = None
        vm.__setattr__('_vm_object', vm_object_mock)
        with self.assertRaises(TimeoutError):
            vm.ip()

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.sudo')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_ssh_success(
            self, run, sudo, connection
    ):
        vm = VirtualMachine(ssh_username='', ssh_password='')
        self.assertEqual(vm.ssh('whatever'), None)
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        result_mock = mock.MagicMock()
        result_mock.return_code = 3
        result_mock.failed = False
        run.return_value = result_mock
        sudo.return_value = result_mock
        self.assertEqual(vm.ssh('whatever', use_sudo=False).return_code, 3)
        self.assertEqual(vm.ssh('whatever', use_sudo=True).return_code, 3)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.run')
    @mock.patch('vcdriver.vm.sudo')
    def test_virtual_machine_ssh_fail(self, sudo, run, connection):
        vm = VirtualMachine(ssh_username='', ssh_password='')
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = 'fe80::250:56ff:febf:1a0a'
        vm.__setattr__('_vm_object', vm_object_mock)
        with self.assertRaises(SshError):
            vm.ssh('whatever', use_sudo=True)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_ssh_timeout(self, run, connection):
        vm = VirtualMachine(ssh_username='', ssh_password='', timeout=1)
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        run.side_effect = Exception
        with self.assertRaises(TimeoutError):
            vm.ssh('whatever', use_sudo=True)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.put')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_upload_success(
            self, run, put, connection
    ):
        vm = VirtualMachine(ssh_username='', ssh_password='')
        self.assertEqual(vm.upload('from', 'to'), None)
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        result_mock = mock.MagicMock()
        result_mock.failed = False
        put.return_value = result_mock
        self.assertEqual(vm.upload('from', 'to'), result_mock)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.put')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_upload_fail(
            self, run, put, connection
    ):
        vm = VirtualMachine(ssh_username='', ssh_password='')
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        with self.assertRaises(UploadError):
            vm.upload('from', 'to')

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.get')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_download_success(
            self, run, get, session
    ):
        vm = VirtualMachine(ssh_username='', ssh_password='')
        self.assertEqual(vm.download('from', 'to'), None)
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        result_mock = mock.MagicMock()
        result_mock.failed = False
        get.return_value = result_mock
        self.assertEqual(vm.download('from', 'to'), result_mock)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.get')
    @mock.patch('vcdriver.vm.run')
    def test_virtual_machine_download_fail(
            self, run, get, session
    ):
        vm = VirtualMachine(ssh_username='', ssh_password='')
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        with self.assertRaises(DownloadError):
            vm.download('from', 'to')

    @mock.patch('vcdriver.vm.connection')
    @mock.patch.object(winrm.Session, 'run_ps')
    def test_virtual_machine_winrm_success(self, run_ps, connection):
        vm = VirtualMachine(winrm_username='user', winrm_password='pass')
        self.assertEqual(vm.winrm('whatever'), None)
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        run_ps.return_value.status_code = 0
        vm.winrm('script')
        run_ps.assert_called_with('script')
        self.assertEqual(run_ps.call_count, 2)

    @mock.patch('vcdriver.vm.connection')
    @mock.patch.object(winrm.Session, 'run_ps')
    def test_virtual_machine_winrm_fail(self, run_ps, connection):
        vm = VirtualMachine(winrm_username='user', winrm_password='pass')
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        run_ps.return_value.status_code = 1
        with self.assertRaises(WinRmError):
            vm.winrm('script')

    @mock.patch('vcdriver.vm.connection')
    @mock.patch.object(winrm.Session, 'run_ps')
    def test_virtual_machine_winrm_timeout(self, run_ps, connection):
        vm = VirtualMachine(
            winrm_username='user', winrm_password='pass', timeout=1
        )
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm.__setattr__('_vm_object', vm_object_mock)
        run_ps.side_effect = Exception
        with self.assertRaises(TimeoutError):
            vm.winrm('script')

    @mock.patch('vcdriver.vm.connection')
    def test_virtual_machine_missing_credentials(self, connection):
        vm_object_mock = mock.MagicMock()
        vm_object_mock.summary.guest.ipAddress = '127.0.0.1'
        vm = VirtualMachine()
        vm.__setattr__('_vm_object', vm_object_mock)
        with self.assertRaises(MissingCredentialsError):
            vm.winrm('')
        with self.assertRaises(MissingCredentialsError):
            vm.ssh('')
        vm = VirtualMachine(ssh_username='', winrm_password='')
        vm.__setattr__('_vm_object', vm_object_mock)
        with self.assertRaises(MissingCredentialsError):
            vm.winrm('')
        with self.assertRaises(MissingCredentialsError):
            vm.ssh('')

    @mock.patch('vcdriver.vm.connection')
    def test_virtual_machine_summary(self, connection):
        print(VirtualMachine().summary())

    def test_str_repr(self):
        self.assertEqual(str(VirtualMachine(name='whatever')), 'whatever')
        self.assertEqual(repr(VirtualMachine(name='whatever')), 'whatever')

    @mock.patch('vcdriver.vm.connection')
    @mock.patch.object(VirtualMachine, 'create')
    @mock.patch.object(VirtualMachine, 'destroy')
    def test_virtual_machines_success(self, destroy, create, connection):
        vm = VirtualMachine()
        with virtual_machines([vm]):
            pass
        create.assert_called_once_with()
        destroy.assert_called_once_with()

    @mock.patch('vcdriver.vm.connection')
    @mock.patch.object(VirtualMachine, 'create')
    @mock.patch.object(VirtualMachine, 'destroy')
    def test_virtual_machines_fail(self, destroy, create, connection):
        vm = VirtualMachine()
        with self.assertRaises(Exception):
            with virtual_machines([vm]):
                raise Exception
        create.assert_called_once_with()
        destroy.assert_called_once_with()

    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.vm.get_all_vcenter_objects')
    def test_get_all_virtual_machines(
            self, get_all_vcenter_objects, connection
    ):
        obj1 = mock.MagicMock()
        obj2 = mock.MagicMock()
        get_all_vcenter_objects.return_value = [obj1, obj2]
        self.assertEqual(len(get_all_virtual_machines()), 2)

    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_find_snapshot(self, wait_for_vcenter_task):
        fake_snapshots = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock()]
        for snapshot in fake_snapshots[:-1]:
            snapshot.name = 'snapshot'
            snapshot.childSnapshotList = []
        fake_snapshots[-1].name = 'other'
        fake_snapshots[-1].childSnapshotList = []
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        vm.__setattr__('_vm_object', vm_object_mock)
        vm_object_mock.snapshot.rootSnapshotList = []
        with self.assertRaises(NoObjectFound):
            vm.find_snapshot('snapshot')
        vm_object_mock.snapshot.rootSnapshotList = fake_snapshots[:-2]
        vm.find_snapshot('snapshot')
        vm_object_mock.snapshot.rootSnapshotList = fake_snapshots
        with self.assertRaises(TooManyObjectsFound):
            vm.find_snapshot('snapshot')
        vm_object_mock.snapshot = None
        with self.assertRaises(NoObjectFound):
            vm.find_snapshot('snapshot')

    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_create_snapshot(self, wait_for_vcenter_task):
        fake_snapshot = mock.MagicMock()
        fake_snapshot.name = 'snapshot'
        fake_snapshot.childSnapshotList = []
        vm = VirtualMachine()
        vm_object_mock = mock.MagicMock()
        vm_object_mock.snapshot.rootSnapshotList = []
        vm.__setattr__('_vm_object', vm_object_mock)
        vm.create_snapshot('snapshot', True)
        vm_object_mock.snapshot.rootSnapshotList = [fake_snapshot]
        with self.assertRaises(TooManyObjectsFound):
            vm.create_snapshot('snapshot', True)

    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_revert_snapshot(self, wait_for_vcenter_task):
        vm = VirtualMachine()
        vm.find_snapshot = mock.MagicMock()
        vm.revert_snapshot('snapshot')

    @mock.patch('vcdriver.vm.wait_for_vcenter_task')
    def test_delete_snapshot(self, wait_for_vcenter_task):
        vm = VirtualMachine()
        vm.find_snapshot = mock.MagicMock()
        vm.delete_snapshot('snapshot')
