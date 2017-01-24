import contextlib

from fabric.api import sudo, run, get, put
from pyVmomi import vim

from vcdriver.auth import Session
from vcdriver.config import DATA_STORE, RESOURCE_POOL, FOLDER
from vcdriver.exceptions import SshError, UploadError, DownloadError
from vcdriver.helpers import (
    get_vcenter_object,
    wait_for_vcenter_task,
    wait_for_dhcp_server,
    ssh_context
)


class VirtualMachine(object):
    def __init__(
            self,
            resource_pool=RESOURCE_POOL,
            data_store=DATA_STORE,
            folder=FOLDER,
            name=None,
            template=None,
            timeout=120,
            ssh_username=None,
            ssh_password=None
    ):
        """
        :param resource_pool: The vcenter resource pool name
        :param data_store: The vcenter data store name
        :param folder: The vcenter folder name
        :param name: The virtual machine name
        :param template: The virtual machine template name to be cloned
        :param timeout: The timeout for the dhcp and vcenter tasks
        :param ssh_username: The username for the ssh functions
        :param ssh_password: The password for the ssh functions

        An internal session that gets closed at exit is kept as _session
        An internal instance of a vcenter vm object is kept as _vm_object
        The ip is cached internally as _ip
        """
        self.resource_pool = resource_pool
        self.data_store = data_store
        self.folder = folder
        self.name = name
        self.template = template
        self.timeout = timeout
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self._session = Session()
        self._vm_object = None
        self._ip = None

    def create(self):
        """ Create the virtual machine and update the vm object """
        if not self._vm_object:
            self._vm_object = wait_for_vcenter_task(
                get_vcenter_object(
                    self._session.connection, vim.VirtualMachine, self.template
                ).CloneVM_Task(
                    folder=get_vcenter_object(
                        self._session.connection, vim.Folder, self.folder
                    ),
                    name=self.name,
                    spec=vim.vm.CloneSpec(
                        location=vim.vm.RelocateSpec(
                            datastore=get_vcenter_object(
                                self._session.connection,
                                vim.Datastore,
                                self.data_store
                            ),
                            pool=get_vcenter_object(
                                self._session.connection,
                                vim.ResourcePool,
                                self.resource_pool
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

    def destroy(self):
        """ Destroy the virtual machine and set the vm object to None """
        if self._vm_object:
            wait_for_vcenter_task(
                self._vm_object.PowerOffVM_Task(),
                'Power off virtual machine "{}"'.format(self.name),
                self.timeout
            )
            wait_for_vcenter_task(
                self._vm_object.Destroy_Task(),
                'Destroy virtual machine "{}"'.format(self.name),
                self.timeout
            )
            self._vm_object = None
            self._ip = None

    def find(self):
        """ Find and update the vm object based on the name """
        if not self._vm_object:
            self._vm_object = get_vcenter_object(
                self._session.connection, vim.VirtualMachine, self.name
            )
            print('VM object found: {}'.format(self._vm_object))

    def ip(self, use_cache=True):
        """
        Poll vcenter to get the virtual machine IP
        :param use_cache: If False, force an update of the internal value

        :return: Return the ip
        """
        if self._vm_object:
            if not self._ip or not use_cache:
                self._ip = wait_for_dhcp_server(self._vm_object, self.timeout)
            return self._ip

    def ssh(self, command, use_sudo=False):
        """
        Executes a shell command through ssh
        :param command: The command to be executed
        :param use_sudo: If True, it runs as sudo

        :return: The fabric equivalent of run and sudo

        :raise: SshError: If the command fails
        """
        with ssh_context(self.ssh_username, self.ssh_password, self.ip()):
            if use_sudo:
                result = sudo(command)
            else:
                result = run(command)
            if result.failed:
                raise SshError(command, result.return_code)
            return result

    def upload(self, remote_path, local_path, use_sudo=False):
        """
        Upload a file or directory to the virtual machine
        :param remote_path: The remote location
        :param local_path: The local local
        :param use_sudo: If True, it runs as sudo

        :return: The list of uploaded files

        :raise: UploadError: If the task fails
        """
        with ssh_context(self.ssh_username, self.ssh_password, self.ip()):
            try:
                result = put(
                    remote_path=remote_path,
                    local_path=local_path,
                    use_sudo=use_sudo
                )
                if result.failed:
                    raise UploadError(remote_path)
            except ValueError as value_error:
                print(value_error)
                raise UploadError(remote_path)
            return result

    def download(self, remote_path, local_path, use_sudo=False):
        """
        Download a file or directory from the virtual machine
        :param remote_path: The remote location
        :param local_path: The local local
        :param use_sudo: If True, it runs as sudo

        :return: The list of downloaded files

        :raise: DownloadError: If the task fails
        """
        with ssh_context(self.ssh_username, self.ssh_password, self.ip()):
            result = get(
                remote_path=remote_path,
                local_path=local_path,
                use_sudo=use_sudo
            )
            if result.failed:
                raise DownloadError(remote_path)
            return result

    def print_summary(self):
        """ Print a nice summary of the virtual machine """
        ip = self.ip()
        row_format = "{:<40}" * 2
        print(
            '\033[1m'
            '=======================\n'
            'Virtual Machine Summary\n'
            '======================='
            '\033[0m'
        )
        for element in [
            ['\033[94mName\033[0m', self.name],
            ['\033[94mTemplate\033[0m', self.template],
            ['\033[94mResource pool\033[0m', self.resource_pool],
            ['\033[94mData store\033[0m', self.data_store],
            ['\033[94mFolder\033[0m', self.folder],
            ['\033[94mSSH username\033[0m', self.ssh_username],
            ['\033[94mSSH password\033[0m', self.ssh_password],
            ['\033[94mIP\033[0m', ip]
        ]:
            print(row_format.format(element[0], str(element[1])))


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
        for vm in vms:
            vm.destroy()
    except:
        print('An exception has been thrown, cleaning up virtual machines:')
        for vm in vms:
            vm.destroy()
        raise
