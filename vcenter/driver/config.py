from getpass import getpass
import os


HOST = os.getenv('VCENTER_HOST') or raw_input('Vcenter host: ')
PORT = os.getenv('VCENTER_PORT') or raw_input('Vcenter port: ')
USERNAME = os.getenv('VCENTER_USERNAME') or raw_input('Vcenter user: ')
PASSWORD = os.getenv('VCENTER_PASSWORD') or getpass('Vcenter password: ')
