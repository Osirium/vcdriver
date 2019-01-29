.. image:: https://badge.fury.io/py/vcdriver.svg
  :target: https://badge.fury.io/py/vcdriver

.. image:: https://travis-ci.org/Lantero/vcdriver.svg?branch=master
  :target: https://travis-ci.org/Lantero/vcdriver

.. image:: https://codecov.io/gh/Lantero/vcdriver/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/Lantero/vcdriver

.. image:: https://img.shields.io/packagist/l/doctrine/orm.svg?style=flat
  :target: https://github.com/Lantero/vcdriver

*****
About
*****

Vcdriver is a wrapper around pyvmomi that lets you manage virtual machines on your Vsphere in an easy way.

- Create, find or destroy virtual machines.

- Power on/off, shutdown, reboot and reset them.

- Snapshot management.

- Remote management:

  - SSH protocol for remote commands (Requires the SSH service).
  - SFTP protocol for file transfers (Requires the SSH service).
  - WinRM protocol for remote commands and file transfer on Windows machines (Requires the WinRM service).

How does it work underneath?
============================

- Vsphere is driven using its official python API, `pyvmomi <https://github.com/vmware/pyvmomi>`_.

- The virtual machines are manipulated with `Fabric3 <https://pypi.python.org/pypi/Fabric3>`_ and
  `pywinrm <https://pypi.python.org/pypi/pywinrm>`_.

- It currently supports Python **2.7**, **3.4**, **3.5** and **3.6**.

- It works with latest versions of Vsphere, **6.0** and **6.5**.

Why would I use vcdriver instead of using pyvmomi directly?
===========================================================

Pyvmomi is powerful but its learning curve is overkill for most of the tasks you might want to
execute programmatically with Vsphere. All the complexity has been abstracted out so you can do
in 5 lines of vcdriver code what you would do in 50 lines of pyvmomi code.
That makes your testing and automation scripts way easier to read and maintain.

************
Installation
************

.. code-block::

  pip install vcdriver

*************
Documentation
*************

Documentation and examples can be found on the `wiki <https://github.com/Osirium/vcdriver/wiki>`_.

*******
Testing
*******

Prepare your python environment: ``pip install -e . && pip install pytest pytest-cov mock``.

Unit tests
==========

#. Run ``pytest -v --cov=vcdriver --cov-fail-under 100 test/unit``.

Integration tests
=================

As you might expect, the unit tests can only test the logic of the driver, as all the vcenter components have to be mocked out.
You can run some integration tests to check it works fine for your Vsphere instance. To do so:

#. You need the following Vsphere resources:

   - An empty folder which will serve as a sandbox environment for the tests.
   - A Unix virtual machine template with the SSH service allowing remote username/password SSH/SFTP connections.
   - A Windows Server virtual machine template with the WinRM service allowing remote username/password WinRM connections.
     The ansible people have done a great job about this, and you can set it up with their script:
     `ConfigureRemotingForAnsible.ps1 <https://github.com/ansible/ansible/blob/devel/examples/scripts/ConfigureRemotingForAnsible.ps1>`_.

#. Read through the `setup section <https://github.com/Osirium/vcdriver/wiki/Example-1>`_ and create your configuration file.

#. Provide the following extra environment variables:

   - ``vcdriver_test_config_file``: The path to your file config.
   - ``vcdriver_test_unix_template``: The name of the UNIX virtual machine template that will be cloned for the tests.
   - ``vcdriver_test_windows_template``: The name of the Windows Server virtual machine template that will be cloned for the tests.
   - ``vcdriver_test_folder``: An empty vm folder to perform the tests in it.

#. Run ``pytest -v -s test/integration``.
