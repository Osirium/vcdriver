from __future__ import print_function
import contextlib
import datetime
import os
import socket
import sys
import time

from colorama import init, Style
from fabric.api import run
from fabric.context_managers import settings
from pyVmomi import vim, vmodl
import winrm

from vcdriver.exceptions import (
    TooManyObjectsFound,
    NoObjectFound,
    TimeoutError,
    IpError
)


init()


def get_all_vcenter_objects(connection, object_type):
    """
    Return all the vcenter objects of a given type
    :param connection: A vcenter connection
    :param object_type:  A vcenter object type, like vim.VirtualMachine

    :return: A list with all the objects found
    """
    print(
        'Retrieving all Vcenter objects of type "{}" ... '.format(object_type),
        end=''
    )
    sys.stdout.flush()
    start = time.time()
    content = connection.RetrieveContent()
    view = content.viewManager.CreateContainerView
    objects = [
        obj for obj in view(content.rootFolder, [object_type], True).view
    ]
    print(datetime.timedelta(seconds=time.time() - start))
    return objects


def get_vcenter_object_by_name(connection, object_type, name):
    """
    Find a vcenter object
    :param connection: A vcenter connection
    :param object_type: A vcenter object type, like vim.VirtualMachine
    :param name: The name of the object

    :return: The object found

    :raise: TooManyObjectsFound: If more than one object is found
    :raise: NoObjectFound: If no results are found
    """
    content = connection.RetrieveContent()
    view = content.viewManager.CreateContainerView

    def name_matches(obj):
        try:
            return obj.name == name
        except (vmodl.fault.ManagedObjectNotFound, AttributeError):
            pass
        return False

    objects = [
        obj for obj in view(content.rootFolder, [object_type], True).view
        if name_matches(obj)
    ]
    count = len(objects)
    if count == 1:
        return objects[0]
    elif count > 1:
        raise TooManyObjectsFound(object_type, name)
    else:
        raise NoObjectFound(object_type, name)


def styled_print(styles):
    """
    Generate a function that prints a message with a given style
    :param styles: The colorama styles to be applied e.g. colorama.Fore.RED

    :return: The print function
    """
    return lambda msg: print(''.join(styles) + msg + Style.RESET_ALL)


@contextlib.contextmanager
def hide_std():
    stdout = sys.stdout
    stderr = sys.stderr
    with open(os.devnull, 'w') as null:
        sys.stdout = sys.stderr = null
        try:
            yield
        finally:
            sys.stdout = stdout
            sys.stderr = stderr


def timeout_loop(
        timeout, description, seconds_until_retry, quiet,
        callback, *callback_args, **callback_kwargs
):
    """
    Wait inside a blocking loop for a task to complete
    :param timeout: The timeout, in seconds
    :param description: The task description
    :param seconds_until_retry: Seconds before re-checking the callback
    :param quiet: If true, the benchmark time will not be printed
    :param callback: If this function is True, the while loop will break
    :param callback_args: The positional arguments of the callback
    :param callback_kwargs: The keyword arguments of the callback

    :raise: TimeoutError: If the timeout is reached
    """
    error = None
    if not quiet:
        print('Waiting for [{}] ... '.format(description), end='')
        sys.stdout.flush()
    countdown = timeout
    start = time.time()
    while countdown >= 0:
        callback_start = time.time()
        try:
            if callback(*callback_args, **callback_kwargs):
                break
        except Exception as e:
            error = e
        callback_time = time.time() - callback_start
        time.sleep(seconds_until_retry)
        countdown = countdown - seconds_until_retry - callback_time
    if countdown <= 0:
        if error:
            description = '{}. {}'.format(description, str(error))
        raise TimeoutError(description, timeout)
    if not quiet:
        print(datetime.timedelta(seconds=time.time() - start))


def validate_ip(ip):
    """
    Try to validate an ip against ipv4 and ipv6
    :param ip: The target ip

    :return: A dictionary with the ip and the ip version

    :raise IpError: If the ip is not valid
    """
    if validate_ipv4(ip):
        return {'ip': ip, 'version': 4}
    elif validate_ipv6(ip):
        return {'ip': ip, 'version': 6}
    else:
        raise IpError(ip)


def validate_ipv4(ip):
    """
    Validate an ipv4 address
    :param ip: The string with the ip

    :return: True ip if it's valid for ipv4, False otherwise
    """
    ip = str(ip)
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except AttributeError:
        try:
            socket.inet_aton(ip)
        except socket.error:
            return False
    except socket.error:
        return False
    return True


def validate_ipv6(ip):
    """
    Validate an ipv6 address
    :param ip: The string with the ip

    :return: True ip if it's valid for ipv6, False otherwise
    """
    ip = str(ip)
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False
    return True


_TERMINAL_STATES = frozenset(
    (vim.TaskInfo.State.success, vim.TaskInfo.State.error))


def wait_for_vcenter_task(task, task_description, timeout, _poll_interval=1):
    """
    Wait for a vcenter task to finish
    :param task: A vcenter task object
    :param task_description: The task description
    :param timeout: The timeout, in seconds

    :return: The task result

    :raise: TimeoutError: If the timeout is reached
    """
    timeout_loop(
        timeout, task_description, _poll_interval, False,
        callback=lambda: task.info.state in _TERMINAL_STATES,
    )
    if task.info.state == vim.TaskInfo.State.success:
        return task.info.result
    else:
        if task.info.error is not None:
            raise task.info.error


@contextlib.contextmanager
def fabric_context(host, username, password):
    """
    Set the ssh context for fabric
    :param host: SSH host
    :param username: SSH username
    :param password: SSH password
    """
    ip_version = validate_ip(host)['version']
    if ip_version == 6:
        host = '[{}]'.format(host)
    with settings(
            host_string="{}@{}".format(username, host),
            password=password,
            warn_only=True,
            disable_known_hosts=True
    ):
        yield


def check_ssh_service(host, username, password):
    """
    Check whether the ssh service is up or not on the target host
    :param host: SSH host
    :param username: SSH username
    :param password: SSH password
    """
    with hide_std():
        with fabric_context(host, username, password):
            run('')
    return True


def check_winrm_service(host, username, password, **kwargs):
    """
    Check whether the winrm service is up or not on the target host
    :param host: WinRM host
    :param username: WinRM username
    :param password: WinRM password
    :param kwargs: pywinrm Protocol kwargs
    """
    with hide_std():
        winrm.Session(host, (username, password), **kwargs).run_ps('ls')
    return True
