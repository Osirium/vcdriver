import os
import unittest

from vcdriver.config import create_config_file, get, load, reset


class TestConfig(unittest.TestCase):
    maxDiff = None
    @classmethod
    def setUpClass(cls):
        cls.config_file_1 = 'config_file_1.cfg'
        cls.config_file_2 = 'config_file_2.cfg'
        cls.config_file_3 = 'config_file_3.cfg'
        create_config_file(cls.config_file_1)
        create_config_file(cls.config_file_2, VCDRIVER_USERNAME='Sinatra')
        create_config_file(cls.config_file_3, VCDRIVER_PASSWORD='myway')

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.config_file_1)
        os.remove(cls.config_file_2)
        os.remove(cls.config_file_3)

    def test_create_get_load_reset(self):
        state_1 = get()
        state_2 = get()
        state_2['Vsphere Session']['VCDRIVER_USERNAME'] = 'Sinatra'
        state_3 = get()
        state_3['Vsphere Session']['VCDRIVER_USERNAME'] = 'Sinatra'
        state_3['Vsphere Session']['VCDRIVER_PASSWORD'] = 'myway'
        self.assertEqual(get(), state_1)
        load(self.config_file_1)
        self.assertEqual(get(), state_1)
        reset()
        self.assertEqual(get(), state_1)
        os.environ['VCDRIVER_USERNAME'] = 'Sinatra'
        load()
        self.assertEqual(get(), state_2)
        reset()
        self.assertEqual(get(), state_1)
        load(self.config_file_2)
        self.assertEqual(get(), state_2)
        reset()
        self.assertEqual(get(), state_1)
        os.environ['VCDRIVER_USERNAME'] = 'Sinatra'
        load(self.config_file_3)
        self.assertEqual(get(), state_3)
        reset()
        self.assertEqual(get(), state_1)
