import contextlib

from fabric.api import sudo, run, get, put
from pyVmomi import vim

from vcdriver.auth import session_context
from vcdriver.config import DATA_STORE, DATA_CENTER, RESOURCE_POOL, FOLDER
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
            data_center=DATA_CENTER,
            data_store=DATA_STORE,
            resource_pool=RESOURCE_POOL,
            folder=FOLDER,
            name=None,
            template=None,
            timeout=120,
            ssh_username=None,
            ssh_password=None
    ):
        self.data_center = data_center
        self.data_store = data_store
        self.resource_pool = resource_pool
        self.folder = folder
        self.name = name
        self.template = template
        self.timeout = timeout
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self._vm_object = None

    def create(self):
        if not self._vm_object:
            with session_context() as session:
                self._vm_object = wait_for_vcenter_task(
                    get_vcenter_object(
                        session.connection, vim.VirtualMachine, self.template
                    ).CloneVM_Task(
                        folder=get_vcenter_object(
                            session.connection, vim.Folder, self.folder
                        ),
                        name=self.name,
                        spec=vim.vm.CloneSpec(
                            location=vim.vm.RelocateSpec(
                                datastore=get_vcenter_object(
                                    session.connection,
                                    vim.Datastore,
                                    self.data_store
                                ),
                                pool=get_vcenter_object(
                                    session.connection,
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
        if self._vm_object:
            with session_context():
                wait_for_vcenter_task(
                    self._vm_object.PowerOffVM_Task(),
                    'Power off VM',
                    self.timeout
                )
                wait_for_vcenter_task(
                    self._vm_object.Destroy_Task(),
                    'Destroy VM',
                    self.timeout
                )
                self._vm_object = None

    def find(self):
        if not self._vm_object:
            with session_context() as session:
                self._vm_object = get_vcenter_object(
                    session.connection, vim.VirtualMachine, self.name
                )

    def ip(self):
        if self._vm_object:
            with session_context():
                return wait_for_dhcp_server(self._vm_object, self.timeout)

    def ssh(self, command, use_sudo=False):
        with ssh_context(self.ssh_username, self.ssh_password, self.ip()):
            if use_sudo:
                result = sudo(command)
            else:
                result = run(command)
            if result.failed:
                raise SshError(command, result.return_code)
            return result.return_code

    def upload(self, remote_path, local_path, use_sudo=False):
        with ssh_context(self.ssh_username, self.ssh_password, self.ip()):
            result = put(
                remote_path=remote_path,
                local_path=local_path,
                use_sudo=use_sudo
            )
            if result.failed:
                raise UploadError(remote_path)
            return result

    def download(self, remote_path, local_path, use_sudo=False):
        with ssh_context(self.ssh_username, self.ssh_password, self.ip()):
            result = get(
                remote_path=remote_path,
                local_path=local_path,
                use_sudo=use_sudo
            )
            if result.failed:
                raise DownloadError(remote_path)
            return result


@contextlib.contextmanager
def virtual_machines(vms):
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
