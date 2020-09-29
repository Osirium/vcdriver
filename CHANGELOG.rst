Change Log
==========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`__
and this project adheres to `Semantic
Versioning <http://semver.org/>`__.

5.1.2rc1 (unreleased)
---------------------

- Nothing changed yet.


[4.3.0] - 2018-07-06
--------------------

Changed
~~~~~~~

-  Timeout loop function now displays last exception traceback when
   timing out

.. _section-1:

[4.2.0] - 2018-06-15
--------------------

Added
~~~~~

-  Added created_at property to know when the vm was created

.. _section-2:

[4.0.0] - 2017-10-10
--------------------

.. _changed-1:

Changed
~~~~~~~

-  Upload and download functions renamed to ssh_upload and ssh_download

.. _added-1:

Added
~~~~~

-  Quiet mode for SSH and WinRM functions

.. _section-3:

[3.7.3] - 2017-10-03
--------------------

.. _changed-2:

Changed
~~~~~~~

-  Improve winrm_upload function
-  Better output in RemoteCommandError exceptions

.. _section-4:

[3.7.2] - 2017-10-02
--------------------

.. _changed-3:

Changed
~~~~~~~

-  Improve winrm_upload function

.. _section-5:

[3.7.1] - 2017-09-28
--------------------

.. _changed-4:

Changed
~~~~~~~

-  Improve integration tests
-  Fix vm default name

.. _section-6:

[3.7.0] - 2017-09-22
--------------------

.. _changed-5:

Changed
~~~~~~~

-  Fix several WinRM issues

.. _section-7:

[3.6.0] - 2017-09-22
--------------------

.. _added-2:

Added
~~~~~

-  WinRM upload file function

.. _section-8:

[3.5.2] - 2017-09-04
--------------------

.. _changed-6:

Changed
~~~~~~~

-  Add default to winrm kwargs

.. _section-9:

[3.5.1] - 2017-08-31
--------------------

.. _changed-7:

Changed
~~~~~~~

-  Fix configuration defaults being deleted when loading configuration
-  Fix configuration input being repeatedly prompted to the user

.. _section-10:

[3.5.0] - 2017-08-25
--------------------

.. _added-3:

Added
~~~~~

-  Autostart function for virtual machines

.. _section-11:

[3.4.0] - 2017-08-18
--------------------

.. _changed-8:

Changed
~~~~~~~

-  Fix python3 winrm function by decoding stdout and stderr

.. _section-12:

[3.3.5] - 2017-08-18
--------------------

.. _changed-9:

Changed
~~~~~~~

-  Fix python3 winrm function running empty script

.. _section-13:

[3.3.4] - 2017-08-17
--------------------

.. _changed-10:

Changed
~~~~~~~

-  Fix python3 compatibility issue with the hide std function

.. _section-14:

[3.3.3] - 2017-07-12
--------------------

.. _changed-11:

Changed
~~~~~~~

-  Call connection() only once per function

.. _section-15:

[3.3.2] - 2017-07-10
--------------------

.. _changed-12:

Changed
~~~~~~~

-  Fix waiting for a vsphere task for vcenter 6.5

.. _section-16:

[3.3.1] - 2017-07-4
-------------------

.. _changed-13:

Changed
~~~~~~~

-  Change raw_input to input for python2/3 portability

.. _section-17:

[3.3.0] - 2017-07-4
-------------------

.. _changed-14:

Changed
~~~~~~~

-  Input user instead of raising MissingConfigException

.. _section-18:

[3.2.2] - 2017-07-4
-------------------

.. _changed-15:

Changed
~~~~~~~

-  Reboot and shutdown now wait until vmware tools is ready or timeout
-  Reboot and shutdown are now both async for consistency
-  Fix integration tests

.. _section-19:

[3.2.1] - 2017-07-2
-------------------

.. _changed-16:

Changed
~~~~~~~

-  Reset function is now idempotent
-  Fix integration tests

.. _section-20:

[3.2.0] - 2017-06-30
--------------------

.. _added-4:

Added
~~~~~

-  Power on function
-  Power off function
-  Shutdown function

.. _section-21:

[3.1.0] - 2017-06-22
--------------------

.. _added-5:

Added
~~~~~

-  Disk space threshold check for cloning vms

.. _section-22:

[3.0.3] - 2017-06-21
--------------------

.. _changed-17:

Changed
~~~~~~~

-  Update MANIFEST.in

.. _section-23:

[3.0.2] - 2017-06-21
--------------------

.. _changed-18:

Changed
~~~~~~~

-  Tests have been migrated from unittest to pytest
-  README has been updated

.. _section-24:

[3.0.1] - 2017-06-21
--------------------

.. _added-6:

Added
~~~~~

-  A read function for the configuration

.. _changed-19:

Changed
~~~~~~~

-  Default config uses empty string instead of None to be consistent

.. _section-25:

[3.0.0] - 2017-06-19
--------------------

.. _added-7:

Added
~~~~~

-  New configuration engine that allows the usage of INI files and
   environment

.. _changed-20:

Changed
~~~~~~~

-  Service checks (SSH and WinRM) are now quiet and don’t print anything
-  Retrieving objects from vcenter is also a quiet function now

Removed
~~~~~~~

-  MissingCredentialsError has been removed in favour of the new
   configuration
