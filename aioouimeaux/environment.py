import logging

import socket
import asyncio as aio

from aioouimeaux.device import DeviceUnreachable
from aioouimeaux.device.switch import Switch
from aioouimeaux.device.insight import Insight
from aioouimeaux.device.maker import Maker
from aioouimeaux.device.lightswitch import LightSwitch
from aioouimeaux.device.motion import Motion
from aioouimeaux.device.bridge import Bridge
from aioouimeaux.discovery import UPnP, UPNP_PORT, UPNP_ADDR
from aioouimeaux.subscribe import SubscriptionRegistry
from aioouimeaux.utils import matcher
from functools import partial

import inspect

_MARKER = object()
_NOOP = lambda *x: None
log = logging.getLogger(__name__)

reqlog = logging.getLogger("requests")
reqlog.disabled = True


class StopBroadcasting(Exception):
    pass


class UnknownDevice(Exception):
    pass

class Environment(object):
    def __init__(self, callback=_NOOP, with_discovery=True, with_subscribers=True):
        """
        Create a WeMo environment.

        @param callback:         A function to be called when a new device is discovered.
        @type callback:          function
        @param with_discovery:   Whether to start device discovery.
        @type with_discovery:    bool
        @param with_subscribers: Whether to register for events with discovered devices.
        @type with_subscribers:  bool
        """
        if with_discovery:
            self.upnp = aio.Future()
        else:
            self.upnp = None
        #UPnP(bind=bind or self._config.bind)
        #discovered.connect(self._found_device, self.upnp)
        self._with_discovery = with_discovery
        self._with_subscribers = with_subscribers
        self._callback = callback
        self.devices = {}

    def __iter__(self):
        return self.devices.itervalues()




    def start(self):
        """
        Start the server(s) necessary to receive information from devices.
        """
        loop = aio.get_event_loop()

        if self._with_subscribers:
            # Start the server to listen to events
            self.registry = SubscriptionRegistry()
            server = self.registry.server
            xx = aio.ensure_future(server)

        if self._with_discovery:
            # Start the server to listen to new devices
            addrinfo = socket.getaddrinfo(UPNP_ADDR, None)[0]
            sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
            listen = loop.create_datagram_endpoint(
                        partial(UPnP,loop,UPNP_ADDR,self._found_device,self.upnp),
                        sock=sock
                     )
            xx = aio.ensure_future(listen)

        if self._with_discovery or self._with_subscribers:
            xx = aio.ensure_future(self.real_start())

    async def real_start(self):
        #print ("Awaiting registry")
        #await self.registry
        #self.registry = self.registry.result()
        await self.upnp
        self.upnp = self.upnp.result()
        if self._with_discovery:
            self.discover()


    def discover(self, seconds=2):
        """
        Discover devices in the environment.

        @param seconds: Number of seconds to broadcast requests.
        @type seconds: int
        """
        log.info("Discovering devices")
        self.upnp.broadcast(2)

    def _found_device(self, sender, **kwargs):
        address = kwargs['address']
        headers = kwargs['headers']
        usn = headers['usn']
        if usn.startswith('uuid:Socket'):
            klass = Switch
        elif usn.startswith('uuid:Lightswitch'):
            klass = LightSwitch
        elif usn.startswith('uuid:Insight'):
            klass = Insight
        elif usn.startswith('uuid:Sensor'):
            klass = Motion
        elif usn.startswith('uuid:Bridge'):
            klass = Bridge
        elif usn.startswith('uuid:Maker'):
        	klass = Maker
        else:
            log.info("Unrecognized device type. USN={0}".format(usn))
            return
        device = klass(headers['location'])
        aio.ensure_future(self._found_device_end(device,address))


    async def _found_device_end(self,device,address):
        await device.initialized
        log.info("Found device %r at %s" % (device, address))
        self._process_device(device)

    def _process_device(self, device):
        self.devices[device.name] = device
        if self._with_subscribers:
            self.registry.register(device)
            self.registry.on(device, 'BinaryState',
                             device._update_state)
        try:
            if isinstance(device, Bridge):
                pass
            else:
                device.ping()
        except DeviceUnreachable:
            return
        self._callback(device)

    def list_switches(self):
        """
        List switches discovered in the environment.
        """
        return [x for x,y in self.devices.items() if y.device_type == "Switch"]

    def list_motions(self):
        """
        List motions discovered in the environment.
        """
        return [x for x,y in self.devices.items() if y.device_type == "Motion"]

    def list_makers(self):
        """
        List makers discovered in the environment.
        """
        return [x for x,y in self.devices.items() if y.device_type == "Maker"]

    def list_bridges(self):
        """
        List bridges discovered in the environment.
        """
        return [x for x,y in self.devices.items() if y.device_type == "Bridge"]

    def get(self, name):
        if name:
            matches = matcher(name)
        else:
            matches = _NOOP
        for k in self.devices:
            if matches(k):
                return self.devices[k]
        else:
            raise UnknownDevice(name)

    def get_switch(self, name):
        """
        Get a switch by name.
        """
        try:
            return self.devices[name]
        except KeyError:
            raise UnknownDevice(name)

    def get_motion(self, name):
        """
        Get a motion by name.
        """
        try:
            return self.devices[name]
        except KeyError:
            raise UnknownDevice(name)

    def get_bridge(self, name):
        """
        Get a bridge by name.
        """
        try:
            return self.devices[name]
        except KeyError:
            raise UnknownDevice(name)

    def get_maker(self, name):
        """
        Get a maker by name.
        """
        try:
            return self.devices[name]
        except KeyError:
            raise UnknownDevice(name)


if __name__ == "__main__":

    def report_status(dev):
        print(f"\n{dev.name} status is now {dev.get_state() and 'On' or 'Off'}\n")

    def register_device(dev):
        dev.register_callback("statechange", report_status)
        print(f"Got new device {dev.name}")
        dev.explain()

    async def dotoggle(env):
        while True:
            await aio.sleep(5)
            print("Toggling")
            for dev in env.devices.values():
                dev.toggle()

    logging.basicConfig(level=logging.DEBUG)
    loop = aio.get_event_loop()
    environment = Environment(callback=register_device)
    environment.start()
    aio.ensure_future(dotoggle(environment))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n", "Exiting at user's request")
    finally:
        # Close the server
        loop.close()
