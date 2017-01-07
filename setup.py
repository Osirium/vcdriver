from setuptools import setup, find_packages


setup(
    version='1.0.0',
    name='vcdriver',
    description='Vcenter driver for testing purposes',
    long_description=(
        "This is a vcenter driver for Python 2.7, based on pyvmomi.\n"
        "Adding this extra layer helps you drive your vcenter instance easier "
        "and it makes it a useful testing tool.\nThe ssh utility uses fabric, "
        "so it's limited to what fabric and ssh can do."
    ),
    url='https://github.com/Lantero/vcdriver',
    author='Carlos Ruiz Lantero',
    author_email='carlos.ruiz.lantero@gmail.com',
    license='MIT',
    install_requires=['fabric', 'pyvmomi'],
    packages=find_packages(),
)
