from setuptools import setup, find_packages


setup(
    version='1.1.3',
    name='vcdriver',
    description='Vcenter driver for testing purposes',
    long_description=(
        "This is a vcenter driver, based on pyvmomi.\n"
        "Adding this extra layer helps you drive your vcenter instance easier "
        "and it makes it a useful testing tool.\nThe ssh, download, and "
        "upload utilities use fabric underneath."
    ),
    url='https://github.com/Lantero/vcdriver',
    author='Carlos Ruiz Lantero',
    author_email='carlos.ruiz.lantero@gmail.com',
    license='MIT',
    install_requires=['Fabric3', 'pyvmomi'],
    packages=find_packages(),
)
