
import random
import datetime
import time
import aioouimeaux
from aioouimeaux.wemo import WeMo
import asyncio as aio

async def runme(wemo):
    await aio.sleep(3)
    print("")
    print("WeMo Randomizer")
    print("---------------")
    print(wemo.list_switches())
    print("---------------")
    while True:
        # http://stackoverflow.com/questions/306400/how-do-i-randomly-select-an-item-from-a-list-using-python
        switchRND = wemo.get_switch( random.choice( wemo.list_switches() ) )
        print(switchRND)
        switchRND.toggle()
        await aio.sleep(90)

async def doclose(wemo):
    for switch in ( wemo.list_switches() ):
            print("Turning Off: " + switch)
            wemo.get_switch(switch).off()
    await aio.sleep(1)

def register_device(device):
    xx=device.get_state()

# http://pydoc.net/Python/ouimeaux/0.7.3/ouimeaux.examples.watch/
if __name__ == "__main__":
    loop = aio.get_event_loop()
    wemo = WeMo(types=["Switch"])
    wemo.start()
    task = loop.create_task(runme(wemo))
    # TODO: run from 10am to 10pm
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("---------------")
        print("Goodbye!")
        print("---------------")
        # Turn off all switches
        task.cancel()
        loop.run_until_complete(doclose(wemo))
    finally:
        loop.close()
