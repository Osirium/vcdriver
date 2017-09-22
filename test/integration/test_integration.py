import hashlib
import os
import shutil
import socket
import sys

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
from vcdriver.helpers import timeout_loop


def touch(file_name):
    with open(file_name, 'wb') as f:
        f.write(b'\0' * 1024 * 5)  # 5 kb file


def wait_for_power_state_or_die(vm_object, state):
    timeout_loop(
        30, '', 1, True, lambda: vm_object.summary.runtime.powerState == state
    )


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
            wait_for_power_state_or_die(vm_object, 'poweredOn')
            assert vm_object.summary.runtime.powerState == 'poweredOn'
            vm.power_on()
            wait_for_power_state_or_die(vm_object, 'poweredOn')
            assert vm_object.summary.runtime.powerState == 'poweredOn'
            vm.power_off()
            wait_for_power_state_or_die(vm_object, 'poweredOff')
            assert vm_object.summary.runtime.powerState == 'poweredOff'
            vm.power_off()
            wait_for_power_state_or_die(vm_object, 'poweredOff')
            assert vm_object.summary.runtime.powerState == 'poweredOff'
            vm.power_on()
            vm.reset()
            wait_for_power_state_or_die(vm_object, 'poweredOn')
            assert vm_object.summary.runtime.powerState == 'poweredOn'
            vm.shutdown()
            wait_for_power_state_or_die(vm_object, 'poweredOff')
            assert vm_object.summary.runtime.powerState == 'poweredOff'
            vm.shutdown()
            wait_for_power_state_or_die(vm_object, 'poweredOff')
            assert vm_object.summary.runtime.powerState == 'poweredOff'
            vm.power_on()
            vm.reboot()
            wait_for_power_state_or_die(vm_object, 'poweredOn')
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


def test_autostart(vms):
    for vm in vms.values():
        vm.set_autostart()


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


def test_winrm(files, vms):
    vms['windows'].create()
    vms['windows'].winrm('ipconfig /all')
    # FIXME:
    # Due to this pywinrm bug: https://github.com/diyan/pywinrm/issues/111
    # we need to split the integration tests depending on the major version
    # Python 2: Everything works as expected
    # Python 3: Failed scripts throw TypeError instead of WinRmError
    # Python 3: WinRM upload does not work :(
    if sys.version_info[0] == 2:
        with pytest.raises(WinRmError):
            vms['windows'].winrm('ipconfig-wrong /wrong')
        vms['windows'].winrm_upload(
            local_path='file-0',
            remote_path='C:\\file-0'
        )
        with open('file-0', 'rb') as f:
            expected_sha256 = hashlib.sha256(f.read()).hexdigest().upper()
        _, resulted_sha256, _ = vms['windows'].winrm(
            '$(Get-FileHash -Algorithm SHA256 C:\\file-0).hash'
        )
        assert expected_sha256 == str(resulted_sha256.strip())
    elif sys.version_info[0] == 3:
        with pytest.raises(TypeError):
            vms['windows'].winrm('ipconfig-wrong /wrong')

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
