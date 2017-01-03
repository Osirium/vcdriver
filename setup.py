import os
from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


def src_requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()


def test_requirements():
    with open(os.path.join('test', 'requirements.txt')) as f:
        return f.read().splitlines()


setup(
    version='0.1.0',
    name='vcdriver',
    description='Vcenter driver for testing purposes',
    long_description=readme(),
    url='https://github.com/Lantero/vcdriver',
    author='Carlos Ruiz Lantero',
    author_email='carlos.ruiz.lantero@gmail.com',
    license='MIT',
    install_requires=src_requirements(),
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=test_requirements(),
)
