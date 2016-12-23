from setuptools import setup, find_packages

setup(
    name='vcenter-driver',
    version='0.1.0',
    description='Vcenter driver for testing purposes',
    author='Carlos Ruiz Lantero',
    author_email='carlos.ruiz.lantero@gmail.com',
    install_requires=['fabric', 'pyvmomi==6.5'],
    packages=find_packages(),
)
