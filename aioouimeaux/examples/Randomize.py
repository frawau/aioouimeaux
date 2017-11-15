
import random
import datetime
import time
import aioouimeaux
from aioouimeaux.environment import Environment
import asyncio as aio

async def runme(env):
    await aio.sleep(3)
    print("")
    print("WeMo Randomizer")
    print("---------------")
    print(env.list_switches())
    print(env.list_motions())
    print("---------------")
    while True:
        # http://stackoverflow.com/questions/306400/how-do-i-randomly-select-an-item-from-a-list-using-python
        switchRND = env.get_switch( random.choice( env.list_switches() ) )
        print(switchRND)
        switchRND.toggle()
        await aio.sleep(90)

async def doclose(env):
    for switch in ( env.list_switches() ):
            print("Turning Off: " + switch)
            env.get_switch(switch).off()
    await aio.sleep(1)


# http://pydoc.net/Python/ouimeaux/0.7.3/ouimeaux.examples.watch/
if __name__ == "__main__":
    loop = aio.get_event_loop()
    env = Environment()
    env.start()
    task = loop.create_task(runme(env))
    # TODO: run from 10am to 10pm
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("---------------")
        print("Goodbye!")
        print("---------------")
        # Turn off all switches
        task.cancel()
        loop.run_until_complete(doclose(env))
    finally:
        loop.close()
