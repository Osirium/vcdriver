import mock
import unittest
from fabric.api import local

from vcdriver import vm


class VmObjectMock(object):
    def __init__(self, ip):
        super(self.__class__, self).__init__()
        self.__setattr__('PowerOffVM_Task', mock.MagicMock)
        self.__setattr__('Destroy_Task', mock.MagicMock)
        self.__setattr__('summary', mock.MagicMock())
        setattr(self.summary, 'guest', mock.MagicMock())
        setattr(self.summary.guest, 'ipAddress', ip)


class TestVm(unittest.TestCase):
    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get_object')
    @mock.patch('vcdriver.vm.vim.vm.CloneSpec')
    @mock.patch('vcdriver.vm.vim.vm.RelocateSpec')
    @mock.patch('vcdriver.vm.wait_for_task')
    def test_virtual_machine_create(
            self, wait_for_task, relocate_spec, clone_spec, get_object, session
    ):
        session.connection = 'some connection'
        session.id = 'some id'
        wait_for_task.return_value = VmObjectMock('127.0.0.1')
        vm.VirtualMachine(template=None, name='something', folder='a').create()
        machine = vm.VirtualMachine(template=None)
        machine.create()
        machine.create()
        self.assertEqual(wait_for_task.call_count, 2)

    @mock.patch('vcdriver.vm.Session')
    @mock.patch('vcdriver.vm.get_object')
    @mock.patch('vcdriver.vm.vim.vm.CloneSpec')
    @mock.patch('vcdriver.vm.vim.vm.RelocateSpec')
    @mock.patch('vcdriver.vm.wait_for_task')
    def test_virtual_machine_create_with_dhcp_timeout(
            self, wait_for_task, relocate_spec, clone_spec, get_object, session
    ):
        session.connection = 'some connection'
        session.id = 'some id'
        wait_for_task.return_value = VmObjectMock(None)
        with self.assertRaises(RuntimeError):
            vm.VirtualMachine(template=None, dhcp_timeout=1).create()

    @mock.patch('vcdriver.vm.wait_for_task')
    def test_virtual_machine_destroy(self, wait):
        machine = vm.VirtualMachine(template=None)
        machine.vm_object = VmObjectMock('127.0.0.1')
        machine.destroy()
        machine.destroy()
        self.assertEqual(wait.call_count, 2)

    @mock.patch('vcdriver.vm.run', side_effect=local)
    @mock.patch('vcdriver.vm.settings')
    def test_virtual_machine_ssh(self, settings, run):
        run.return_code = 0
        run.failed = False
        self.assertEqual(
            vm.VirtualMachine(template=None).ssh('', use_sudo=False), 0
        )

    @mock.patch('vcdriver.vm.sudo', side_effect=local)
    @mock.patch('vcdriver.vm.settings')
    def test_virtual_machine_ssh_with_sudo(self, settings, sudo):
        sudo.return_code = 0
        sudo.failed = False
        self.assertEqual(
            vm.VirtualMachine(template=None).ssh('', use_sudo=True), 0
        )

    @mock.patch('vcdriver.vm.run')
    @mock.patch('vcdriver.vm.settings')
    def test_virtual_machine_ssh_fails(self, settings, run):
        run.return_code = 27
        run.failed = True
        with self.assertRaises(RuntimeError):
            vm.VirtualMachine(template=None).ssh('', use_sudo=False)

    @mock.patch.object(vm.VirtualMachine, 'create')
    @mock.patch.object(vm.VirtualMachine, 'destroy')
    def test_virtual_machines(self, destroy, create):
        with vm.virtual_machines([vm.VirtualMachine(template=None)]):
            pass
        create.assert_called_once_with()
        destroy.assert_called_once_with()

    @mock.patch.object(vm.VirtualMachine, 'create')
    @mock.patch.object(vm.VirtualMachine, 'destroy')
    def test_virtual_machines_with_exception(self, destroy, create):
        with self.assertRaises(Exception):
            with vm.virtual_machines([vm.VirtualMachine(template=None)]):
                raise Exception
        create.assert_called_once_with()
        destroy.assert_called_once_with()
