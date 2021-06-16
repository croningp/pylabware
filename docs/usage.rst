Usage
=====

Importing the library automatically imports all the device modules into the
library namespace to make their usage straightforward:

    >>> import PyLabware as pl
    >>> dir(pl)
    ['C3000SyringePump', 'C815FlashChromatographySystem', 'CF41Chiller',
    'CVC3000VacuumPump', 'HeiTorque100PrecisionStirrer', 'Microstar75Stirrer',
    'PetiteFleurChiller', 'R300Rotovap', 'RCTDigitalHotplate',
    'RETControlViscHotplate', 'RV10Rotovap', 'RZR2052ControlStirrer',
    '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__',
    '__package__', '__path__', '__spec__', 'connections', 'controllers', 'devices',
    'exceptions', 'models', 'parsers']

Basic examples
--------------

Creating a device
*****************

**Serial connection:**

    >>> import PyLabware as pl
    >>> pump = pl.C3000SyringePump(device_name="reagent_pump", port="COM7",
    connection_mode="serial", address=None, switch_address=4)

* :py:attr:`device_name` is an arbitrary string used to identify a device.
* :py:attr:`port` is a serial port name (platform-dependent).
* :py:attr:`connection_mode` determines which :doc:`connection adapter <data_model>` would be activated for the device.
* :py:attr:`address` determines IP address/DNS name for socket-based or HTTP REST connection, it is not used for serial connection.

 The rest of constructor parameters are device specific and are described in the corresponding :doc:`module documentation <src/devices>`.


**Socket-based connection:**

    >>> import PyLabware as pl
    >>> chiller = pl.CF41Chiller(device_name="jacket_chiller", port="5050",
    connection_mode="tcpip", address="192.168.0.1")

**HTTP connection:**

    >>> import PyLabware as pl
    >>> rv = pl.R300Rotovap(device_name="rotavap", connection_mode="http",
    address="r300.local", password="yourpass", port="4443")

Operating a device
******************

A general sequence for an arbitrary device would be:

1. Create device object. ::

    >>> import PyLabware as pl
    >>> pump = pl.C3000SyringePump(device_name="reagent_pump", port="COM7",
    connection_mode="serial", address=None, switch_address=4)

2. Alter any settings if needed.

3. Open connection. ::

    >>> pump.connect()                  # Open serial connection

4. Check that device is alive. ::

    >>> pump.is_connected()             # Check that the pump is live
    True

5. Check that device is initialized. :py:meth:`initialize_device()` handles any
   device-specific functionality needed for it to operate properly. ::

    >>> pump.is_initialized()           # Check that the pump has been initialized
    False
    >>> pump.initialize_device()

6. Run whatever operations are needed. ::

    >>> pump.get_valve_position()       # Check pump distribution valve position
    'I'
    >>> pump.withdraw(200)              # Withdraw 200 units
    >>> pump.get_plunger_position()
    200
    >>> pump.set_valve_position("O")    # Switch valve
    >>> pump.get_valve_position()
    'O'
    >>> pump.dispense(200)              # Dispense 200 units to another output
    >>> pump.get_plunger_position()
    0

7. Close the connection and exit. ::

    >>> pump.disconnect()               # Close connection before exiting

.. warning::  Gracefully closing connection before exiting is a good practice.
              Otherwise you are relying on a Python garbage collector for
              closing the connection when it destroys the device object.
              There are no warranties the latter would happen cleanly,
              so the physical device might get stuck with the half-open connection.

Running sequential commands
***************************

Often it is important to ensure that the device is idle before sending a
command. A classical example would be a syringe pump running
at low speed that would block any further commands until the current
dispensing/withdrawing is complete.

.. note:: For the definition of what 'device idle state' means in the context of
          this library, please check the documentation for the
          :py:meth:`~PyLabware.models.AbstractLabDevice.is_idle()`:

