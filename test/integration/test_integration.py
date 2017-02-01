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
from vcdriver.folder import destroy_virtual_machines


class TestIntegration(unittest.TestCase):
    @staticmethod
    def touch(file_name):
        open(file_name, 'wb').close()

    @classmethod
    def setUpClass(cls):
        os.makedirs(os.path.join('dir-0', 'dir-1', 'dir-2'))
        cls.touch('file-0')
        cls.touch(os.path.join('dir-0', 'file-1'))
        cls.touch(os.path.join('dir-0', 'dir-1', 'file-2'))
        cls.touch(os.path.join('dir-0', 'dir-1', 'dir-2', 'file-3'))

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree('dir-0')
        except:
            pass
        try:
            shutil.rmtree('dir-0')
        except:
            pass

    def setUp(self):
        self.unix = VirtualMachine(
            name='test-integration-vcdriver-unix',
            template=os.getenv('VCDRIVER_TEST_UNIX_TEMPLATE'),
            folder=os.getenv('VCDRIVER_TEST_FOLDER')
        )
        self.windows = VirtualMachine(
            name='test-integration-vcdriver-windows',
            template=os.getenv('VCDRIVER_TEST_WINDOWS_TEMPLATE'),
            folder=os.getenv('VCDRIVER_TEST_FOLDER')
        )

    def tearDown(self):
        try:
            self.unix.destroy()
        except:
            pass
        try:
            self.windows.destroy()
        except:
            pass

    def test_idempotent_methods(self):
        for vm in [self.unix, self.windows]:
            with self.assertRaises(NoObjectFound):
                vm.find()
            with self.assertRaises(NoObjectFound):
                vm.find()
            self.assertIsNone(vm.__getattribute__('_vm_object'))
            vm.create()
            vm.create()
            self.assertIsNotNone(vm.__getattribute__('_vm_object'))
            vm.__setattr__('_vm_object', None)
            vm.find()
            vm.find()
            self.assertIsNotNone(vm.__getattribute__('_vm_object'))
            vm.destroy()
            vm.destroy()
            self.assertIsNone(vm.__getattribute__('_vm_object'))

    def test_context_manager(self):
        with self.assertRaises(NoObjectFound):
            self.unix.find()
        with self.assertRaises(NoObjectFound):
            self.windows.find()
        with virtual_machines([self.unix, self.windows]):
            self.unix.find()
            self.windows.find()
        with self.assertRaises(NoObjectFound):
            self.unix.find()
        with self.assertRaises(NoObjectFound):
            self.windows.find()

    def test_destroy_virtual_machines(self):
        self.unix.create()
        self.windows.create()
        vms = destroy_virtual_machines(os.getenv('VCDRIVER_TEST_FOLDER'))
        with self.assertRaises(NoObjectFound):
            vms[0].find()
        with self.assertRaises(NoObjectFound):
            vms[1].find()

    def test_ip(self):
        socket.inet_aton(self.unix.ip())
        socket.inet_aton(self.windows.ip())

    def test_ssh(self):
        self.assertEqual(self.unix.ssh('ls').return_code, 0)
        with self.assertRaises(SshError):
            self.unix.ssh('wrong-command-seriously')

    def test_upload_and_download(self):
        for vm in [self.unix, self.windows]:
            self.assertEqual(
                len(vm.upload(local_path='file-0', remote_path='file-0')), 1
            )
            self.assertEqual(
                len(vm.upload(local_path='file-0', remote_path='.')), 1
            )
            self.assertEqual(
                len(vm.upload(local_path='dir-0', remote_path='.')), 3
            )
            os.remove('file-0')
            shutil.rmtree('dir-0')
            self.assertEqual(
                len(vm.download(local_path='file-0', remote_path='file-0')), 1
            )
            self.assertEqual(
                len(vm.download(local_path='.', remote_path='file-0')), 1
            )
            self.assertEqual(
                len(vm.download(local_path='dir-0', remote_path='dir-0')), 3
            )
            self.assertEqual(
                len(vm.download(local_path='.', remote_path='dir-0')), 3
            )
            os.remove('file-0')
            shutil.rmtree('dir-0')
            with self.assertRaises(DownloadError):
                vm.download(local_path='file-0', remote_path='wrong-path')
            with self.assertRaises(UploadError):
                vm.upload(local_path='wrong-path', remote_path='file-0')
            with self.assertRaises(UploadError):
                vm.upload(local_path='dir-0', remote_path='wrong-path')
