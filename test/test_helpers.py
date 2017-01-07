import mock
import unittest

from vcdriver import helpers


class ErrorMock(Exception):
    pass


class VcenterObjectMock(object):
    def __init__(self, name):
        self.name = name


class TestHelpers(unittest.TestCase):
    def test_get_object(self):
        connnection_mock = mock.MagicMock()
        content_mock = mock.MagicMock
        setattr(connnection_mock, 'RetrieveContent', content_mock)
        setattr(content_mock, 'content', mock.MagicMock())
        setattr(content_mock.content, 'viewManager', mock.MagicMock())
        setattr(
            content_mock.content.viewManager,
            'CreateContainerView',
            mock.MagicMock
        )
        apple = VcenterObjectMock('apple')
        orange_1 = VcenterObjectMock('orange')
        orange_2 = VcenterObjectMock('orange')
        setattr(
            content_mock.content.viewManager.CreateContainerView,
            'view',
            [apple, orange_1, orange_2]
        )
        self.assertEqual(
            helpers.get_object(connnection_mock, VcenterObjectMock, 'apple'),
            apple
        )
        self.assertEqual(
            helpers.get_object(connnection_mock, VcenterObjectMock, 'grapes'),
            None
        )
        with self.assertRaises(IndexError):
            helpers.get_object(connnection_mock, VcenterObjectMock, 'orange')

    @mock.patch('vcdriver.helpers.vim.TaskInfo.State.success')
    def test_wait_for_task_success(self, success_state):
        task_mock = mock.MagicMock()
        setattr(task_mock, 'info', mock.MagicMock)
        setattr(task_mock.info, 'state', success_state)
        setattr(task_mock.info, 'result', 'whatever')
        self.assertEqual(
            'whatever', helpers.wait_for_task(task_mock, 'my task', 600)
        )

    def test_wait_for_task_fail(self):
        task_mock = mock.MagicMock()
        setattr(task_mock, 'info', mock.MagicMock)
        setattr(task_mock.info, 'state', 'failure')
        setattr(task_mock.info, 'error', ErrorMock)
        with self.assertRaises(ErrorMock):
            helpers.wait_for_task(task_mock, 'my task', 600)

    @mock.patch('vcdriver.helpers.vim.TaskInfo.State.running')
    def test_wait_for_task_timeout(self, running_state):
        task_mock = mock.MagicMock()
        setattr(task_mock, 'info', mock.MagicMock)
        setattr(task_mock.info, 'state', running_state)
        with self.assertRaises(RuntimeError):
            helpers.wait_for_task(task_mock, 'my task', 1)