To indicate whether a device is ready to receive further commands, every device
driver implements a hardware-specific
:py:meth:`~PyLabware.models.AbstractLabDevice.is_idle()` method::

    >>> import PyLabware as pl
    >>> pump = pl.C3000SyringePump(device_name="reagent_pump", port="COM7",
    connection_mode="serial", address=None, switch_address=4)
    >>> pump.connect()
    >>> pump.initialise_device()
    >>> pump.is_idle()
    True
    ###########################
    # Set slow withdrawal speed
    ###########################
    >>> pump.set_speed(20)
    >>> pump.withdraw(200)
    ###############################################################
    # From here the pump would give a hardware error if any further
    # plunger movement commands are issued before it has finished move.
    ###############################################################

To make the life easier, a
:py:meth:`~PyLabware.controllers.LabDevice.execute_when_ready()` method
is provided. For most of the device drivers it is internally used when
necessary, so that the end user has nothing to worry about::

    class C3000SyringePump(AbstractSyringePump, AbstractDistributionValve):
        ...
        def move_plunger_absolute(self, position: int, set_busy: bool = True):
            """Makes absolute plunger move.
            """

            if set_busy is True:
                cmd = self.cmd.SYR_MOVE_ABS
            else:
                cmd = self.cmd.SYR_MOVE_ABS_NOBUSY
            # Send command & check reply for errors
            self.execute_when_ready(self.send, cmd, position)

For the detailed syntax please check the corresponding
:doc:`documentation <src/controllers>`.

The :py:meth:`~PyLabware.controllers.LabDevice.wait_until_ready()`
is a simplified wrapper over
:py:meth:`~PyLabware.controllers.LabDevice.execute_when_ready()`
that just blocks until the device is idle.

