import contextlib
import os
import uuid

from colorama import Style, Fore
from fabric.api import sudo, run, get, put
from fabric.context_managers import settings
from pyVmomi import vim
import winrm

from vcdriver.session import connection
from vcdriver.config import (
    DATA_STORE,
    RESOURCE_POOL,
    FOLDER,
    VM_SSH_USERNAME,
    VM_SSH_PASSWORD,
    VM_WINRM_USERNAME,
    VM_WINRM_PASSWORD
)
from vcdriver.exceptions import (
    SshError,
    WinRmError,
    UploadError,
    DownloadError
)
from vcdriver.helpers import (
    get_all_vcenter_objects,
    get_vcenter_object_by_name,
    styled_print,
    timeout_loop,
    validate_ip,
    wait_for_vcenter_task
)


class VirtualMachine(object):
    def __init__(
            self,
            resource_pool=RESOURCE_POOL,
            data_store=DATA_STORE,
            folder=FOLDER,
            name=str(uuid.uuid4()),
            template=None,
            timeout=3600,
            ssh_username=VM_SSH_USERNAME,
            ssh_password=VM_SSH_PASSWORD,
            winrm_username=VM_WINRM_USERNAME,
            winrm_password=VM_WINRM_PASSWORD
    ):
        """
        :param resource_pool: The vcenter resource pool name
        :param data_store: The vcenter data store name
        :param folder: The vcenter folder name
        :param name: The virtual machine name
        :param template: The virtual machine template name to be cloned
        :param timeout: The timeout for the tasks
        :param ssh_username: The ssh username to manage the virtual machine
        :param ssh_password: The ssh password to manage the virtual machine
        :param winrm_username: The winrm username to manage the virtual machine
        :param winrm_password: The winrm password to manage the virtual machine

        _vm_object: An internal instance of the vcenter vm object
        """
        self.resource_pool = resource_pool
        self.data_store = data_store
        self.folder = folder
        self.name = name
        self.template = template
        self.timeout = timeout
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.winrm_username = winrm_username
        self.winrm_password = winrm_password
        self._vm_object = None

    def create(self):
        """ Create the virtual machine and update the vm object """
        if not self._vm_object:
            self._vm_object = wait_for_vcenter_task(
                get_vcenter_object_by_name(
                    connection(), vim.VirtualMachine, self.template
                ).CloneVM_Task(
                    folder=get_vcenter_object_by_name(
                        connection(), vim.Folder, self.folder
                    ),
                    name=self.name,
                    spec=vim.vm.CloneSpec(
                        location=vim.vm.RelocateSpec(
                            datastore=get_vcenter_object_by_name(
                                connection(),
                                vim.Datastore,
                                self.data_store
                            ),
                            pool=get_vcenter_object_by_name(
                                connection(),
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

    def find(self):
        """ Find and update the vm object based on the name """
        if not self._vm_object:
            self._vm_object = get_vcenter_object_by_name(
                connection(), vim.VirtualMachine, self.name
            )

    def destroy(self):
        """ Destroy the virtual machine and set the vm object to None """
        if self._vm_object:
            try:
                wait_for_vcenter_task(
                    self._vm_object.PowerOffVM_Task(),
                    'Power off virtual machine "{}"'.format(self.name),
                    self.timeout
                )
            except vim.fault.InvalidPowerState:
                pass
            wait_for_vcenter_task(
                self._vm_object.Destroy_Task(),
                'Destroy virtual machine "{}"'.format(self.name),
                self.timeout
            )
            self._vm_object = None

    def ip(self):
        """
        Poll vcenter to get the virtual machine IP

        :return: Return the ip
        """
        if self._vm_object:
            if not self._vm_object.summary.guest.ipAddress:
                timeout_loop(
                    timeout=self.timeout,
                    description='Get IP',
                    callback=lambda: self._vm_object.summary.guest.ipAddress
                )
            ip = self._vm_object.summary.guest.ipAddress
            validate_ip(ip)
            return ip

    def ssh(self, command, use_sudo=False):
        """
        Executes a shell command through ssh
        :param command: The command to be executed
        :param use_sudo: If True, it runs as sudo

        :return: The fabric equivalent of run and sudo

        :raise: SshError: If the command fails
        """
        if self._vm_object:
            self._wait_for_ssh_service()
            with self._fabric_context():
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
        if self._vm_object:
            self._wait_for_ssh_service()
            with self._fabric_context():
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

    def download(self, remote_path, local_path, use_sudo=False):
        """
        Download a file or directory from the virtual machine
        :param remote_path: The remote location
        :param local_path: The local local
        :param use_sudo: If True, it runs as sudo

        :return: The list of downloaded files

        :raise: DownloadError: If the task fails
        """
        if self._vm_object:
            self._wait_for_ssh_service()
            with self._fabric_context():
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

    def winrm(self, script, **kwargs):
        """
        Executes a remote windows powershell script
        :param script: A string with the powershell script
        :param kwargs: The pywinrm Protocol class kwargs

        :return: A tuple with the status code, the stdout and the stderr

        :raise: WinRmError: If the command fails
        """
        if self._vm_object:
            self._wait_for_winrm_service(**kwargs)
            print('Executing remotely on {} ...'.format(self.ip()))
            styled_print(Style.DIM)(script)
            result = winrm.Session(
                target=self.ip(),
                auth=(self.winrm_username, self.winrm_password),
                read_timeout_sec=self.timeout+1,
                operation_timeout_sec=self.timeout,
                **kwargs
            ).run_ps(script)
            styled_print(Style.BRIGHT)('CODE: {}'.format(result.status_code))
            styled_print(Fore.GREEN)(result.std_out)
            if result.status_code != 0:
                styled_print(Fore.RED)(result.std_err)
                raise WinRmError(script, result.status_code)
            else:
                return result.status_code, result.std_out, result.std_err

    def summary(self):
        """ Return a string summary of the virtual machine """
        ip = self.ip()
        return (
            '=======================\n'
            'Virtual Machine Summary\n'
            '=======================\n'
            '{}'.format(
                os.linesep.join([
                    '{:<40}{:<40}'.format(element[0], str(element[1]) or '')
                    for element in [
                        ['Name:', self.name],
                        ['Template:', self.template],
                        ['Resource pool:', self.resource_pool],
                        ['Data store:', self.data_store],
                        ['Folder:', self.folder],
                        ['SSH Username:', self.ssh_username],
                        ['WinRM Username:', self.winrm_username],
                        ['IP:', ip]
                    ]
                ])
            )
        )


    @contextlib.contextmanager
    def _fabric_context(self):
        """ Set the ssh context for fabric """
        ip = self.ip()
        ip_version = validate_ip(ip)['version']
        if ip_version == 6:
            ip = '[{}]'.format(ip)
        with settings(
                host_string="{}@{}".format(self.ssh_username, ip),
                password=self.ssh_password,
                warn_only=True,
                disable_known_hosts=True
        ):
            yield

    def _check_ssh_service(self):
        """ Check whether the ssh service is up or not """
        try:
            with self._fabric_context():
                run('')
                return True
        except:
            return False

    def _check_winrm_service(self, **kwargs):
        """
        Check whether the winrm service is up or not
        :param kwargs: pywinrm Protocol kwargs
        """
        try:
            winrm.Session(
                target=self.ip(),
                auth=(self.winrm_username, self.winrm_password),
                **kwargs
            ).run_ps('')
            return True
        except:
            return False

    def _wait_for_ssh_service(self):
        """ Wait until ssh service is ready """
        self.ip()
        timeout_loop(
            timeout=self.timeout,
            description='Check SSH service',
            callback=self._check_ssh_service
        )

    def _wait_for_winrm_service(self, **kwargs):
        """
        Wait until winrm service is ready
        :param kwargs: pywinrm Protocol kwargs
        """
        self.ip()
        timeout_loop(
            timeout=self.timeout,
            description='Check WinRM service',
            callback=self._check_winrm_service,
            **kwargs
        )

    def __str__(self):
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
        for vm in vms:
            vm.destroy()
    except:
        print('An exception has been thrown, cleaning up virtual machines:')
        for vm in vms:
            vm.destroy()
        raise


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
