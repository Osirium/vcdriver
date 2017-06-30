import contextlib
import os
import uuid

from colorama import Style, Fore
from fabric.api import sudo, run, get, put
from pyVmomi import vim
import winrm

from vcdriver.session import connection
from vcdriver.config import configurable
from vcdriver.exceptions import (
    SshError,
    WinRmError,
    UploadError,
    DownloadError,
    NoObjectFound,
    TooManyObjectsFound,
    NotEnoughDiskSpace
)
from vcdriver.helpers import (
    get_all_vcenter_objects,
    get_vcenter_object_by_name,
    styled_print,
    timeout_loop,
    validate_ip,
    wait_for_vcenter_task,
    fabric_context,
    check_ssh_service,
    check_winrm_service
)


class VirtualMachine(object):
    def __init__(
            self,
            name=str(uuid.uuid4()),
            template=None,
            timeout=3600
    ):
        """
        :param name: The virtual machine name
        :param template: The virtual machine template name to be cloned
        :param timeout: The timeout for the tasks

        _vm_object: An internal instance of the vcenter vm object
        """
        self.name = name
        self.template = template
        self.timeout = timeout
        self._vm_object = None

    @configurable([
        ('Virtual Machine Deployment', 'vcdriver_resource_pool'),
        ('Virtual Machine Deployment', 'vcdriver_data_store'),
        ('Virtual Machine Deployment', 'vcdriver_data_store_threshold'),
        ('Virtual Machine Deployment', 'vcdriver_folder')
    ])
    def create(self, **kwargs):
        """ Create the virtual machine and update the vm object """
        if not self._vm_object:
            data_store_name = kwargs['vcdriver_data_store']
            data_store = get_vcenter_object_by_name(
                connection(),
                vim.Datastore,
                data_store_name
            )
            capacity = float(data_store.summary.capacity)
            free_space = float(data_store.summary.freeSpace)
            free_percentage = 100 * free_space / capacity
            threshold = kwargs['vcdriver_data_store_threshold']
            if free_percentage < float(threshold):
                raise NotEnoughDiskSpace(
                    data_store_name, threshold, free_percentage
                )
            self._vm_object = wait_for_vcenter_task(
                get_vcenter_object_by_name(
                    connection(), vim.VirtualMachine, self.template
                ).CloneVM_Task(
                    folder=get_vcenter_object_by_name(
                        connection(), vim.Folder, kwargs['vcdriver_folder']
                    ),
                    name=self.name,
                    spec=vim.vm.CloneSpec(
                        location=vim.vm.RelocateSpec(
                            datastore=data_store,
                            pool=get_vcenter_object_by_name(
                                connection(),
                                vim.ResourcePool,
                                kwargs['vcdriver_resource_pool']
                            )
                        ),
                        powerOn=True,
                        template=False
                    )
                ),
                'Create virtual machine "{}" from template "{}"'.format(
                    self.name, self.template
                ),
                self.timeout
            )

    def find(self):
        """ Find and update the vm object based on the name """
        if not self._vm_object:
            self._vm_object = get_vcenter_object_by_name(
                connection(), vim.VirtualMachine, self.name
            )

    def destroy(self):
        """ Destroy the virtual machine and set the vm object to None """
        self.power_off()
        if self._vm_object:
            wait_for_vcenter_task(
                self._vm_object.Destroy_Task(),
                'Destroy virtual machine "{}"'.format(self.name),
                self.timeout
            )
            self._vm_object = None

    def power_on(self):
        """ Power on the virtual machine """
        if self._vm_object:
            try:
                wait_for_vcenter_task(
                    self._vm_object.PowerOnVM_Task(),
                    'Power on virtual machine "{}"'.format(self.name),
                    self.timeout
                )
            except vim.fault.InvalidPowerState:
                pass

    def power_off(self):
        """ Power off the virtual machine """
        if self._vm_object:
            try:
                wait_for_vcenter_task(
                    self._vm_object.PowerOffVM_Task(),
                    'Power off virtual machine "{}"'.format(self.name),
                    self.timeout
                )
            except vim.fault.InvalidPowerState:
                pass

    def reset(self):
        """ Reset the virtual machine """
        if self._vm_object:
            wait_for_vcenter_task(
                self._vm_object.ResetVM_Task(),
                'Reset virtual machine "{}"'.format(self.name),
                self.timeout
            )

    def reboot(self):
        """
        Reboot the guest operating system in an async fashion
        Need Vmware tools installed in the virtual machine
        """
        if self._vm_object:
            try:
                self._vm_object.RebootGuest()
            except vim.fault.InvalidPowerState:
                pass

    def shutdown(self):
        """
        Shutdown the guest operating system
        Need Vmware tools installed in the virtual machine
        """
        if self._vm_object:
            try:
                self._vm_object.ShutdownGuest()
                timeout_loop(
                    self.timeout,
                    'Shutdown vitual machine "{}"'.format(self.name), 1, False,
                    lambda:
                    self._vm_object.summary.runtime.powerState == 'poweredOff'
                )
            except vim.fault.InvalidPowerState:
                pass

    def ip(self):
        """
        Poll vcenter to get the virtual machine IP

        :return: Return the ip
        """
        if self._vm_object:
            if not self._vm_object.summary.guest.ipAddress:
                timeout_loop(
                    self.timeout, 'Get IP', 1, False,
                    lambda: self._vm_object.summary.guest.ipAddress
                )
            ip = self._vm_object.summary.guest.ipAddress
            validate_ip(ip)
            return ip

    @configurable([
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_username'),
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_password')
    ])
    def ssh(self, command, use_sudo=False, **kwargs):
        """
        Executes a shell command through ssh
        :param command: The command to be executed
        :param use_sudo: If True, it runs as sudo

        :return: The fabric equivalent of run and sudo

        :raise: SshError: If the command fails
        """
        if self._vm_object:
            self._wait_for_ssh_service(
                kwargs['vcdriver_vm_ssh_username'],
                kwargs['vcdriver_vm_ssh_password']
            )
            with fabric_context(
                    self.ip(),
                    kwargs['vcdriver_vm_ssh_username'],
                    kwargs['vcdriver_vm_ssh_password']
            ):
                if use_sudo:
                    result = sudo(command)
                else:
                    result = run(command)
                if result.failed:
                    raise SshError(command, result.return_code)
                return result

    @configurable([
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_username'),
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_password')
    ])
    def upload(self, remote_path, local_path, use_sudo=False, **kwargs):
        """
        Upload a file or directory to the virtual machine
        :param remote_path: The remote location
        :param local_path: The local local
        :param use_sudo: If True, it runs as sudo

        :return: The list of uploaded files

        :raise: UploadError: If the task fails
        """
        if self._vm_object:
            self._wait_for_ssh_service(
                kwargs['vcdriver_vm_ssh_username'],
                kwargs['vcdriver_vm_ssh_password']
            )
            with fabric_context(
                    self.ip(),
                    kwargs['vcdriver_vm_ssh_username'],
                    kwargs['vcdriver_vm_ssh_password']
            ):
                result = put(
                    remote_path=remote_path,
                    local_path=local_path,
                    use_sudo=use_sudo
                )
                if result.failed:
                    raise UploadError(
                        local_path=local_path,
                        remote_path=remote_path
                    )
                else:
                    return result

    @configurable([
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_username'),
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_password')
    ])
    def download(self, remote_path, local_path, use_sudo=False, **kwargs):
        """
        Download a file or directory from the virtual machine
        :param remote_path: The remote location
        :param local_path: The local local
        :param use_sudo: If True, it runs as sudo

        :return: The list of downloaded files

        :raise: DownloadError: If the task fails
        """
        if self._vm_object:
            self._wait_for_ssh_service(
                kwargs['vcdriver_vm_ssh_username'],
                kwargs['vcdriver_vm_ssh_password']
            )
            with fabric_context(
                    self.ip(),
                    kwargs['vcdriver_vm_ssh_username'],
                    kwargs['vcdriver_vm_ssh_password']
            ):
                result = get(
                    remote_path=remote_path,
                    local_path=local_path,
                    use_sudo=use_sudo
                )
                if result.failed:
                    raise DownloadError(
                        local_path=local_path,
                        remote_path=remote_path
                    )
                else:
                    return result

    @configurable([
        ('Virtual Machine Remote Management', 'vcdriver_vm_winrm_username'),
        ('Virtual Machine Remote Management', 'vcdriver_vm_winrm_password')
    ])
    def winrm(self, script, winrm_kwargs, **kwargs):
        """
        Executes a remote windows powershell script
        :param script: A string with the powershell script
        :param winrm_kwargs: The pywinrm Protocol class kwargs

        :return: A tuple with the status code, the stdout and the stderr

        :raise: WinRmError: If the command fails
        """
        if self._vm_object:
            self._wait_for_winrm_service(
                kwargs['vcdriver_vm_winrm_username'],
                kwargs['vcdriver_vm_winrm_password'],
                **winrm_kwargs
            )
            print('Executing remotely on {} ...'.format(self.ip()))
            styled_print(Style.DIM)(script)
            result = winrm.Session(
                target=self.ip(),
                auth=(
                    kwargs['vcdriver_vm_winrm_username'],
                    kwargs['vcdriver_vm_winrm_password'],
                ),
                read_timeout_sec=self.timeout+1,
                operation_timeout_sec=self.timeout,
                **winrm_kwargs
            ).run_ps(script)
            styled_print(Style.BRIGHT)('CODE: {}'.format(result.status_code))
            styled_print(Fore.GREEN)(result.std_out)
            if result.status_code != 0:
                styled_print(Fore.RED)(result.std_err)
                raise WinRmError(script, result.status_code)
            else:
                return result.status_code, result.std_out, result.std_err

    def find_snapshot(self, name):
        """
        Find a snapshot by name
        :param name: The name of the snapshot

        :return: The given snapshot

        :raise: TooManyObjectsFound: If more than one object is found
        :raise: NoObjectFound: If no results are found
        """
        if self._vm_object:
            if self._vm_object.snapshot is not None:
                found_snapshots = self._get_snapshots_by_name(
                    self._vm_object.snapshot.rootSnapshotList, name
                )
            else:
                found_snapshots = []
            if len(found_snapshots) > 1:
                raise TooManyObjectsFound(vim.vm.Snapshot, name)
            elif len(found_snapshots) == 0:
                raise NoObjectFound(vim.vm.Snapshot, name)
            else:
                return found_snapshots[0].snapshot

    def create_snapshot(self, name, dump_memory, description=''):
        """
        Create a snapshot of the virtual machine
        :param name: The name of the snapshot to create
        :param dump_memory: Whether to dump the memory of the vm
        :param description: A description of the snapshot
        """
        if self._vm_object:
            try:
                self.find_snapshot(name)
            except NoObjectFound:
                wait_for_vcenter_task(self._vm_object.CreateSnapshot(
                    name, description, dump_memory, False),
                    'Creating snapshot "{}" on "{}"'.format(name, self.name),
                    self.timeout
                )
            else:
                raise TooManyObjectsFound(vim.vm.Snapshot, name)

    def revert_snapshot(self, name):
        """
        Revert to a snapshot of the virtual machine
        :param name: The name of the snapshot to revert to
        """
        if self._vm_object:
            wait_for_vcenter_task(
                self.find_snapshot(name).RevertToSnapshot_Task(),
                'Restoring snapshot "{}" on "{}"'.format(name, self.name),
                self.timeout
            )

    def remove_snapshot(self, name, remove_children=False):
        """
        Delete a snapshot from the virtual machine
        :param name: The name of the snapshot to delete
        :param remove_children: Whether to remove the children snapshots or not
        """
        if self._vm_object:
            wait_for_vcenter_task(
                self.find_snapshot(name).RemoveSnapshot_Task(remove_children),
                'Delete snapshot "{}" from "{}"'.format(name, self.name),
                self.timeout
            )

    def summary(self):
        """ Return a string summary of the virtual machine in markdown/reST """
        ip = self.ip()
        return (
            'Virtual Machine Summary{new_line}'
            '======================={new_line}'
            '{elements}'.format(
                new_line=os.linesep,
                elements=os.linesep.join([
                    '* **{}**: {}'.format(element[0], str(element[1] or ''))
                    for element in [
                        ['Name', self.name],
                        ['Template', self.template],
                        ['IP', ip]
                    ]
                ])
            )
        )

    def _wait_for_ssh_service(self, username, password):
        """
        Wait until ssh service is ready
        :param username: SSH username
        :param password: SSH password
        """
        timeout_loop(
            self.timeout, 'Check SSH service', 1, True,
            check_ssh_service, self.ip(), username, password
        )

    def _wait_for_winrm_service(self, username, password, **kwargs):
        """
        Wait until winrm service is ready
        :param username: WinRM username
        :param password: WinRM password
        :param kwargs: pywinrm Protocol kwargs
        """
        timeout_loop(
            self.timeout, 'Check WinRM service', 1, True,
            check_winrm_service, self.ip(), username, password, **kwargs
        )

    @classmethod
    def _get_snapshots_by_name(cls, snapshots, name):
        """
        Filter the snapshots by name
        :param snapshots: The list of the snapshots
        :param name: The name

        :return: The list of snapshots filtered
        """
        found_snapshots = []
        for snapshot in snapshots:
            if name == snapshot.name:
                found_snapshots.append(snapshot)
            found_snapshots = (
                found_snapshots +
                cls._get_snapshots_by_name(snapshot.childSnapshotList, name)
            )
        return found_snapshots

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self.name)


@contextlib.contextmanager
def virtual_machines(vms):
    """
    Ensure that a list of VMs are created and destroyed within a context
    :param vms: The list of virtual machines (VirtualMachine)
    """
    for vm in vms:
        vm.create()
    try:
        yield
    finally:
        for vm in vms:
            vm.destroy()


@contextlib.contextmanager
def snapshot(vm):
    """
    Ensure that you run something and restore the VM to its initial state
    :param vm: The vm object (VirtualMachine)
    """
    snapshot_name = str(uuid.uuid4())
    vm.create_snapshot(snapshot_name, True)
    try:
        yield
    finally:
        vm.revert_snapshot(snapshot_name)
        vm.remove_snapshot(snapshot_name, False)


def get_all_virtual_machines():
    """
    Get all the virtual machines from your Vcenter Instance.
    It will update both the internal _vm_object and the name.

    :return: A list with all the VirtualMachine objects
    """
    machines = []
    for vm_object in get_all_vcenter_objects(connection(), vim.VirtualMachine):
        machine = VirtualMachine()
        machine.__setattr__('_vm_object', vm_object)
        machine.name = vm_object.summary.config.name
        machines.append(machine)
    return machines
