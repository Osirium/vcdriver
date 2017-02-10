from pyVmomi import vim

from vcdriver.session import connection
from vcdriver.helpers import get_vcenter_object_by_name
from vcdriver.vm import VirtualMachine


def destroy_virtual_machines(folder_name, timeout=600):
    """
    Destroy all the virtual machines in the folder with the given name
    :param folder_name: The folder name
    :param timeout: The timeout for vcenter tasks in seconds

    :return: A list with the destroyed vms
    """
    folder = get_vcenter_object_by_name(connection(), vim.Folder, folder_name)
    destroyed_vms = []
    for entity in folder.childEntity:
        if isinstance(entity, vim.VirtualMachine):
            vm = VirtualMachine(
                name=entity.summary.config.name, timeout=timeout
            )
            vm.__setattr__('_vm_object', entity)
            vm.destroy()
            destroyed_vms.append(vm)
    return destroyed_vms
