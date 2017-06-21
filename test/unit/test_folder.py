import mock
from pyVmomi import vim

from vcdriver.folder import destroy_virtual_machines
from vcdriver.vm import VirtualMachine


@mock.patch('vcdriver.vm.connection')
@mock.patch('vcdriver.folder.connection')
@mock.patch('vcdriver.folder.get_vcenter_object_by_name')
@mock.patch.object(VirtualMachine, 'destroy')
def test_destroy_virtual_machines(
        destroy, get_vcenter_object_by_name, folder_connection, vm_connection
):
    vm1 = mock.MagicMock(spec=vim.VirtualMachine)
    vm1.summary.config.name = ''
    vm2 = mock.MagicMock(spec=vim.VirtualMachine)
    vm2.summary.config.name = ''
    other = mock.MagicMock()
    folder_mock = mock.MagicMock()
    folder_mock.childEntity = [vm1, vm2, other]
    get_vcenter_object_by_name.return_value = folder_mock
    assert len(destroy_virtual_machines('wrong folder')) == 2
    assert destroy.call_count == 2
