import functools
import os
from six.moves import configparser

from vcdriver.exceptions import MissingConfigValues

# FIXME: Deprecated (Remove)
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
# End of FIXME

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


def load(path=None):
    """
    Will load the configuration from a INI file or the environment
    :param path: The configuration file path
    """
    global _config
    if path:
        config = configparser.RawConfigParser()
        config.read(path)
    for section_key, section_content in _config.items():
        for config_key in section_content.keys():
            if path:
                _config[section_key][config_key] = config.get(
                    section_key, config_key
                ) or os.getenv(config_key)
            else:
                _config[section_key][config_key] = os.getenv(config_key)


def required(section_keys):
    """
    Ensure that a configuration value is present in the kwargs or the config
    :param section_keys: An iterable of the required section-key pairs

    :return: The decorated function

    :raise: MissingConfigValues: If any configuration values are missing
    """
    global _config

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            missing_keys = []
            for section, key in section_keys:
                if not kwargs.get(key, None):
                    config_section = _config.get(section)
                    if config_section:
                        config_value = config_section.get(key)
                    else:
                        config_value = None
                    if config_value:
                        kwargs[key] = config_value
                    else:
                        missing_keys.append(key)
            if missing_keys:
                raise MissingConfigValues(missing_keys)
            return function(*args, **kwargs)
        return wrapper
    return decorator
