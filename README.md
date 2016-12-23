This is a vcenter driver, based on pyvmomi. Adding this extra layer helps you drive your vcenter instance easier and it makes it a useful testing tool. The ssh part is based on fabric.

### Installation
`python setup.py install`

### Configuration
In order to communicate with your Vcenter instance, you need to provide these environment variables:
* VCENTER_HOST
* VCENTER_PORT
* VCENTER_USERNAME
* VCENTER_PASSWORD

You will be prompted for them if you don't provide them.

### Usage in a nutshell
```python
from vcenter.driver.vm import VirtualMachine, virtual_machines

# This is a lazy instance, you need to explicitely call its create 
# and destroy methods to actually create and destroy the box on Vcenter.
vm = VirtualMachine(
    name='The name of your virtual machine'  # Optional, a uuid will be generated for you as a default
    template='Target template name'
    data_center='Target data center name'
    data_store='Target data store name'
    resource_pool='Target resource pool name'
    ssh_username='user'  # Optional, only if you want to run ssh commands
    ssh_username='password'  # Optional, only if you want to run ssh commands
)

# This will call the create and destroy methods for you even if 
# an exception is thrown internally, useful for testing
with virtual_machines([vm]):
    print('The ip is {}'.format(vm.ip))
    vm.ssh('echo "Hello world"')
```
