[![Build Status](https://travis-ci.org/Lantero/vcenter-driver.svg?branch=master)](https://travis-ci.org/Lantero/vcenter-driver) [![codecov](https://codecov.io/gh/Lantero/vcenter-driver/branch/master/graph/badge.svg)](https://codecov.io/gh/Lantero/vcenter-driver)


This is a vcenter driver, based on pyvmomi. 
Adding this extra layer helps you drive your vcenter instance easier and it makes it a useful testing tool. 
The ssh utility uses fabric, so it's limited to what fabric and ssh can do.

### Installation
`python setup.py install`

### Configuration
* In order to communicate with your Vcenter instance, you need to provide the following environment variables:
    * VCENTER_HOST
    * VCENTER_PORT
    * VCENTER_USERNAME
    * VCENTER_PASSWORD
* Optionally, you can also specify defaults for some of the virtual machine creation parameters, if you don't
want to provide them with the class constructor method:
    * VCENTER_DATA_CENTER
    * VCENTER_DATA_STORE
    * VCENTER_RESOURCE_POOL


### Usage in a nutshell
Provided you have set all the environment variables from the previous section, you can try something like:
```python
from vcenter.driver.vm import VirtualMachine, virtual_machines

kwargs = {
    # If name is not provided, a unique UUID will be generated for you
    # 'name': 'Your VM custom name'
    'template': 'My Vcenter template',
    'ssh_username': 'user',  # Only necessary if you want to run ssh commands
    'ssh_password': 'pass'  # Only necessary if you want to run ssh commands
}
# These are lazy objects, you need to explicitly call their create 
# and destroy methods to actually create and destroy the boxes on Vcenter.
vm1 = VirtualMachine(**kwargs)
vm2 = VirtualMachine(**kwargs)

# This context manager will call the create and destroy methods for you even if 
# an exception is thrown internally, useful for testing
with virtual_machines([vm1, vm2]):
    vm1.ssh('apt-get update', use_sudo=True)
    vm1.ssh('echo "Hello from vm 1, my ip is {}"'.format(vm1.ip))
    vm2.ssh('echo "Hello from vm 2, my ip is {}"'.format(vm2.ip))
    raise KeyboardInterrupt
```
