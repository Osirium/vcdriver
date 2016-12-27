from getpass import getpass
import os

# Session config
HOST = os.getenv('VCENTER_HOST') or raw_input('Vcenter host: ')
PORT = os.getenv('VCENTER_PORT') or raw_input('Vcenter port: ')
USERNAME = os.getenv('VCENTER_USERNAME') or raw_input('Vcenter user: ')
PASSWORD = os.getenv('VCENTER_PASSWORD') or getpass('Vcenter password: ')

# Virtual machine config
DATA_CENTER = os.getenv('VCENTER_DATA_CENTER') or raw_input(
    'Vcenter data center: '
)
DATA_STORE = os.getenv('VCENTER_DATA_STORE') or raw_input(
    'Vcenter data store: '
)
RESOURCE_POOL = os.getenv('VCENTER_RESOURCE_POOL') or raw_input(
    'Vcenter resource pool: '
)
