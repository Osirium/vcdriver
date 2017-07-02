import os
import shutil
import socket
import time

import pytest

from vcdriver.exceptions import (
    NoObjectFound,
    TooManyObjectsFound,
    DownloadError,
    UploadError,
    SshError,
    WinRmError,
    NotEnoughDiskSpace
)
from vcdriver.vm import (
    VirtualMachine,
    virtual_machines,
    snapshot,
    get_all_virtual_machines
)
from vcdriver.folder import destroy_virtual_machines
from vcdriver.config import load


def touch(file_name):
    open(file_name, 'wb').close()


@pytest.fixture(scope='module')
def files():
    os.makedirs(os.path.join('dir-0', 'dir-1', 'dir-2'))
    touch('file-0')
    touch(os.path.join('dir-0', 'file-1'))
    touch(os.path.join('dir-0', 'dir-1', 'file-2'))
    touch(os.path.join('dir-0', 'dir-1', 'dir-2', 'file-3'))
    yield
    try:
        shutil.rmtree('dir-0')
    except:
        pass
    try:
        os.remove('file-0')
    except:
        pass


@pytest.fixture(scope='function')
def vms():
    load(os.getenv('vcdriver_test_config_file'))
    unix = VirtualMachine(
        name='test-integration-vcdriver-unix',
        template=os.getenv('vcdriver_test_unix_template')
    )
    windows = VirtualMachine(
        name='test-integration-vcdriver-windows',
        template=os.getenv('vcdriver_test_windows_template')
    )
    vms = {'unix': unix, 'windows': windows}
    yield vms
    for vm in vms.values():
        try:
            vm.find()
            vm.destroy()
        except:
            pass


def test_create_delete(vms):
    for vm in vms.values():
        assert vm.__getattribute__('_vm_object') is None
        with pytest.raises(NotEnoughDiskSpace):
            vm.create(vcdriver_data_store_threshold=99)
        vm.create()
        assert vm.__getattribute__('_vm_object') is not None
        vm.create()
        assert vm.__getattribute__('_vm_object') is not None
        vm.destroy()
        assert vm.__getattribute__('_vm_object') is None
        vm.destroy()
        assert vm.__getattribute__('_vm_object') is None


def test_boot_methods(vms):
    with virtual_machines(vms.values()):
        for vm in vms.values():
            vm_object = vm.__getattribute__('_vm_object')
            assert vm_object.summary.runtime.powerState == 'poweredOn'
            vm.power_on()
            assert vm_object.summary.runtime.powerState == 'poweredOn'
            vm.power_off()
            time.sleep(1)
            assert vm_object.summary.runtime.powerState == 'poweredOff'
            vm.power_off()
            assert vm_object.summary.runtime.powerState == 'poweredOff'
            vm.power_on()
            vm.reset()
            time.sleep(20)  # Need some time to load vmware tools
            assert vm_object.summary.runtime.powerState == 'poweredOn'
            vm.shutdown()
            time.sleep(1)
            assert vm_object.summary.runtime.powerState == 'poweredOff'
            vm.shutdown()
            assert vm_object.summary.runtime.powerState == 'poweredOff'
            vm.power_on()
            time.sleep(20)  # Need some time to load vmware tools
            vm.reboot()
            time.sleep(20)  # Reboot is async and OS dependant
            assert vm_object.summary.runtime.powerState == 'poweredOn'


def test_virtual_machines(vms):
    for vm in vms.values():
        with pytest.raises(NoObjectFound):
            vm.find()
    with virtual_machines(vms.values()):
        for vm in vms.values():
            vm.find()
    for vm in vms.values():
        with pytest.raises(NoObjectFound):
            vm.find()


def test_get_all_virtual_machines(vms):
    vms['unix'].create()
    assert len(get_all_virtual_machines()) >= 1


def test_destroy_virtual_machines(vms):
    for vm in vms.values():
        vm.create()
    for vm in destroy_virtual_machines(os.getenv('vcdriver_test_folder')):
        with pytest.raises(NoObjectFound):
            vm.find()


def test_ip(vms):
    for vm in vms.values():
        vm.create()
        socket.inet_aton(vm.ip())


def test_ssh(vms):
    vms['unix'].create()
    assert vms['unix'].ssh('ls').return_code == 0
    with pytest.raises(SshError):
        vms['unix'].ssh('wrong-command-seriously')


def test_upload_and_download(files, vms):
    vms['unix'].create()
    assert len(
        vms['unix'].upload(local_path='file-0', remote_path='file-0')
    ) == 1
    assert len(vms['unix'].upload(local_path='file-0', remote_path='.')) == 1
    assert len(vms['unix'].upload(local_path='dir-0', remote_path='.')) == 3
    os.remove('file-0')
    shutil.rmtree('dir-0')
    assert len(
        vms['unix'].download(local_path='file-0', remote_path='file-0')
    ) == 1
    assert len(vms['unix'].download(local_path='.', remote_path='file-0')) == 1
    assert len(
        vms['unix'].download(local_path='dir-0', remote_path='dir-0')
    ) == 3
    assert len(vms['unix'].download(local_path='.', remote_path='dir-0')) == 3
    with pytest.raises(DownloadError):
        vms['unix'].download(local_path='file-0', remote_path='wrong-path')
    with pytest.raises(UploadError):
        vms['unix'].upload(local_path='dir-0', remote_path='wrong-path')


def test_winrm(vms):
    vms['windows'].create()
    vms['windows'].winrm('ipconfig /all', dict())
    with pytest.raises(WinRmError):
        vms['windows'].winrm('ipconfig-wrong /wrong', dict())


def test_snapshots(vms):
    snapshot_name = 'test_snapshot'
    for vm in vms.values():
        vm.create()
        with pytest.raises(NoObjectFound):
            vm.find_snapshot(snapshot_name)
        vm.create_snapshot(snapshot_name, True)
        with pytest.raises(TooManyObjectsFound):
            vm.create_snapshot(snapshot_name, True)
        vm.find_snapshot(snapshot_name)
    assert vms['unix'].ssh('touch banana').return_code == 0
    assert vms['unix'].ssh('ls') == 'banana'
    for vm in vms.values():
        vm.revert_snapshot(snapshot_name)
    assert vms['unix'].ssh('ls') == ''
    with snapshot(vms['unix']):
        vms['unix'].ssh('touch banana')
        assert vms['unix'].ssh('ls') == 'banana'
    assert vms['unix'].ssh('ls') == ''
