===========
Python API
===========

WeMo
-----------
The main interface is presented by a ``WeMo``, which optionally accepts
functions called when a Switch, Motion o other device is identified::

    import asyncio as aio
    from aioouimeaux.wemo import WeMo

    def on_device(device):
        if device.device_type == "Switch":
            print(f"Switch found! {device.name}")
        elif device.device_type == "Switch":
            print(f"Motion found! {device.name}")

    loop = aio.get_event_loop()
    wemo = WeMo(on_device)

Start up the server to listen for responses to the discovery broadcast::

    wemo.start()
    loop.run_forever()

Discovery of all WeMo devices is then done automatically. If repeated discovery
is needed it can be triggered with "discovery" pass the length of time (in seconds)
you want discovery to run::

    wemo.discover(seconds=3)

During that time, ``WeMo`` will broadcast search requests every second
and parse responses. At any point, you can see the names of discovered devices::

    print(wemo.list_switches())
    ['Living Room', 'TV Room', 'Front Closet']
    print(wemo.list_motions())
    ['Front Hallway']

Devices can be retrieved by using ``get_switch`` and ``get_motion`` methods::

    switch = env.get_switch('TV Room')
    print(switch)
    <WeMo Switch "TV Room">

Devices
-------
Every device has a ``device_type`` attributes. Yhe value is one of
    - Switch
    - Motion
    - Bridge
    - Insight
    - Maker

One can register a callable/coroutine to be executed when a given event occurs.
At this time only the "statechange" event is known::

    import asyncio as aio
    from aioouimeaux.wemo import WeMo

    def report_status(device):
        """The callback function will get a device as parameter."""
        print(f"{device.device_type} {device.name} status is now {device.get_state() and 'On' or 'Off'}")

    def on_device(device):
        print(f"Device found! {device.name}")
        device.register_callback("statechange", report_status)

    loop = aio.get_event_loop()
    wemo = WeMo(on_device)
    wemo.start()
    loop.run_forever()

All devices have an ``explain()`` method, which will print out a list of all
available services, as well as the actions and arguments to those actions
on each service::

    switch.explain()

    basicevent
    ----------
      SetSmartDevInfo(SmartDevURL)
      SetServerEnvironment(ServerEnvironmentType, TurnServerEnvironment, ServerEnvironment)
      GetDeviceId()
      GetRuleOverrideStatus(RuleOverrideStatus)
      GetIconURL(URL)
      SetBinaryState(BinaryState)
    ...

Services and actions are available via simple attribute access. Calling actions
returns a ``future`` that will be set with a dictionary of return values::

    async def show_result(future):
        await future
        print(future.result())

    future = switch.basicevent.SetBinaryState(BinaryState=0)
    xx = aio.ensure_future(show_result(future))

Devices can take time to be initialized. To verify that a device has been initialized, then
``initialized`` attribute is a future that is set once initialization is done.

Switches
--------
Switches have three shortcut methods defined: ``get_state``, ``on`` and
``off``. Those methods return a ``future``

Motions
-------
Motions have one shortcut method defined: ``get_state``.

Bridge (Not tested)
------
Bridges have these shortcut methods. Returning ``future``

    bridge_get_lights
    bridge_get_groups
    light_set_state
    light_set_group

Insight (Not tested)
-------
In addition to the normal Switch methods, Insight switches have several metrics
exposed::

    insight.today_kwh
    insight.current_power
    insight.today_on_time
    insight.on_for
    insight.today_standby_time


Examples
--------
The module can be ran::

    python3 -m aioouimeaux

will give an output similar to this::

    Hit "Enter" to start
    Use Ctrl-C to quit
    Motion Motion status is now Off
    Switch Test Switch 3 status is now Off
    Switch Test Switch 1 status is now On
    Switch Test Switch 2 status is now On
    Motion Motion status is now Off
    Select Device:
            [1]     Motion
            [2]     Test Switch 1
            [3]     Test Switch 2
            [4]     Test Switch 3

    Your choice:2
    Select Function for Test Switch 1:
            [1]     Power (0 or 1)
            [2]     Get Home Id
            [3]     Get MAC Address
            [4]     Get Device Id
            [5]     Get Serial Number
            [6]     Explain
            [7]     Function X (e.g. basicevent.GetHomeInfo see 'explain')

            [0]     Back to device selection



Some examples_ are included in the source demonstrating common use cases.
Suggestions (or implementations) for more are always welcome.

.. _examples: https://github.com/frawau/aioouimeaux/tree/master/aioouimeaux/examples
