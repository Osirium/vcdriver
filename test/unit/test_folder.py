import mock
import unittest

from pyVmomi import vim

from vcdriver.folder import destroy_virtual_machines
from vcdriver.vm import VirtualMachine


class TestFolder(unittest.TestCase):
    @mock.patch('vcdriver.vm.connection')
    @mock.patch('vcdriver.folder.connection')
    @mock.patch('vcdriver.folder.get_vcenter_object')
    @mock.patch.object(VirtualMachine, 'destroy')
    def test_destroy_virtual_machines(
            self, destroy, get_vcenter_object, folder_connection, vm_connection
    ):
        vm1 = mock.MagicMock(spec=vim.VirtualMachine)
        vm1.summary.config.name = ''
        vm2 = mock.MagicMock(spec=vim.VirtualMachine)
        vm2.summary.config.name = ''
        other = mock.MagicMock()
        folder_mock = mock.MagicMock()
        folder_mock.childEntity = [vm1, vm2, other]
        get_vcenter_object.return_value = folder_mock
        self.assertEqual(len(destroy_virtual_machines('wrong folder')), 2)
        self.assertEqual(destroy.call_count, 2)
