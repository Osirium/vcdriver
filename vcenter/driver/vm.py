from __future__ import print_function
from contextlib import contextmanager
from fabric.api import sudo
from fabric.context_managers import settings
from pyVmomi import vim
from uuid import uuid1

from auth import get_connection
from helpers import get_object, wait_for_task, wait


class VirtualMachine(object):
    def __init__(
            self, template, data_center, data_store, resource_pool,
            name=str(uuid1()), ssh_username=None, ssh_password=None
    ):
        self.template = template
        self.data_center = data_center
        self.data_store = data_store
        self.resource_pool = resource_pool
        self.name = name
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.connection = None
        self.vm_object = None
        self.ip = None

    def create(self):
        self.connection = get_connection()
        spec = vim.vm.CloneSpec(
            location=vim.vm.RelocateSpec(
                datastore=get_object(
                    self.connection, vim.Datastore, self.data_store
                ),
                pool=get_object(
                    self.connection, vim.ResourcePool, self.resource_pool
                )
            ),
            powerOn=True,
            template=False
        )
        self.vm_object = wait_for_task(
            get_object(
                self.connection, vim.VirtualMachine, self.template
            ).CloneVM_Task(
                folder=get_object(
                    self.connection, vim.Datacenter, self.data_center
                ).vmFolder,
                name=self.name,
                spec=spec
            ),
            "Create virtual machine '{}' from template '{}'".format(
                self.name, self.template
            )
        )
        print("'{}' waiting on the DHCP server ".format(self.name), end='')
        while not self.vm_object.summary.guest.ipAddress:
            wait(1)
        self.ip = self.vm_object.summary.guest.ipAddress
        print(' {}'.format(self.ip))

    def destroy(self):
        wait_for_task(
            self.vm_object.PowerOffVM_Task(),
            "Power off virtual machine '{}'".format(self.name)
        )
        wait_for_task(
            self.vm_object.Destroy_Task(),
            "Destroy virtual machine '{}'".format(self.name)
        )

    def ssh(self, command):
        with settings(
                user=self.ssh_username,
                password=self.ssh_password,
                host_string="{}@{}".format(self.ssh_username, self.ip),
                warn_only=True
        ):
            result = sudo(command)
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
        for vm in vms:
            vm.destroy()
        raise
