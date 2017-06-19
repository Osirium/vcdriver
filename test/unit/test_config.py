import os
import unittest

from six.moves import configparser

from vcdriver.config import load, configurable
from vcdriver.exceptions import MissingConfigValues


class TestConfig(unittest.TestCase):
    def require_nothing(self, **kwargs):
        pass

    @configurable([('Vsphere Session', 'vcdriver_username')])
    def require_username(self, vcdriver_username):
        pass

    @configurable([
        ('Vsphere Session', 'vcdriver_username'),
        ('Vsphere Session', 'vcdriver_password')
    ])
    def require_username_and_password(
            self, vcdriver_username, vcdriver_password
    ):
        pass

    @configurable([('Bad', 'Wrong')])
    def require_bad_section(self, **kwargs):
        pass

    @staticmethod
    def config_file(path, prepopulated_data=None):
        config = configparser.RawConfigParser()
        config.add_section('Vsphere Session')
        config.set('Vsphere Session', 'vcdriver_host', '')
        config.set('Vsphere Session', 'vcdriver_port', '')
        config.set('Vsphere Session', 'vcdriver_username', '')
        config.set('Vsphere Session', 'vcdriver_password', '')
        config.add_section('Virtual Machine Deployment')
        config.set(
            'Virtual Machine Deployment',
            'vcdriver_resource_pool',
            ''
        )
        config.set('Virtual Machine Deployment', 'vcdriver_data_store', '')
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

    @classmethod
    def setUpClass(cls):
        cls.config_file('config_file_1.cfg')
        cls.config_file(
            'config_file_2.cfg',
            [['Vsphere Session', 'vcdriver_username', 'Sinatra']]
        )
        cls.config_file(
            'config_file_3.cfg',
            [['Vsphere Session', 'vcdriver_password', 'myway']]
        )

    @classmethod
    def tearDownClass(cls):
        os.remove('config_file_1.cfg')
        os.remove('config_file_2.cfg')
        os.remove('config_file_3.cfg')

    def test_config(self):
        self.require_nothing()
        with self.assertRaises(MissingConfigValues):
            self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        load('config_file_1.cfg')
        self.require_nothing()
        with self.assertRaises(MissingConfigValues):
            self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        load()
        self.require_nothing()
        with self.assertRaises(MissingConfigValues):
            self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        os.environ['vcdriver_username'] = 'Sinatra'
        load()
        self.require_nothing()
        self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        os.environ['vcdriver_username'] = ''
        load()
        self.require_nothing()
        with self.assertRaises(MissingConfigValues):
            self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        load('config_file_2.cfg')
        self.require_nothing()
        self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        load()
        self.require_nothing()
        with self.assertRaises(MissingConfigValues):
            self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        os.environ['vcdriver_username'] = 'Sinatra'
        load('config_file_3.cfg')
        self.require_nothing()
        self.require_username()
        self.require_username_and_password()
        os.environ['vcdriver_username'] = ''
        load()
        self.require_nothing()
        with self.assertRaises(MissingConfigValues):
            self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        self.require_username_and_password(
            vcdriver_username='Sinatra',
            vcdriver_password='myway'
        )
        with self.assertRaises(MissingConfigValues):
            self.require_bad_section()
