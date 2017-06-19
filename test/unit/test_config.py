import os
import unittest

from six.moves import configparser

from vcdriver.config import load, configurable
from vcdriver.exceptions import MissingConfigValues


class TestConfig(unittest.TestCase):
    def require_nothing(self, **kwargs):
        pass

    @configurable([('Vsphere Session', 'VCDRIVER_USERNAME')])
    def require_username(self, **kwargs):
        pass

    @configurable([
        ('Vsphere Session', 'VCDRIVER_USERNAME'),
        ('Vsphere Session', 'VCDRIVER_PASSWORD')
    ])
    def require_username_and_password(self, **kwargs):
        pass

    @configurable([('Bad', 'Wrong')])
    def require_bad_section(self, **kwargs):
        pass

    @staticmethod
    def config_file(path, prepopulated_data=None):
        config = configparser.RawConfigParser()
        config.add_section('Vsphere Session')
        config.set('Vsphere Session', 'VCDRIVER_HOST', '')
        config.set('Vsphere Session', 'VCDRIVER_PORT', '')
        config.set('Vsphere Session', 'VCDRIVER_USERNAME', '')
        config.set('Vsphere Session', 'VCDRIVER_PASSWORD', '')
        config.add_section('Virtual Machine Deployment')
        config.set(
            'Virtual Machine Deployment',
            'VCDRIVER_RESOURCE_POOL',
            ''
        )
        config.set('Virtual Machine Deployment', 'VCDRIVER_DATA_STORE', '')
        config.set('Virtual Machine Deployment', 'VCDRIVER_FOLDER', '')
        config.add_section('Virtual Machine Remote Management')
        config.set(
            'Virtual Machine Remote Management',
            'VCDRIVER_VM_SSH_USERNAME',
            ''
        )
        config.set(
            'Virtual Machine Remote Management',
            'VCDRIVER_VM_SSH_PASSWORD',
            ''
        )
        config.set(
            'Virtual Machine Remote Management',
            'VCDRIVER_VM_WINRM_USERNAME',
            ''
        )
        config.set(
            'Virtual Machine Remote Management',
            'VCDRIVER_VM_WINRM_PASSWORD',
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
            [['Vsphere Session', 'VCDRIVER_USERNAME', 'Sinatra']]
        )
        cls.config_file(
            'config_file_3.cfg',
            [['Vsphere Session', 'VCDRIVER_PASSWORD', 'myway']]
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
        os.environ['VCDRIVER_USERNAME'] = 'Sinatra'
        load()
        self.require_nothing()
        self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        os.environ['VCDRIVER_USERNAME'] = ''
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
        os.environ['VCDRIVER_USERNAME'] = 'Sinatra'
        load('config_file_3.cfg')
        self.require_nothing()
        self.require_username()
        self.require_username_and_password()
        os.environ['VCDRIVER_USERNAME'] = ''
        load()
        self.require_nothing()
        with self.assertRaises(MissingConfigValues):
            self.require_username()
        with self.assertRaises(MissingConfigValues):
            self.require_username_and_password()
        self.require_username_and_password(
            VCDRIVER_USERNAME='Sinatra',
            VCDRIVER_PASSWORD='myway'
        )
        with self.assertRaises(MissingConfigValues):
            self.require_bad_section()
