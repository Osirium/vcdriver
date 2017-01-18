.. image:: https://travis-ci.org/Lantero/vcdriver.svg?branch=master
  :target: https://travis-ci.org/Lantero/vcdriver

.. image:: https://codecov.io/gh/Lantero/vcdriver/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/Lantero/vcdriver

About
=====

This project started from the need of using Vcenter for testing purposes, 
although it can also be used to manage your Vcenter instance.

- **How does it work underneath?**

  - Vcenter is driven using its official python API, `pyvmomi <https://github.com/vmware/pyvmomi>`_.
  - The virtual machines are manipulated with `fabric <https://github.com/fabric/fabric>`_.
  - It currently supports Python **2.7**, **3.3**, **3.4**, **3.5** and **3.6**.
    
- **Why would I use vcdriver instead of using pyvmomi and fabric directly?**

  - **Simplicity**: Write tests or scripts that are both easy to write and read. Pyvmomi is powerful, but its learning curve is overkill for most of the tasks you might want to execute programatically with Vcenter.
  - **Maintainability**: If your Vcenter and pyvmomi versions get out of sync and something stops working, you don't need to change every single test or script you have, you just need to change the internal implementation of the driver.

Installation
============

.. code-block::

  pip install vcdriver

Documentation
=============

Documentation and examples can be found on the `wiki <https://github.com/Lantero/vcdriver/wiki>`_.


