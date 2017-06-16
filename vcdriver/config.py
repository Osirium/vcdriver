import copy
import os
from six.moves import configparser

# FIXME: Deprecated
HOST = os.getenv('VCDRIVER_HOST')
PORT = os.getenv('VCDRIVER_PORT')
USERNAME = os.getenv('VCDRIVER_USERNAME')
PASSWORD = os.getenv('VCDRIVER_PASSWORD')
RESOURCE_POOL = os.getenv('VCDRIVER_RESOURCE_POOL')
DATA_STORE = os.getenv('VCDRIVER_DATA_STORE')
FOLDER = os.getenv('VCDRIVER_FOLDER')
VM_SSH_USERNAME = os.getenv('VCDRIVER_VM_SSH_USERNAME')
VM_SSH_PASSWORD = os.getenv('VCDRIVER_VM_SSH_PASSWORD')
VM_WINRM_USERNAME = os.getenv('VCDRIVER_VM_WINRM_USERNAME')
VM_WINRM_PASSWORD = os.getenv('VCDRIVER_VM_WINRM_PASSWORD')

_config = {
    'Vsphere Session': {
        'VCDRIVER_HOST': None,
        'VCDRIVER_PORT': None,
        'VCDRIVER_USERNAME': None,
        'VCDRIVER_PASSWORD': None
    },
    'Virtual Machine Deployment': {
        'VCDRIVER_RESOURCE_POOL': None,
        'VCDRIVER_DATA_STORE': None,
        'VCDRIVER_FOLDER': None
    },
    'Virtual Machine Remote Management': {
        'VCDRIVER_VM_SSH_USERNAME': None,
        'VCDRIVER_VM_SSH_PASSWORD': None,
        'VCDRIVER_VM_WINRM_USERNAME': None,
        'VCDRIVER_VM_WINRM_PASSWORD': None
    }
}


def create_config_file(path, **kwargs):
    """
    Create an empty configuration file
    :param path: The configuration file path
    :param kwargs: Any pre-populated values
    """
    config = configparser.RawConfigParser()
    for section_key, section_dict in _config.items():
        config.add_section(section_key)
        for subsection_key in section_dict.keys():
            if subsection_key in kwargs.keys():
                config.set(section_key, subsection_key, kwargs[subsection_key])
            else:
                config.set(section_key, subsection_key, '')
    with open(path, 'wb') as cf:
        config.write(cf)


def get():
    """ Return the current configuration values (Read only) """
    global _config
    return copy.deepcopy(_config)


def load(path=None):
    """
    Will load the configuration from a INI file, or the env otherwise
    :param path: The configuration file path
    """
    global _config
    if path:
        config = configparser.RawConfigParser()
        config.read(path)
    for section_key, section_dict in _config.items():
        for subsection_key in section_dict.keys():
            if path:
                _config[section_key][subsection_key] = config.get(
                    section_key, subsection_key
                ) or os.getenv(subsection_key)
            else:
                _config[section_key][subsection_key] = os.getenv(
                    subsection_key
                )


def reset():
    """ Reset all configuration values to None """
    global _config
    for section_key, section_dict in _config.items():
        for subsection_key in section_dict.keys():
            _config[section_key][subsection_key] = None
