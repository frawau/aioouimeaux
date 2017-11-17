# aioouimeaux

Open source control for Belkin WeMo devices

* Free software: BSD license
* Documentation: Soon at http://aioouimeaux.rtfd.org.

## Features

* Supports WeMo Switch, Light Switch, Insight Switch and Motion
* Python API to interact with device at a low level using asyncio

## About this library

Based on a repository that can be found here: https://github.com/syphoxy/ouimeaux.git
The original repository can be found here: https://github.com/iancmcc/ouimeaux

The library was modified to make use of asyncio.

It has been forked here since it is a significant change. It has been renamed to
clearly indicate the difference.

## Installation
```
$ sudo pip3 install aioouimeaux

```
If you want to use a virtual environement
```
$ sudo pip3 install virtualenv
$ mkdir ouimeaux-env
$ virtualenv ouimeaux-env
$ source ouimeaux-env/bin/activate
$ cd ouimeaux-env
$ pip3 install git+https://github.com/syphoxy/ouimeaux.git
```

At this point you should be able to use

**Note:** Ensure that the `pip` and `virtualenv` command you use belongs to a
Python 3 installation. On some systems, there are multiple versions of Python
installed.

You can try:
```
python3 -m aioouimeaux
```
and see something like:
```
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

```

## Troubleshooting

Open an issue and I'll try to help.
