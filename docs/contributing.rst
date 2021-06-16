Contributing
============

Contributing is welcome both in the form of adding new devices support and
enhancing the functionality of the existing ones.

To report a bug or ask for a feature/enhancement please create an issue
on `Github <https://link_to_github>`_.

.. todo:: Create issue templates

Reporting bugs
--------------

As most of the bugs that can be encountered are related to the particular
hardware behavior, it would be impossible to reproduce and fix them without
knowing the exact hardware been used. **The following information must be
included with any bug description to be considered:**

* Full log output at the DEBUG log level (preferably attached as a separate
  .log file).
* The Python script that caused the error along with full stack trace.
* Exact brand, model and firmware version of the unit that has been used.

Please adhere to the following structure when creating an issue:

* Quick summary.
* Code excerpt/stack trace.
* Comments/suggestions, if any.

Feature requests
----------------

Please adhere to the following structure when creating an issue:

* Quick summary.
* Current behavior - describe what's happening/missing now.
* Desired behavior - describe what you would like to have instead and **why**.

.. _add_new_device:

Adding new devices
------------------

Here is the rough sequence to follow if you want to add a new device 'XXX':

0. Prepare your development tools:

   * Python (see :doc:`overview` for Python version and required packages)
   * Flake8
   * MyPy
1. If you have write access to the repository, create a new branch off
   ``develop`` named ``add_XXX_support``. If you don't have a write access, fork
   the repository and create a branch in your private fork.
2. Copy :file:`PyLabware/examples/new_Device_template.py` from
   :file:`examples` to :file:`devices`.
3. Rename the file to be <manufacturer>_<device_model>.py
4. Check the style guide below and write up your code.
5. When putting the command definitions into the helper class, please, put
   **all** commands listed in the device manual even if you are planning to use
   only a subset of them. You don't have to implement a method for each command,
   but having all of them listed is a burden of the first module author to help
   others in future.
6. Add the user manual into the :file:`manuals` folder and add a
   reference to it in the docstring of the command class.
7. Test your code on the hardware and fix all bugs found. If there are bugs in
   the hardware discovered, do describe them in the docstring of the appropriate
   method.
8. Run linting and MyPy check from the repository root::

    flake8 .
    mypy .

   There must be no flake8 errors, and as few MyPy errors as possible.
9. Before submitting PR ensure to merge in latest changes from the ``develop``
   branch.
10. Submit a PR to the mainline, provide brief description of the device and
    its particular quirks, if any.



Code style
----------

Please, take your time to read `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_
carefully before writing any code. If anything remains unclear, please, take
your time to read it again. We are not strictly following all the PEP8
guidelines, however, ugly code would not be merged. Here is the rough list of
things to check for:

* **All classes/methods/functions must have meaningful docstrings**
  - they are used for automatic generation of documentation.
* `Google style guide <http://google.github.io/styleguide/pyguide.html>`_
  must be followed for the docstrings syntax.
* Apart from the docstrings, **the code must have inline comments.**
* PascalCase is used for class names, underscore case for variable/method names.
  All command names use capitalized underscore syntax.
* Lazy formatting is using for logging.
* Log outputs should be preceded by the method name that emits the message.
* All parameters in log messages should be enclosed in <>.
* All code should pass flake8 linting without errors. A configuration file used
  in the CI can be found in the repository root.
* Type annotations should be used, but type checking with MyPy is not enforced.

