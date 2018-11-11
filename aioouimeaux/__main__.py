#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# This application is an example on how to use aioouimeaux
#
# Copyright (c) 2016 François Wautier
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
import sys
import asyncio as aio
from functools import partial
import argparse
import socket
import asyncio as aio
from aioouimeaux.wemo import WeMo
from collections import OrderedDict

wemodoi = None #Device of interest

listoffunc=OrderedDict()
listoffunc["Get Home Id"] = (lambda dev: dev.basicevent.GetHomeId(),"HomeId")
listoffunc["Get MAC Address"] = (lambda dev: dev.basicevent.GetMacAddr(),"MacAddr")
listoffunc["Get Device Id"] = (lambda dev: dev.basicevent.GetDeviceId(),"")
listoffunc["Get Serial Number"] = (lambda dev: dev.serialnumber,"")
listoffunc["Get Power Consumption"] = (lambda dev: dev.insight_params,"")

async def showinfo(future,info,dev,key=""):
    try:
        await aio.wait_for(future, timeout=5)
        resu = future.result()
        if key:
            print("\n{}: {} is {}".format(dev.name, info,resu[key]))
        else:
            print("\n{}: {} is {}".format(dev.name, info,resu))
    except Exception as e:
        print("\nException for {}: {} failed with {}".format(dev.name, info,e))
        unregister_device(dev)

async def await_result(future,dev):
    try:
        await aio.wait_for(future, timeout=5)
        resu = future.result()
        #TODO Could log on debug
    except Exception as e:
        print("\nException for {}: On/Off failed with {e}".format(dev.name))
        unregister_device(dev)

def readin():
    """Reading from stdin and displaying menu"""
    global MyWeMo
    global wemodoi
    selection = sys.stdin.readline().strip("\n")
    devices = MyWeMo.list_devices()
    devices.sort()
    lov=[ x for x in selection.split(" ") if x != ""]
    if lov:
        if wemodoi:
            #try:
            if True:
                selection = int(lov[0])
                if selection < 0 :
                    print("Invalid selection.")
                else:
                    if wemodoi.device_type == "Switch":
                        if selection == 1:
                            if len(lov) >1:
                                if lov[1].lower() in ["1","on","true"]:
                                    future = wemodoi.on()
                                else:
                                    future = wemodoi.off()
                                xx = aio.ensure_future(await_result(future,wemodoi))
                                wemodoi=None
                            else:
                                print("Error: For power you must indicate on or off\n")
                        selection -= 1

                    if selection > (len(listoffunc)+2):
                        print("Invalid selection.")
                    elif selection == (len(listoffunc)+1):
                        print("Function supported by {}".format(wemodoi.name))
                        wemodoi.explain(prefix="\t")
                        wemodoi = None
                    elif selection == (len(listoffunc)+2):
                        if len(lov) >1:
                            lok = [ x.strip() for x in lov[1].strip().split(".")]
                            fcnt = wemodoi
                            for key in lok:
                                fcnt = getattr(fcnt,key,None)
                                if fcnt is None:
                                    print("Unknown function {}".format(lov[1].strip()))
                                    break
                            if fcnt:
                                if callable(fcnt):
                                    param={}
                                    if len(lov)>2:
                                        param={}
                                        key=None
                                        for x in range(2,len(lov)):
                                            if key:
                                                param[key]=lov[x]
                                                key=None
                                            else:
                                                key=lov[x]
                                        if key:
                                            param[key]=""
                                    if param:
                                        future = fcnt(**param)
                                    else:
                                        future = fcnt()
                                    xx = aio.ensure_future(showinfo(future,".".join(lok),wemodoi,""))
                                else:
                                    print(getattr(wemodoi,fcnt,None))
                                wemodoi = None
                        else:
                            print("We need a function to execute")
                    elif selection>0:
                        what = [x for x in listoffunc.keys()][selection-1]
                        fcnt,key = listoffunc[what]
                        what = what.replace("Get","").strip()
                        try:
                            future = fcnt(wemodoi)
                            if aio.isfuture(future):
                                    xx = aio.ensure_future(showinfo(future,what,wemodoi,key))
                        except:
                            print("Operation not supported by device.")

                        else:
                            print("\n{}: {} is {}".format(wemodoi.name, what, future))
                        wemodoi = None
                    else:
                        wemodoi = None
            #except:
            #print (f"\nError: Selection must be a number between 0 and {len(listoffunc)+3}.\n")
        else:
            try:
                if int(lov[0]) > 0:
                    devices = MyWeMo.list_devices()
                    devices.sort()
                    if int(lov[0]) <=len(devices):
                        wemodoi=MyWeMo.devices[devices[int(lov[0])-1]]
                    else:
                        print("\nError: Not a valid selection.\n")

            except:
                print ("\nError: Selection must be a number.\n")

    if wemodoi:
        print("Select Function for {}:".format(wemodoi.name))
        selection = 1
        if wemodoi.device_type == "Switch":
            print("\t[{}]\tPower (0 or 1)".format(selection))
            selection += 1
        for x in listoffunc:
            print("\t[{}]\t{}".format(selection,x))
            selection += 1
        print("\t[{}]\tExplain".format(selection))
        print("\t[{}]\tFunction X (e.g. basicevent.GetHomeInfo see 'explain')".format(selection+1))
        print("")
        print("\t[0]\tBack to device selection")
    else:
        idx=1
        print("Select Device:")
        devices = MyWeMo.list_devices()
        devices.sort()
        for x in devices:
            print("\t[{}]\t{}".format(idx,x))
            idx+=1
    print("")
    print("Your choice: ", end='',flush=True)


def report_status(dev):
    print("{} {} status is now {}".format(dev.device_type, dev.name, dev.get_state() and 'On' or 'Off'))

def register_device(dev):
    dev.register_callback("statechange", report_status)
    #dev.explain()

def unregister_device(dev):
    global MyWeMo
    print("Device {} with {}".format(dev, dev.basicevent.eventSubURL))
    MyWeMo.device_gone(dev)


loop = aio.get_event_loop()
#loop.set_debug(True)
MyWeMo = WeMo(callback=register_device)
MyWeMo.start()
try:
    loop.add_reader(sys.stdin,readin)
    print("Hit \"Enter\" to start")
    print("Use Ctrl-C to quit")
    loop.run_forever()
except KeyboardInterrupt:
    print("\n", "Exiting at user's request")
finally:
    # Close the reader
    loop.remove_reader(sys.stdin)
    MyWeMo.stop()
    loop.run_until_complete(aio.sleep(1))
    loop.close()
