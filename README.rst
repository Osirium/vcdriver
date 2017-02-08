.. image:: https://badge.fury.io/py/vcdriver.svg
  :target: https://badge.fury.io/py/vcdriver

.. image:: https://travis-ci.org/Lantero/vcdriver.svg?branch=master
  :target: https://travis-ci.org/Lantero/vcdriver

.. image:: https://codecov.io/gh/Lantero/vcdriver/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/Lantero/vcdriver

About
=====

Vcdriver is a wrapper around pyvmomi that lets you create, find and destroy virtual machines on your
Vcenter/Vsphere instance. It also lets you manage those virtual machines:

- SSH protocol for remote commands (Only for Unix, Requires the SSH service)
- SFTP protocol for file transfers (Only for Unix, Requires the SSH service)
- WinRM protocol for remote commands on Windows machines (Only for Windows, requires the WinRM service)

How does it work underneath?
============================

- Vcenter is driven using its official python API, `pyvmomi <https://github.com/vmware/pyvmomi>`_.
- The virtual machines are manipulated with `Fabric3 <https://pypi.python.org/pypi/Fabric3>`_ and
  `pywinrm <https://pypi.python.org/pypi/pywinrm>`_.
- It currently supports Python **2.7**, **3.3**, **3.4**, **3.5** and **3.6**.
    
Why would I use vcdriver instead of using pyvmomi directly?
===========================================================

- **Simplicity**: Write tests or scripts that are both easy to write and read. Pyvmomi is powerful, but its
  learning curve is overkill for most of the tasks you might want to execute programatically with Vcenter.
- **Maintainability**: If your Vcenter and pyvmomi versions get out of sync and something stops working, you don't
  need to change every single test or script you have, you just need to update the driver.

Installation
============

.. code-block::

  pip install vcdriver

Documentation
=============

Documentation and examples can be found on the `wiki <https://github.com/Lantero/vcdriver/wiki>`_.

Unit tests
==========

Just run ``nosetests -v test/unit``.

Integration tests
=================

As you might expect, the unit tests can only test the logic of the driver, as all the vcenter components have to be mocked out.
You can run some integration tests to check it works fine for your Vcenter instance. To do so:

1. Read through the configuration section on the `wiki <https://github.com/Lantero/vcdriver/wiki>`_.
2. You need the following Vcenter resources:

  - An empty folder which will serve as a sandbox environment for the tests.
  - A Unix virtual machine template with the SSH service allowing remote username/password SSH/SFTP connections.
  - A Windows Server virtual machine template with the WinRM service allowing remote username/password WinRM connections.
    This might not be non-trivial, so here is a snippet you can run on the CMD console to set it up on a Windows Server 2012,
    which probably works for other versions too. Remember this is not a production config, you can read a bit more about different
    WinRM setups on the `wiki <https://github.com/Lantero/vcdriver/wiki>`_.

    .. code-block::

      winrm quickconfig
      winrm set winrm/config/client/auth @{Basic="true"}
      winrm set winrm/config/service/auth @{Basic="true"}
      winrm set winrm/config/service @{AllowUnencrypted="true"}

3. Provide the following environment variables:

  - ``VCDRIVER_TEST_FOLDER``: The name of the sandbox folder that will be used for the tests.
  - ``VCDRIVER_TEST_UNIX_TEMPLATE``: The name of the UNIX virtual machine template that will be cloned for the tests.
  - ``VCDRIVER_TEST_UNIX_USERNAME``: The username for the UNIX machine.
  - ``VCDRIVER_TEST_UNIX_PASSWORD``: The password for the UNIX machine.
  - ``VCDRIVER_TEST_WINDOWS_TEMPLATE``: The name of the Windows Server virtual machine template that will be cloned for the tests.
  - ``VCDRIVER_TEST_WINDOWS_USERNAME``: The username for the Windows machine.
  - ``VCDRIVER_TEST_WINDOWS_PASSWORD``: The password for the Windows machine.

4. Run ``nosetests -v test/integration``.
