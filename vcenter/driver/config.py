import os

# Session config
HOST = os.getenv('VCENTER_HOST')
PORT = os.getenv('VCENTER_PORT')
USERNAME = os.getenv('VCENTER_USERNAME')
PASSWORD = os.getenv('VCENTER_PASSWORD')

# Virtual machine config
DATA_CENTER = os.getenv('VCENTER_DATA_CENTER')
DATA_STORE = os.getenv('VCENTER_DATA_STORE')
RESOURCE_POOL = os.getenv('VCENTER_RESOURCE_POOL')
