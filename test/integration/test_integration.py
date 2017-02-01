import os
import shutil
import socket
import unittest

from vcdriver.exceptions import (
    NoObjectFound,
    DownloadError,
    UploadError,
    SshError,
    WinRmError
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
            os.remove('file-0')
        except:
            pass

    def setUp(self):
        self.unix = VirtualMachine(
            name='test-integration-vcdriver-unix',
            template=os.getenv('VCDRIVER_TEST_UNIX_TEMPLATE'),
            folder=os.getenv('VCDRIVER_TEST_FOLDER'),
            username=os.getenv('VCDRIVER_TEST_UNIX_USERNAME'),
            password=os.getenv('VCDRIVER_TEST_UNIX_PASSWORD')
        )
        self.windows = VirtualMachine(
            name='test-integration-vcdriver-windows',
            template=os.getenv('VCDRIVER_TEST_WINDOWS_TEMPLATE'),
            folder=os.getenv('VCDRIVER_TEST_FOLDER'),
            username=os.getenv('VCDRIVER_TEST_WINDOWS_USERNAME'),
            password=os.getenv('VCDRIVER_TEST_WINDOWS_PASSWORD')
        )
        self.all_vms = [self.unix, self.windows]

    def tearDown(self):
        for vm in self.all_vms:
            try:
                vm.destroy()
            except:
                pass

    def test_idempotent_methods(self):
        for vm in self.all_vms:
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
        for vm in self.all_vms:
            with self.assertRaises(NoObjectFound):
                vm.find()
        with virtual_machines(self.all_vms):
            for vm in self.all_vms:
                vm.find()
        for vm in self.all_vms:
            with self.assertRaises(NoObjectFound):
                vm.find()

    def test_destroy_virtual_machines(self):
        for vm in self.all_vms:
            vm.create()
        for vm in destroy_virtual_machines(os.getenv('VCDRIVER_TEST_FOLDER')):
            with self.assertRaises(NoObjectFound):
                vm.find()

    def test_ip(self):
        for vm in self.all_vms:
            vm.create()
            socket.inet_aton(vm.ip())

    def test_ssh(self):
        self.unix.create()
        self.assertEqual(self.unix.ssh('ls').return_code, 0)
        with self.assertRaises(SshError):
            self.unix.ssh('wrong-command-seriously')

    def test_winrm_cmd_and_ps(self):
        self.windows.create()
        self.windows.winrm_cmd('ipconfig', '/all')
        with self.assertRaises(WinRmError):
            self.windows.winrm_cmd('ipconfig-wrong', '/all')
        # TODO: Test winrm_ps

    def test_upload_and_download(self):
        for vm in self.all_vms:
            vm.create()
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
            with self.assertRaises(DownloadError):
                vm.download(local_path='file-0', remote_path='wrong-path')
            with self.assertRaises(UploadError):
                vm.upload(local_path='dir-0', remote_path='wrong-path')
