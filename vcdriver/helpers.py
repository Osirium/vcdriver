from __future__ import print_function
import contextlib
import datetime
import sys
import time

from fabric.context_managers import settings
from pyVmomi import vim

from vcdriver.exceptions import (
    TooManyObjectsFound,
    NoObjectFound,
    TimeoutError
)


def get_vcenter_object(connection, object_type, name):
    content = connection.RetrieveContent()
    view = content.viewManager.CreateContainerView
    objects = [
        obj for obj in view(content.rootFolder, [object_type], True).view
        if hasattr(obj, 'name') and obj.name == name
    ]
    count = len(objects)
    if count == 1:
        return objects[0]
    elif count > 1:
        raise TooManyObjectsFound(object_type, name)
    else:
        raise NoObjectFound(object_type, name)


def wait_for_vcenter_task(task, task_description, timeout=600, step=1):
    _timeout_loop(
        description=task_description,
        callback=lambda: task.info.state == vim.TaskInfo.State.running,
        timeout=timeout,
        step=step
    )
    if task.info.state == vim.TaskInfo.State.success:
        return task.info.result
    else:
        raise task.info.error


def wait_for_dhcp_server(vm_object, timeout=120, step=1):
    _timeout_loop(
        description='Get IP',
        callback=lambda: not vm_object.summary.guest.ipAddress,
        timeout=timeout,
        step=step
    )
    return vm_object.summary.guest.ipAddress


@contextlib.contextmanager
def ssh_context(username, password, ip):
    with settings(
            host_string="{}@{}".format(username, ip),
            password=password,
            warn_only=True,
            disable_known_hosts=True
    ):
        yield


def _timeout_loop(description, callback, timeout, step, *args, **kwargs):
    start = time.time()
    print('Waiting on [{}] ... '.format(description), end='')
    sys.stdout.flush()
    while callback(*args, **kwargs) and timeout:
        time.sleep(step)
        timeout -= step
    if not timeout:
        raise TimeoutError(description, timeout)
    print(datetime.timedelta(seconds=time.time() - start))