.. note:: If using :py:meth:`is_idle()`/:py:meth:`execute_when_ready()` is not
          convenient (e.g. the device doesn't report busy/idle state), there is
          a simple control flow mechanism built in that ensures there is a
          minimal delay between any two successive commands. Read more :ref:`here <timeouts>`.


Operating multiple devices
**************************

Operating multiple devices is similar to the single device example given above.
The :py:attr:`device_name` attribute can be used to distinguish between device
replies in the log files.

.. note:: Every device has its own connection object, so concurrent
          access to a single serial port from multiple devices is not supported.


Advanced examples
-----------------

.. _tasks:

Running concurrent tasks for devices
************************************

PyLabware supports concurrent execution of commands if the device hardware itself
supports it::

    >>> import PyLabware as pl
    >>> pump = pl.C3000SyringePump(device_name="reagent_pump", port="COM7",
    connection_mode="serial", address=None, switch_address=4)
    >>> pump.connect()
    >>> pump.initialise_device()
    >>> pump.is_idle()
    True
    >>> pump.set_speed(20)
    >>> pump.withdraw(200)
    >>> def print_plunger_position():
    ...:    print(f"Plunger position: {pump.get_plunger_position()}")
    >>> pump.start_task(interval=5, method=print_plunger_position, args=None)
    Plunger position: 0
    Plunger position: 0
    Plunger position: 0
    >>> pump.withdraw(200)
    Plunger position: 12
    Plunger position: 62
    Plunger position: 113
    Plunger position: 163
    Plunger position: 200
    Plunger position: 200
    >>> pump.get_all_tasks()
    [<LabDeviceTask(Thread-2, started 7944)>]
    >>> task = pump.get_all_tasks()[0]
    >>> pump.stop_task(task)

In the example above the plunger position is constantly monitored and printed
out while the pump is withdrawing the liquid. Any sensible number of tasks can
be run in parallel and started/stopped independently. A common use case for this
feature would be to issue keep-alive commands so that the device stays active.

More examples can be found in
:file:`PyLabware/examples/concurrent_tasks.py`

.. todo:: Add example from IKA RV10 keepalive.

.. _simulation:

Simulation mode
***************

Often it is desirable to make a dry run of a script before running it on actual
hardware to avoid unnecessary time/material cost and/or to ease up debug and
development. To fulfill this task, every device can be run in simulation
mode.

The simulation mode is switched on by setting the :py:attr:`simulation` property
to ``True``. Simulation messages are printed to log at INFO level so to use it
you need to configure logging first::

    >>> import PyLabware as pl
    >>> import logging
    >>> logging.getLogger().setLevel(logging.INFO)
    >>> pump = pl.C3000SyringePump(device_name="reagent_pump", port="COM7", connection_mode="serial", address=None, switch_address=4)
    [INFO] :: PyLabware.connections.SerialConnection :: Creating connection object with the following settings:
    {'address': None, 'port': 'COM7', 'encoding': 'UTF-8', 'command_delay': 0.5,
    'receive_buffer_size': 128, 'receive_timeout': 1, 'transmit_timeout': 1,
    'receiving_interval': 0.05, 'write_timeout': 0.5, 'baudrate': 9600,
    'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'xonxoff': False, 'rtscts': False,
    'dsrdtr': False, 'inter_byte_timeout': False}

    >>> pump.simulation = True

After that one can use the device as usual issuing any commands::

    >>> pump.is_connected()
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Pretending to send message <'/5?23R\r\n'>
    True
    >>> pump.is_initialized()
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Patched send() to return <True>, calling <is_initialized>
    True
    >>> pump.get_valve_position()
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Pretending to send message <'/5?6R\r\n'>
    >>> pump.get_plunger_position()
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Pretending to send message <'/5?R\r\n'>
    >>> In [9]: pump.withdraw(200)
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Patched send() to return <<PyLabware.models.LabDeviceReply object at 0x05A8DA08>>, calling <is_idle>
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: Waiting done. Device <test> ready.
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Pretending to send message <'/5P200R\r\n'>
    >>> pump.dispense(200)
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Patched send() to return <<PyLabware.models.LabDeviceReply object at 0x05A8DA08>>, calling <is_idle>
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: Waiting done. Device <test> ready.
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Pretending to send message <'/5D200R\r\n'>
    >>> pump.set_valve_position("O")
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Patched send() to return <<PyLabware.models.LabDeviceReply object at 0x05A8DA08>>, calling <is_idle>
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: Waiting done. Device <test> ready.
    [INFO] :: PyLabware.controllers.C3000SyringePump.test :: SIM :: Pretending to send message <'/5OR\r\n'>

All methods work without throwing an error, though, obviously, the
methods that have to return the data from the device do not return anything.
This behavior can be altered in the device driver, see below for more details.

The simulation mode is designed in such a way to facilitate device testing. Thus,
all value checking in device methods still takes place even in simulation::

    >>> pump.set_valve_position("X")
    SLDeviceCommandError: Unknown valve position <X> requested!


Tweaking simulation mode
************************

How simulation mode works
^^^^^^^^^^^^^^^^^^^^^^^^^

Simulation mode works by intercepting the execution workflow in the following four
places:

* :py:meth:`LabDevice.connect()`
* :py:meth:`LabDevice.disconnect()`
* :py:meth:`LabDevice.send()`
* :py:meth:`LabDevice._recv()`

A typical implementation just replaces the actual invocation of the underlying
connection adapter method with a :py:meth:`logging.info()` call::

    def connect(self):
        """ Connects to the device.

        This method normally shouldn't be redefined in child classes.
        """

        if self._simulation is True:
            self.logger.info("SIM :: Opened connection.")
            return
        self.connection.open_connection()
        self.logger.info("Opened connection.")

This results in all high-level code (e.g. value checking and other
device-specific logic) to be executed as usual in the simulation mode, but all
the command strings prepared are just logged instead of being sent to the device.


Using :py:attr:`@in_simulation_device_returns` decorator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes it is necessary to tune the simulated device behavior more granularly.
The possible examples are:

* A device that echoes the command back upon successful action. The device driver
  code checks the device reply to determine whether the command has been
  interpreted and ran correctly and raises an error if not.

* A device with higher-level logic that relies on a particular value being
  returned from the device before the execution can continue, e.g. waiting for a
  certain temperature to be reached.

Both of these examples would be impossible to implement with the simple logic
described above. To work around this issue and avoid patching every complex
device method with ``if self.simulation is True`` clause, a special method decorator is used.

:py:attr:`@in_simulation_device_returns` decorator should be used to wrap any
function that relies on a particular value that device should return. This value
should be passed as the decorator argument. Here is an example from :doc:`Tricontinent C3000
syringe pump driver <src/devices.tricontinent_c3000>`::

    class C3000SyringePump(AbstractSyringePump, AbstractDistributionValve):
        ...
        @in_simulation_device_returns(LabDeviceReply(body=C3000SyringePumpCommands.DEFAULT_STATUS))
            def is_idle(self) -> bool:
            """Checks if pump is in idle state.
            """

            # Send status request command and read back reply with no parsing
            # Parsing manipulates status byte to get error flags, we need it here
            try:

                ########################################################
                # send() patching takes place here
                ########################################################
                reply = self.send(self.cmd.GET_STATUS, parse_reply=False)

            except SLConnectionError:
                return False
            # Chop off prefix/terminator & cut out status byte
            reply = parser.stripper(reply.body, self.reply_prefix, self.reply_terminator)
            status_byte = ord(reply[0])
            # Busy/idle bit is 6th bit of the status byte. 0 - busy, 1 - idle
            if status_byte & 1 << 5 == 0:
                self.logger.debug("is_idle()::false.")
                return False
            # Check for errors if any
            try:
                self.check_errors(status_byte)
            except SLDeviceInternalError:
                self.logger.debug("is_idle()::false, errors present.")
                return False
            self.logger.debug("is_idle()::true.")
            return True

The decorator works :doc:`as following <src/controllers>`:

* Gets the object reference from the wrapped bound method (passed as self in the arguments list).
* Checks :py:meth:`self.simulation` to proceed.
* Stores reference to original :py:meth:`self.send()` and replaces :py:meth:`self.send()` with
  a lambda returning decorator argument.
* Runs the wrapped function and stores the return value.
* Replaces :py:meth:`self.send()` back with original reference and returns the return
  value from previous step.

Simulating dynamic return values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes just the decorator is also not enough to achieve desirable behavior. A
typical example would be a device that echoes back not the command, but the
command argument and the code that relies on checking this reply for proper
operation, e.g.::

  Command to device >>> SET_TEMP 25.0
  Device reply      <<< 25.0

This is quite typical echo mode often encountered in different devices. In order
to support this mode of operation the following special syntax is used::

  @in_simulation_device_returns("{$args[1]}")
  def some_method(arg1, arg2, arg3):

``1`` is the number of positional argument that you want to extract from the
:py:meth:`some_method` call. In the case above the decorator will extract
``arg2`` from the arguments list and return it as a return value for the
:py:meth:`send()` call. Here's a specific example from the Heidolph overhead
stirrer driver::

    class HeiTorque100PrecisionStirrer(AbstractStirringController):
        ...
        @in_simulation_device_returns("{$args[1]}")
        def set_speed(self, speed: int):
            """Sets rotation speed in rpm.
            """

            # If the stirrer is not running, just update internal variable
            if not self._running:
                # Check value against limits before updating
                self.check_value(self.cmd.SET_SPEED, speed)
                self._speed_setpoint = speed
            else:

                ###############################################################
                # Here send() will be replaced with a lambda returning args[1]
                # from set_speed(), which is speed
                ###############################################################
                readback_setpoint = self.send(self.cmd.SET_SPEED, speed)

                if readback_setpoint != speed:
                    self.stop()
                    raise SLDeviceReplyError(f"Error setting stirrer speed. Requested setpoint <{self._speed_setpoint}> "
                                            f"RPM, read back setpoint <{readback_setpoint}> RPM")
                self._speed_setpoint = speed


