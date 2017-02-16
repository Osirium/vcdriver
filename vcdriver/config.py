import getpass
import os

# Session config
HOST = os.getenv('VCDRIVER_HOST')
PORT = os.getenv('VCDRIVER_PORT')
USERNAME = os.getenv('VCDRIVER_USERNAME')
PASSWORD = os.getenv('VCDRIVER_PASSWORD') or getpass.getpass(
    'Enter your password for Vcenter: '
)

# Virtual machine config
RESOURCE_POOL = os.getenv('VCDRIVER_RESOURCE_POOL')
DATA_STORE = os.getenv('VCDRIVER_DATA_STORE')
FOLDER = os.getenv('VCDRIVER_FOLDER')
VM_SSH_USERNAME = os.getenv('VCDRIVER_VM_SSH_USERNAME')
VM_SSH_PASSWORD = os.getenv('VCDRIVER_VM_SSH_PASSWORD')
VM_WINRM_USERNAME = os.getenv('VCDRIVER_VM_WINRM_USERNAME')
VM_WINRM_PASSWORD = os.getenv('VCDRIVER_VM_WINRM_PASSWORD')
