import mock
import unittest
from fabric.api import local

from vcdriver import vm


class TestVm(unittest.TestCase):
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

