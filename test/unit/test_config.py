import os

import mock
import pytest
from six.moves import configparser

from vcdriver.config import load, configurable, read, reset


def require_nothing(**kwargs):
    pass


@configurable([('Vsphere Session', 'vcdriver_username')])
def require_username(vcdriver_username):
    pass


@configurable([
    ('Vsphere Session', 'vcdriver_username'),
    ('Vsphere Session', 'vcdriver_password')
])
def require_username_and_password(
        vcdriver_username, vcdriver_password
):
    pass


@configurable([('Bad', 'Wrong')])
def require_bad_section(**kwargs):
    pass


def config_file(path, prepopulated_data=None):
    config = configparser.RawConfigParser()
    config.add_section('Vsphere Session')
    config.set('Vsphere Session', 'vcdriver_host', '')
    config.set('Vsphere Session', 'vcdriver_port', '443')
    config.set('Vsphere Session', 'vcdriver_username', '')
    config.set('Vsphere Session', 'vcdriver_password', '')
    config.add_section('Virtual Machine Deployment')
    config.set(
        'Virtual Machine Deployment',
        'vcdriver_resource_pool',
        ''
    )
    config.set('Virtual Machine Deployment', 'vcdriver_data_store', '')
    config.set(
        'Virtual Machine Deployment',
        'vcdriver_data_store_threshold',
        '0'
    )
    config.set('Virtual Machine Deployment', 'vcdriver_folder', '')
    config.add_section('Virtual Machine Remote Management')
    config.set(
        'Virtual Machine Remote Management',
        'vcdriver_vm_ssh_username',
        ''
    )
    config.set(
        'Virtual Machine Remote Management',
        'vcdriver_vm_ssh_password',
        ''
    )
    config.set(
        'Virtual Machine Remote Management',
        'vcdriver_vm_winrm_username',
        ''
    )
    config.set(
        'Virtual Machine Remote Management',
        'vcdriver_vm_winrm_password',
        ''
    )
    if prepopulated_data:
        for section, key, value in prepopulated_data:
            config.set(section, key, value)
    with open(path, 'w') as cf:
        config.write(cf)


@pytest.fixture(scope='module')
def config_files():
    config_file('config_file_1.cfg')
    config_file(
        'config_file_2.cfg',
        [['Vsphere Session', 'vcdriver_username', 'Sinatra']]
    )
    config_file(
        'config_file_3.cfg',
        [['Vsphere Session', 'vcdriver_password', 'myway']]
    )
    yield
    os.remove('config_file_1.cfg')
    os.remove('config_file_2.cfg')
    os.remove('config_file_3.cfg')


def test_read(config_files):
    assert read() == {
        'Vsphere Session': {
            'vcdriver_host': '',
            'vcdriver_port': '443',
            'vcdriver_username': '',
            'vcdriver_password': ''
        },
        'Virtual Machine Deployment': {
            'vcdriver_resource_pool': '',
            'vcdriver_data_store': '',
            'vcdriver_data_store_threshold': '0',
            'vcdriver_folder': ''
        },
        'Virtual Machine Remote Management': {
            'vcdriver_vm_ssh_username': '',
            'vcdriver_vm_ssh_password': '',
            'vcdriver_vm_winrm_username': '',
            'vcdriver_vm_winrm_password': ''
        }
    }
    load('config_file_3.cfg')
    assert read() == {
        'Vsphere Session': {
            'vcdriver_host': '',
            'vcdriver_port': '443',
            'vcdriver_username': '',
            'vcdriver_password': 'myway'
        },
        'Virtual Machine Deployment': {
            'vcdriver_resource_pool': '',
            'vcdriver_data_store': '',
            'vcdriver_data_store_threshold': '0',
            'vcdriver_folder': ''
        },
        'Virtual Machine Remote Management': {
            'vcdriver_vm_ssh_username': '',
            'vcdriver_vm_ssh_password': '',
            'vcdriver_vm_winrm_username': '',
            'vcdriver_vm_winrm_password': ''
        }
    }


def test_configurable_and_reset(config_files):
    load()
    require_nothing()
    with mock.patch('vcdriver.config.input') as input_mock:
        require_username()
        input_mock.assert_called_once()
    reset()
    with mock.patch('vcdriver.config.input') as input_mock:
        with mock.patch('vcdriver.config.getpass.getpass') as getpass_mock:
            require_username_and_password()
            input_mock.assert_called_once()
            getpass_mock.assert_called_once()
    load('config_file_1.cfg')
    require_nothing()
    with mock.patch('vcdriver.config.input') as input_mock:
        require_username()
        input_mock.assert_called_once()
    reset()
    with mock.patch('vcdriver.config.input') as input_mock:
        with mock.patch('vcdriver.config.getpass.getpass') as getpass_mock:
            require_username_and_password()
            input_mock.assert_called_once()
            getpass_mock.assert_called_once()
    load()
    require_nothing()
    with mock.patch('vcdriver.config.input') as input_mock:
        require_username()
        input_mock.assert_called_once()
    reset()
    with mock.patch('vcdriver.config.input') as input_mock:
        with mock.patch('vcdriver.config.getpass.getpass') as getpass_mock:
            require_username_and_password()
            input_mock.assert_called_once()
            getpass_mock.assert_called_once()
    os.environ['vcdriver_username'] = 'Sinatra'
    load()
    require_nothing()
    require_username()
    with mock.patch('vcdriver.config.input') as input_mock:
        with mock.patch('vcdriver.config.getpass.getpass') as getpass_mock:
            require_username_and_password()
            getpass_mock.assert_called_once()
    os.environ['vcdriver_username'] = ''
    load()
    require_nothing()
    with mock.patch('vcdriver.config.input') as input_mock:
        require_username()
        input_mock.assert_called_once()
    reset()
    with mock.patch('vcdriver.config.input') as input_mock:
        with mock.patch('vcdriver.config.getpass.getpass') as getpass_mock:
            require_username_and_password()
            input_mock.assert_called_once()
            getpass_mock.assert_called_once()
    load('config_file_2.cfg')
    require_nothing()
    require_username()
    with mock.patch('vcdriver.config.input') as input_mock:
        with mock.patch('vcdriver.config.getpass.getpass') as getpass_mock:
            require_username_and_password()
            getpass_mock.assert_called_once()
    reset()
    load()
    require_nothing()
    with mock.patch('vcdriver.config.input') as input_mock:
        require_username()
        input_mock.assert_called_once()
    reset()
    with mock.patch('vcdriver.config.input') as input_mock:
        with mock.patch('vcdriver.config.getpass.getpass') as getpass_mock:
            require_username_and_password()
            input_mock.assert_called_once()
            getpass_mock.assert_called_once()
    os.environ['vcdriver_username'] = 'Sinatra'
    load('config_file_3.cfg')
    require_nothing()
    require_username()
    require_username_and_password()
    os.environ['vcdriver_username'] = ''
    load()
    require_nothing()
    reset()
    with mock.patch('vcdriver.config.input') as input_mock:
        require_username()
        input_mock.assert_called_once()
    reset()
    with mock.patch('vcdriver.config.input') as input_mock:
        with mock.patch('vcdriver.config.getpass.getpass') as getpass_mock:
            require_username_and_password()
            input_mock.assert_called_once()
            getpass_mock.assert_called_once()
    require_username_and_password(
        vcdriver_username='Sinatra',
        vcdriver_password='myway'
    )
    reset()
    with mock.patch('vcdriver.config.input') as input_mock:
        with pytest.raises(KeyError):
            require_bad_section()
        input_mock.assert_called_once()
