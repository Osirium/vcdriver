from setuptools import setup, find_packages


setup(
    version='1.1.6',
    name='vcdriver',
    description='A vcenter driver based on pyvmomi and fabric',
    url='https://github.com/Lantero/vcdriver',
    author='Carlos Ruiz Lantero',
    author_email='carlos.ruiz.lantero@gmail.com',
    license='MIT',
    install_requires=['Fabric3', 'pyvmomi'],
    packages=find_packages(),
)
