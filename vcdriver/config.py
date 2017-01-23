from getpass import getpass
import os

# Session config
HOST = os.getenv('VCDRIVER_HOST')
PORT = os.getenv('VCDRIVER_PORT')
USERNAME = os.getenv('VCDRIVER_USERNAME')
PASSWORD = os.getenv('VCDRIVER_PASSWORD') or getpass('Vcenter password: ')

# Virtual machine config
DATA_CENTER = os.getenv('VCDRIVER_DATA_CENTER')
DATA_STORE = os.getenv('VCDRIVER_DATA_STORE')
RESOURCE_POOL = os.getenv('VCDRIVER_RESOURCE_POOL')
FOLDER = os.getenv('VCDRIVER_FOLDER')
