from getpass import getpass
import os

# Python2-3 compatibility
try:                    # pragma: no cover
    input = raw_input   # pragma: no cover
except NameError:       # pragma: no cover
    pass                # pragma: no cover

# Session config
HOST = os.getenv('VCDRIVER_HOST') or input('Vcenter host: ')
PORT = os.getenv('VCDRIVER_PORT') or input('Vcenter port: ')
USERNAME = os.getenv('VCDRIVER_USERNAME') or input('Vcenter username: ')
PASSWORD = os.getenv('VCDRIVER_PASSWORD') or getpass('Vcenter password: ')

# Virtual machine config
DATA_CENTER = os.getenv('VCDRIVER_DATA_CENTER') or input(
    'Vcenter data center: '
)
DATA_STORE = os.getenv('VCDRIVER_DATA_STORE') or input('Vcenter data store: ')
RESOURCE_POOL = os.getenv('VCDRIVER_RESOURCE_POOL') or input(
    'Vcenter resource pool: '
)
FOLDER = os.getenv('VCDRIVER_FOLDER') or input('Vcenter folder: ')
