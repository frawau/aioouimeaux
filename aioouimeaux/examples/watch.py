#!/usr/bin/env python
import argparse
import sys
import asyncio

from aioouimeaux.environment import Environment
from aioouimeaux.utils import matcher


def mainloop(name):
    matches = matcher(name)

    def found(sender, **kwargs):
        if matches(sender.name):
            print("Found device:", sender.name)
            sender.register_callback("statechange", motion)

    def motion(sender, **kwargs):
        if matches(sender.name):
            print("{} state is {state}".format(
                sender.name, state="on" if sender.get_state() else "off"))

    env = Environment(callback=found)
    env.start()



if __name__ == "__main__":
    parser = argparse.ArgumentParser("Motion notifier")
    parser.add_argument("name", metavar="NAME",
                        help="Name (fuzzy matchable)"
                             " of the Motion to detect")
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    mainloop(args.name)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n", "Exiting at user's request")
    finally:
        # Close the server
        loop.close()
