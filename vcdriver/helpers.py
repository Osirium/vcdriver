from __future__ import print_function
import sys
import time
from pyVmomi import vim


def get_object(connection, object_type, name):
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
        raise IndexError(
            'Two or more objects of type {} with name "{}" were found'.format(
                count, object_type, name
            )
        )


def wait_for_task(task, task_description):
    print('Waiting on Vcenter task [{}] '.format(task_description), end='')
    start_time = time.time()
    state = task.info.state
    while state == vim.TaskInfo.State.running:
        wait(1)
        state = task.info.state
    if state == vim.TaskInfo.State.success:
        elapsed_time = time.time() - start_time
        print(' => Successfully run in {:.3f} seconds'.format(elapsed_time))
        return task.info.result
    else:
        print(' Failed')
        raise task.info.error


def wait(seconds):
    time.sleep(seconds)
    print('.', end='')
    sys.stdout.flush()
