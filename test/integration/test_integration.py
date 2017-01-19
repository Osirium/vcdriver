import os
import shutil
import socket
import unittest

from vcdriver.exceptions import (
    NoObjectFound,
    DownloadError,
    UploadError,
    SshError
)
from vcdriver.vm import VirtualMachine, virtual_machines


class TestIntegrationProvisioning(unittest.TestCase):
    def setUp(self):
        self.vm = VirtualMachine(
            name='test-integration-vcdriver',
            template=os.getenv('VCDRIVER_TEST_TEMPLATE')
        )

    def test_idempotent_methods(self):
        with self.assertRaises(NoObjectFound):
            self.vm.find()
        with self.assertRaises(NoObjectFound):
            self.vm.find()
        self.assertIsNone(self.vm.__getattribute__('_vm_object'))
        self.vm.create()
        self.vm.create()
        self.assertIsNotNone(self.vm.__getattribute__('_vm_object'))
        self.vm.__setattr__('_vm_object', None)
        self.vm.find()
        self.vm.find()
        self.assertIsNotNone(self.vm.__getattribute__('_vm_object'))
        self.vm.destroy()
        self.vm.destroy()
        self.assertIsNone(self.vm.__getattribute__('_vm_object'))

    def test_context_manager(self):
        another_vm = VirtualMachine(
            name='another-test-integration-vcdriver',
            template=os.getenv('VCDRIVER_TEST_TEMPLATE')
        )
        with self.assertRaises(NoObjectFound):
            self.vm.find()
        with self.assertRaises(NoObjectFound):
            another_vm.find()
        with virtual_machines([self.vm, another_vm]):
            self.vm.find()
            another_vm.find()
        with self.assertRaises(NoObjectFound):
            self.vm.find()
        with self.assertRaises(NoObjectFound):
            another_vm.find()


class TestIntegrationNetworking(unittest.TestCase):
    @staticmethod
    def touch(file_name):
        open(file_name, 'wb').close()

    @classmethod
    def setUpClass(cls):
        cls.vm = VirtualMachine(
            name='test-integration-vcdriver',
            template=os.getenv('VCDRIVER_TEST_TEMPLATE'),
            ssh_username=os.getenv('VCDRIVER_TEST_SSH_USERNAME'),
            ssh_password=os.getenv('VCDRIVER_TEST_SSH_PASSWORD')
        )
        cls.vm.create()

    @classmethod
    def tearDownClass(cls):
        cls.vm.destroy()
        try:
            os.remove('file-0')
            shutil.rmtree('dir-0')
        except:
            pass

    def test_ip(self):
        socket.inet_aton(self.vm.ip())

    def test_ssh(self):
        self.assertEqual(self.vm.ssh('ls'), 0)
        with self.assertRaises(SshError):
            self.vm.ssh('wrong-command-seriously')

    def test_upload_and_download(self):
        os.makedirs(os.path.join('dir-0', 'dir-1', 'dir-2'))
        self.touch('file-0')
        self.touch(os.path.join('dir-0', 'file-1'))
        self.touch(os.path.join('dir-0', 'dir-1', 'file-2'))
        self.touch(os.path.join('dir-0', 'dir-1', 'dir-2', 'file-3'))
        self.assertEqual(
            len(self.vm.upload(local_path='file-0', remote_path='file-0')), 1
        )
        self.assertEqual(
            len(self.vm.upload(local_path='file-0', remote_path='.')), 1
        )
        self.assertEqual(
            len(self.vm.upload(local_path='dir-0', remote_path='.')), 3
        )
        os.remove('file-0')
        shutil.rmtree('dir-0')
        self.assertEqual(
            len(self.vm.download(local_path='file-0', remote_path='file-0')), 1
        )
        self.assertEqual(
            len(self.vm.download(local_path='.', remote_path='file-0')), 1
        )
        self.assertEqual(
            len(self.vm.download(local_path='dir-0', remote_path='dir-0')), 3
        )
        self.assertEqual(
            len(self.vm.download(local_path='.', remote_path='dir-0')), 3
        )
        os.remove('file-0')
        shutil.rmtree('dir-0')
        with self.assertRaises(DownloadError):
            self.vm.download(local_path='file-0', remote_path='wrong-path')
        with self.assertRaises(UploadError):
            self.vm.upload(local_path='wrong-path', remote_path='file-0')
        with self.assertRaises(UploadError):
            self.vm.upload(local_path='dir-0', remote_path='wrong-path')

