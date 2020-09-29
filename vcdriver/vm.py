from __future__ import print_function

import base64
import contextlib
import datetime
import os
import sys
import time
import uuid

from colorama import Style, Fore
from fabric.api import sudo, run, get, put, hide
from pyVmomi import vim
import winrm

from vcdriver.config import configurable
from vcdriver.exceptions import (
    SshError,
    WinRmError,
    UploadError,
    DownloadError,
    NoObjectFound,
    TooManyObjectsFound,
    NotEnoughDiskSpace,
    TimeoutError
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
    check_winrm_service,
)
from vcdriver.session import (
    connection,
    close,
    )


class VirtualMachine(object):
    def __init__(
            self,
            name=None,
            template=None,
            timeout=3600
    ):
        """
        :param name: The virtual machine name
        :param template: The virtual machine template name to be cloned
        :param timeout: The timeout for the tasks

        _vm_object: An internal instance of the vcenter vm object
        """
        self.name = name or str(uuid.uuid4())
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
        conn = connection()
        if not self._vm_object:
            data_store_name = kwargs['vcdriver_data_store']
            data_store = get_vcenter_object_by_name(
                conn,
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
                    conn, vim.VirtualMachine, self.template
                ).CloneVM_Task(
                    folder=get_vcenter_object_by_name(
                        conn, vim.Folder, kwargs['vcdriver_folder']
                    ),
                    name=self.name,
                    spec=vim.vm.CloneSpec(
                        location=vim.vm.RelocateSpec(
                            datastore=data_store,
                            pool=get_vcenter_object_by_name(
                                conn,
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

    def refresh(self):
        """ Close session and create a new session """
        if self._vm_object:
            close()
            # Refresh object with updated data (connection id changed)
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

    def power_off(self, delay_by=None):
        """
        Power off the virtual machine

        :param delay_by: if specified, it has to be a timedelta that indicates
            when in the future this task will be executed.
        """
        if self._vm_object:
            if delay_by is None:
                try:
                    wait_for_vcenter_task(
                        self._vm_object.PowerOffVM_Task(),
                        'Power off virtual machine "{}"'.format(self.name),
                        self.timeout
                    )
                except vim.fault.InvalidPowerState:
                    pass
            else:
                self._schedule_vcenter_task_on_vm(
                    vim.VirtualMachine.PowerOff,
                    # task name can't be longer than 80 chars and as to be
                    # unique
                    'Power off {}'.format(self.vm_id()),
                    delay_by
                )

    def reset(self):
        """ Reset the virtual machine """
        if self._vm_object:
            try:
                wait_for_vcenter_task(
                    self._vm_object.ResetVM_Task(),
                    'Reset virtual machine "{}"'.format(self.name),
                    self.timeout
                )
            except vim.fault.InvalidPowerState:
                pass

    def reboot(self):
        """
        Reboot the guest operating system in an async fashion
        Need Vmware tools installed in the virtual machine
        """
        if self._vm_object:
            if self._vm_object.summary.runtime.powerState == 'poweredOn':
                self._wait_for_vmware_tools()
                self._vm_object.RebootGuest()

    def shutdown(self):
        """
        Shutdown the guest operating system in an async fashion
        Need Vmware tools installed in the virtual machine
        """
        if self._vm_object:
            if self._vm_object.summary.runtime.powerState == 'poweredOn':
                self._wait_for_vmware_tools()
                self._vm_object.ShutdownGuest()

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

    def vm_id(self):
        """
        Return the vcenter ID of this VM.

        :return: Return a string in the following format: vm-<number> i.e:
            vm-4856 or None in case the VirtualMachine data has not been
            retrieved from vCenter i.e: find() has not been called yet
        """

        if self._vm_object:
            # summary.vm has the following format:
            # 'vim.VirtualMachine:vm-83288'
            return str(self._vm_object.summary.vm).strip("'").split(":")[1]
        return None

    @property
    def created_at(self):
        """
        Get the created at timestamp

        :return: The datetime object
        """
        # TODO: https://www.virtuallyghetto.com/2018/04/vm-creation-date-now-available-in-vsphere-6-7.html # noqa
        return datetime.datetime.strptime(
            self._vm_object.config.changeVersion, '%Y-%m-%dT%H:%M:%S.%fZ'
        )

    @configurable([
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_username'),
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_password')
    ])
    def ssh(self, command, use_sudo=False, quiet=False, **kwargs):
        """
        Executes a shell command through ssh
        :param command: The command to be executed
        :param use_sudo: If True, it runs as sudo
        :param quiet: Whether to hide the stdout/stderr output or not

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
                    runner = sudo
                else:
                    runner = run
                if quiet:
                    with hide('everything'):
                        result = runner(command)
                else:
                    result = runner(command)
                if result.failed:
                    raise SshError(command, result.return_code, result.stdout)
                return result

    @configurable([
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_username'),
        ('Virtual Machine Remote Management', 'vcdriver_vm_ssh_password')
    ])
    def ssh_upload(
            self,
            remote_path,
            local_path,
            use_sudo=False,
            quiet=False,
            **kwargs
    ):
        """
        Upload a file or directory to the virtual machine
        :param remote_path: The remote location
        :param local_path: The local local
        :param use_sudo: If True, it runs as sudo
        :param quiet: Whether to hide the stdout/stderr output or not

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
                if quiet:
                    with hide('everything'):
                        result = put(
                            local_path, remote_path, use_sudo=use_sudo
                        )
                else:
                    result = put(local_path, remote_path, use_sudo=use_sudo)
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
    def ssh_download(
            self,
            remote_path,
            local_path,
            use_sudo=False,
            quiet=False,
            **kwargs
    ):
        """
        Download a file or directory from the virtual machine
        :param remote_path: The remote location
        :param local_path: The local local
        :param use_sudo: If True, it runs as sudo
        :param quiet: Whether to hide the stdout/stderr output or not

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
                if quiet:
                    with hide('everything'):
                        result = get(
                            remote_path, local_path, use_sudo=use_sudo
                        )
                else:
                    result = get(remote_path, local_path, use_sudo=use_sudo)
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
    def winrm(self, script, winrm_kwargs=dict(), quiet=False, **kwargs):
        """
        Executes a remote windows powershell script
        :param script: A string with the powershell script
        :param winrm_kwargs: The pywinrm Protocol class kwargs
        :param quiet: Whether to hide the stdout/stderr output or not

        :return: A tuple with the status code, the stdout and the stderr

        :raise: WinRmError: If the command fails
        """
        if self._vm_object:
            self._wait_for_winrm_service(
                kwargs['vcdriver_vm_winrm_username'],
                kwargs['vcdriver_vm_winrm_password'],
                **winrm_kwargs
            )
            winrm_session = self._open_winrm_session(
                kwargs['vcdriver_vm_winrm_username'],
                kwargs['vcdriver_vm_winrm_password'],
                winrm_kwargs
            )
            if not quiet:
                print('Executing remotely on {} ...'.format(self.ip()))
                styled_print(Style.DIM)(script)
            status, stdout, stderr = self._run_winrm_ps(winrm_session, script)
            if not quiet:
                styled_print(Style.BRIGHT)('CODE: {}'.format(status))
                styled_print(Fore.GREEN)(stdout)
            if status != 0:
                if not quiet:
                    styled_print(Fore.RED)(stderr)
                raise WinRmError(script, status, stdout, stderr)
            else:
                return status, stdout, stderr

    @configurable([
        ('Virtual Machine Remote Management', 'vcdriver_vm_winrm_username'),
        ('Virtual Machine Remote Management', 'vcdriver_vm_winrm_password')
    ])
    def winrm_upload(
            self,
            remote_path,
            local_path,
            step=1024,
            winrm_kwargs=dict(),
            quiet=False,
            **kwargs
    ):
        """
        Copy a file through winrm
        :param remote_path: The remote location
        :param local_path: The local local
        :param step: Number of bytes to send in each chunk
        :param winrm_kwargs: The pywinrm Protocol class kwargs
        :param quiet: Whether to hide the stdout/stderr output or not

        :return: A tuple with the status code, the stdout and the stderr
        """
        if self._vm_object:
            winrm_session = self._open_winrm_session(
                kwargs['vcdriver_vm_winrm_username'],
                kwargs['vcdriver_vm_winrm_password'],
                winrm_kwargs
            )
            self._run_winrm_ps(
                winrm_session,
                'if (Test-Path -path {0}) {{ Remove-Item -path {0} }}'.format(
                    remote_path)
            )
            size = os.stat(local_path).st_size
            start = time.time()
            with open(local_path, 'rb') as f:
                for i in range(0, size, step):
                    script = (
                        'add-content -value '
                        '$([System.Convert]::FromBase64String("{}")) '
                        '-encoding byte -path {}'.format(
                            base64.b64encode(f.read(step)).decode(),
                            remote_path
                        )
                    )
                    while True:
                        code, stdout, stderr = self._run_winrm_ps(
                            winrm_session, script
                        )
                        if time.time() - start >= self.timeout:
                            raise TimeoutError(
                                'WinRM upload file transfer', self.timeout
                            )
                        if code == 0:
                            break
                        elif code == 1 and 'used by another process' in stderr:
                            # Small delay so previous write can settle down
                            time.sleep(0.1)
                        else:
                            raise WinRmError(script, code, stdout, stderr)
                    if not quiet:
                        transferred = i + step
                        if transferred > size:
                            transferred = size
                        progress_blocks = transferred * 30 // size
                        percentage_string = str(
                            (100 * transferred) // size
                        ) + ' %'
                        percentage_string = (
                            ' ' * (5 - len(percentage_string)) +
                            percentage_string
                        )
                        print(
                            '\r{} ... [{}{}] {}'.format(
                                'Copying "{}" to "{}"'.format(
                                    local_path, remote_path
                                ),
                                '=' * progress_blocks,
                                ' ' * (30 - progress_blocks),
                                percentage_string
                            ),
                            end=''
                        )
                        sys.stdout.flush()
            if not quiet:
                print('')

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

    def set_autostart(self, start_delay=10):
        """ Set virtual machine ESXI autostart in a random order """
        if self._vm_object:
            host_default_settings = vim.host.AutoStartManager.SystemDefaults()
            host_default_settings.enabled = True
            host_default_settings.startDelay = start_delay
            esxi_host = self._vm_object.summary.runtime.host
            spec = esxi_host.configManager.autoStartManager.config
            spec.defaults = host_default_settings
            auto_power_info = vim.host.AutoStartManager.AutoPowerInfo()
            auto_power_info.key = self._vm_object
            auto_power_info.startAction = 'powerOn'
            auto_power_info.startDelay = -1
            auto_power_info.startOrder = -1
            auto_power_info.stopAction = 'None'
            auto_power_info.stopDelay = -1
            auto_power_info.waitForHeartbeat = 'no'
            spec.powerInfo = [auto_power_info]
            esxi_host.configManager.autoStartManager.ReconfigureAutostart(spec)

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

    def _open_winrm_session(self, username, password, winrm_kwargs):
        """
        Open a WinRM session
        :param username: The winrm username
        :param password: The winrm password
        :param winrm_kwargs: The pywinrm Protocol class kwargs

        :return: Return the winrm session
        """
        return winrm.Session(
            target=self.ip(),
            auth=(username, password),
            read_timeout_sec=self.timeout + 1,
            operation_timeout_sec=self.timeout,
            **winrm_kwargs
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

    def _wait_for_vmware_tools(self):
        """ Wait until vmware tools is ready """
        timeout_loop(
            self.timeout, 'Vmware tools readiness', 1, False,
            lambda: self._vm_object.summary.guest.toolsRunningStatus ==
            'guestToolsRunning'
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

    @staticmethod
    def _run_winrm_ps(pywinrm_session, script):
        """
        Run a powershell script
        :param pywinrm_session: The WinRM session
        :param script: The script to be run

        :return: A tuple with the status, stdout and stderr
        """
        result = pywinrm_session.run_ps(script)
        return (
            result.status_code,
            result.std_out.decode('ascii'),
            result.std_err.decode('ascii')
        )

    def _schedule_vcenter_task_on_vm(self, task, task_name, delay_by):
        """
        :param task: A vcenter task method
        :param task_description: The task description
        :param delay_by: if specified, it has to be a timedelta that indicates
            when in the future this task will be executed.
        """

        if not isinstance(delay_by, datetime.timedelta):
            raise TypeError(
                "Invalid type for delay_by. Expected datetime.timedelta."
            )

        spec = vim.scheduler.ScheduledTaskSpec()
        spec.name = task_name
        spec.description = ""
        spec.scheduler = vim.scheduler.OnceTaskScheduler()
        # it seems that CreateScheduledTask will add timezone without
        # converting it, so if you use utcnow here you may end up to
        # scheduling 1 hour in the past when BST is active
        spec.scheduler.runAt = datetime.datetime.now() + delay_by
        spec.action = vim.action.MethodAction()
        spec.action.name = task
        spec.enabled = True

        conn = connection()
        conn.content.scheduledTaskManager.CreateScheduledTask(
            self._vm_object, spec
        )

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

    def process(vm_object):
        try:
            name = vm_object.summary.config.name
        except vim.ManagedObjectNotFound:
            return None

        machine = VirtualMachine(name=name)
        machine._vm_object = vm_object
        return machine

    return [
        machine
        for vm_object in get_all_vcenter_objects(
            connection(), vim.VirtualMachine
        )
        for machine in (process(vm_object),)
        if machine is not None
    ]
