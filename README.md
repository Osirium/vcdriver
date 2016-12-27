This is a vcenter driver, based on pyvmomi. 
Adding this extra layer helps you drive your vcenter instance easier and it makes it a useful testing tool. 
The ssh utility uses fabric, so it's obviously limited to what fabric and ssh can do.

### Installation
`python setup.py install`

### Configuration
* In order to communicate with your Vcenter instance, you need to provide the following environment variables.
You will be prompted for them otherwise:
    * VCENTER_HOST
    * VCENTER_PORT
    * VCENTER_USERNAME
    * VCENTER_PASSWORD
* Optionally, you can also specify defaults for most of the virtual machine creation parameters:
    * VCENTER_DATA_CENTER
    * VCENTER_DATA_STORE
    * VCENTER_RESOURCE_POOL


### Usage in a nutshell
Provided you have set all the environment variables from the previous section, you can try something like:
```python
from vcenter.driver.vm import VirtualMachine, virtual_machines

kwargs = {
    'template': 'My Vcenter template',
    'ssh_username': 'user',
    'ssh_password': 'pass'
}
# These are lazy objects, you need to explicitely call their create 
# and destroy methods to actually create and destroy the boxes on Vcenter.
vm1 = VirtualMachine(**kwargs)
vm2 = VirtualMachine(**kwargs)

# This context manager will call the create and destroy methods for you even if 
# an exception is thrown internally, useful for testing
with virtual_machines([vm1, vm2]):
    vm1.ssh('echo "Hello from vm 1, my ip is {}"'.format(vm1.ip))
    vm2.ssh('echo "Hello from vm 2, my ip is {}"'.format(vm2.ip))
    raise KeyboardInterrupt
```
