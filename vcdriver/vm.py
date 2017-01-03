from __future__ import print_function
from contextlib import contextmanager
from fabric.api import sudo, run
from fabric.context_managers import settings
from pyVmomi import vim

import config
from auth import Session
from helpers import get_object, wait_for_task, wait


class VirtualMachine(object):
    def __init__(
            self,
            template,
            data_center=config.DATA_CENTER,
            data_store=config.DATA_STORE,
            resource_pool=config.RESOURCE_POOL,
            name=None,
            ssh_username=None,
            ssh_password=None
    ):
        self.template = template
        self.data_center = data_center
        self.data_store = data_store
        self.resource_pool = resource_pool
        self.name = name
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.session = None
        self.vm_object = None
        self.ip = None

    def create(self):
        if not self.vm_object:
            self.session = Session()
            if not self.name:
                self.name = self.session.id
            connection = self.session.connection
            spec = vim.vm.CloneSpec(
                location=vim.vm.RelocateSpec(
                    datastore=get_object(
                        connection, vim.Datastore, self.data_store
                    ),
                    pool=get_object(
                        connection, vim.ResourcePool, self.resource_pool
                    )
                ),
                powerOn=True,
                template=False
            )
            self.vm_object = wait_for_task(
                get_object(
                    connection, vim.VirtualMachine, self.template
                ).CloneVM_Task(
                    folder=get_object(
                        connection, vim.Datacenter, self.data_center
                    ).vmFolder,
                    name=self.name,
                    spec=spec
                ),
                "Create virtual machine '{}' from template '{}'".format(
                    self.name, self.template
                )
            )
            print(
                "Virtual machine '{}' waiting on the DHCP server ".format(
                    self.name
                ),
                end=''
            )
            while not self.vm_object.summary.guest.ipAddress:
                wait(1)
            self.ip = self.vm_object.summary.guest.ipAddress
            print(' {}'.format(self.ip))

    def destroy(self):
        if self.vm_object:
            wait_for_task(
                self.vm_object.PowerOffVM_Task(),
                "Power off virtual machine '{}'".format(self.name)
            )
            wait_for_task(
                self.vm_object.Destroy_Task(),
                "Destroy virtual machine '{}'".format(self.name)
            )
            self.session = None
            self.vm_object = None
            self.ip = None

    def ssh(self, command, use_sudo=False):
        with settings(
                user=self.ssh_username,
                password=self.ssh_password,
                host_string="{}@{}".format(self.ssh_username, self.ip),
                warn_only=True
        ):
            if use_sudo:
                result = sudo(command)
            else:
                result = run(command)
            if result.failed:
                raise RuntimeError(
                    "Command '{}' failed with exit code {}".format(
                        command, result.return_code
                    )
                )


@contextmanager
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
