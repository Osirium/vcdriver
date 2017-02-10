from __future__ import print_function
import datetime
import socket
import sys
import time

from colorama import init, Style
from pyVmomi import vim

from vcdriver.exceptions import (
    TooManyObjectsFound,
    NoObjectFound,
    TimeoutError,
    IpError
)


init()


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
    print(
        'Retrieving Vcenter object of type "{}" with name "{}" ... '.format(
            object_type, name
        ),
        end=''
    )
    sys.stdout.flush()
    start = time.time()
    content = connection.RetrieveContent()
    view = content.viewManager.CreateContainerView
    objects = [
        obj for obj in view(content.rootFolder, [object_type], True).view
        if hasattr(obj, 'name') and obj.name == name
    ]
    count = len(objects)
    if count == 1:
        print(datetime.timedelta(seconds=time.time() - start))
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


def timeout_loop(
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
    print('Waiting for [{}] ... '.format(description), end='')
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


def wait_for_vcenter_task(task, task_description, timeout):
    """
    Wait for a vcenter task to finish
    :param task: A vcenter task object
    :param task_description: The task description
    :param timeout: The timeout, in seconds

    :return: The task result

    :raise: TimeoutError: If the timeout is reached
    """
    timeout_loop(
        timeout=timeout,
        description=task_description,
        callback=lambda: task.info.state != vim.TaskInfo.State.running,
    )
    if task.info.state == vim.TaskInfo.State.success:
        return task.info.result
    else:
        if task.info.error is not None:
            raise task.info.error
