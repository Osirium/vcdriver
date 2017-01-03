from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    version='0.1.0',
    name='vcenter-driver',
    description='Vcenter driver for testing purposes',
    long_description=readme(),
    url='https://github.com/Lantero/vcenter-driver',
    author='Carlos Ruiz Lantero',
    author_email='carlos.ruiz.lantero@gmail.com',
    license='MIT',
    install_requires=['fabric', 'pyvmomi'],
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=['nose'],
)
