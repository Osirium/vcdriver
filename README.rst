.. image:: https://badge.fury.io/py/vcdriver.svg
    :target: https://badge.fury.io/py/vcdriver

.. image:: https://travis-ci.org/Lantero/vcdriver.svg?branch=master
  :target: https://travis-ci.org/Lantero/vcdriver

.. image:: https://codecov.io/gh/Lantero/vcdriver/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/Lantero/vcdriver

About
=====

This project started from the need of using Vcenter for testing purposes, although it can also be used to manage your Vcenter instance for other general tasks.

How does it work underneath?
============================

- Vcenter is driven using its official python API, `pyvmomi <https://github.com/vmware/pyvmomi>`_.
- The virtual machines are manipulated with `fabric <https://github.com/fabric/fabric>`_.
- It currently supports Python **2.7**, **3.3**, **3.4**, **3.5** and **3.6**.
    
Why would I use vcdriver instead of using pyvmomi and fabric directly?
======================================================================

- **Simplicity**: Write tests or scripts that are both easy to write and read. Pyvmomi is powerful, but its learning curve is overkill for most of the tasks you might want to execute programatically with Vcenter.
- **Maintainability**: If your Vcenter and pyvmomi versions get out of sync and something stops working, you don't need to change every single test or script you have, you just need to change the internal implementation of the driver.

Installation
============

.. code-block::

  pip install vcdriver

Documentation
=============

Documentation and examples can be found on the `wiki <https://github.com/Lantero/vcdriver/wiki>`_.

A note about the tests
======================

As you might expect, the unit tests can only test the logic of the driver, as all the vcenter components have to be mocked out.
You can run some integration tests to check it works fine for your Vcenter instance. To do so:

1. Read through the configuration section on the `wiki <https://github.com/Lantero/vcdriver/wiki>`_.
2. Provide some extra environment variables:

  - `VCDRIVER_TEST_FOLDER`: The name of the folder that will be used for the tests (Vms will be deleted inside this folder).
  - `VCDRIVER_TEST_TEMPLATE`: The name of the virtual machine template (UNIX-like) that will be cloned for the tests.
  - `VCDRIVER_TEST_SSH_USERNAME`: The username that will ssh into that virtual machine.
  - `VCDRIVER_TEST_SSH_PASSWORD`: The password for the ssh user.

3. Run `nosetests test/integration`.
