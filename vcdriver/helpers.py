from __future__ import print_function
import contextlib
import datetime
import sys
import time

from fabric.api import run
from fabric.context_managers import settings
from pyVmomi import vim
import winrm

from vcdriver.exceptions import (
    TooManyObjectsFound,
    NoObjectFound,
    TimeoutError
)


@contextlib.contextmanager
def fabric_context(username, password, ip):
    """
    Set the ssh context for fabric
    :param username: The user
    :param password: The password
    :param ip: The target machine ip
    """
    with settings(
            host_string="{}@{}".format(username, ip),
            password=password,
            warn_only=True,
            disable_known_hosts=True
    ):
        yield


def get_vcenter_object(connection, object_type, name):
    """
    Find a vcenter object
    :param connection: A vcenter connection
    :param object_type: A vcenter object type, like vim.Folder
    :param name: The name of the object

    :return: The object found

    :raise: TooManyObjectsFound: If more than one object is found
    :raise: NoObjectFound: If no results are found
    """
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


def wait_for_vcenter_task(task, task_description, timeout):
    """
    Wait for a vcenter task to finish
    :param task: A vcenter task object
    :param task_description: The task description
    :param timeout: The timeout, in seconds

    :return: The task result

    :raise: TimeoutError: If the timeout is reached
    """
    _timeout_loop(
        timeout=timeout,
        description=task_description,
        callback=lambda: task.info.state != vim.TaskInfo.State.running,
    )
    if task.info.state == vim.TaskInfo.State.success:
        return task.info.result
    else:
        raise task.info.error


def wait_for_dhcp_service(vm_object, timeout):
    """
    Wait for the virtual machine to have an IP
    :param vm_object: A vcenter virtual machine object
    :param timeout: The timeout, in seconds

    :return: The virtual machine IP

    :raise: TimeoutError: If the timeout is reached
    """
    _timeout_loop(
        timeout=timeout,
        description='Get IP',
        callback=lambda: vm_object.summary.guest.ipAddress
    )
    return vm_object.summary.guest.ipAddress


def wait_for_ssh_service(username, password, ip, timeout):
    """
    Wait until the SSH service is ready
    :param username: The username
    :param password: The password
    :param ip: The target ip
    :param timeout: The timeout, in seconds
    """
    _timeout_loop(
        username=username,
        password=password,
        ip=ip,
        timeout=timeout,
        description='Check SSH service',
        callback=_check_sshservice
    )


def wait_for_winrm_service(username, password, ip, timeout, **kwargs):
    """
    Wait until the WinRM service is ready
    :param username: The username
    :param password: The password
    :param ip: The target ip
    :param timeout: The timeout, in seconds
    :param kwargs: pywinrm Protocol kwargs
    """
    _timeout_loop(
        username=username,
        password=password,
        ip=ip,
        timeout=timeout,
        description='Check WinRM service',
        callback=_check_winrm_service,
        **kwargs
    )


def _timeout_loop(
        timeout, description, callback, wait_until_retry=1, *args, **kwargs
):
    """
    Wait inside a blocking loop for a task to complete
    :param timeout: The timeout, in seconds
    :param description: The task description
    :param callback: If this function is True, the while loop will break
    :param wait_until_retry: Seconds you wait before re-checking the callback
    :param args: The positional arguments of the callback
    :param kwargs: The keyword arguments of the callback

    :raise: TimeoutError: If the timeout is reached
    """
    print('Waiting on [{}] ... '.format(description), end='')
    sys.stdout.flush()
    countdown = timeout
    start = time.time()
    while countdown >= 0:
        callback_start = time.time()
        if callback(*args, **kwargs):
            break
        callback_time = time.time() - callback_start
        time.sleep(wait_until_retry)
        countdown = countdown - wait_until_retry - callback_time
    if countdown <= 0:
        raise TimeoutError(description, timeout)
    print(datetime.timedelta(seconds=time.time() - start))


def _check_sshservice(username, password, ip):
    """
    Check whether the ssh service is up or not
    :param username: The user
    :param password: The password
    :param ip: The target ip

    :return: True if ready, False otherwise
    """
    try:
        with fabric_context(username, password, ip):
            run('')
            return True
    except:
        return False


def _check_winrm_service(username, password, ip, **kwargs):
    """
    Check whether the winrm service is up or not
    :param username: The user
    :param password: The password
    :param ip: The target ip
    :param kwargs: pywinrm Protocol kwargs

    :return: True if ready, False otherwise
    """
    try:
        winrm.Session(
            target=ip, auth=(username, password), **kwargs
        ).run_cmd('')
        return True
    except:
        return False
