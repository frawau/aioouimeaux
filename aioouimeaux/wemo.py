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


_MARKER = object()
_NOOP = lambda *x: None
log = logging.getLogger(__name__)

reqlog = logging.getLogger("requests")
reqlog.disabled = True

_LOTYPES=["Switch","Motion","Bridge", "Maker"]

class StopBroadcasting(Exception):
    pass


class UnknownDevice(Exception):
    pass

class WeMo(object):
    def __init__(self, callback=_NOOP, types = _LOTYPES, with_discovery=True, with_subscribers=True):
        """
        Create a WeMo environment.

        @param callback:         A function to be called when a new device is discovered.
        @type callback:          function
        @param types:            A list of the types of devices we want discovered.
        @type types:             list
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
        self._list_of_types = types
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
            # Allow multiple copies of this program on one machine
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        if self._with_discovery:
            await self.upnp
            self.upnp = self.upnp.result()
            self.discover()


    def stop(self):
        if self._with_subscribers:
            self.registry.close()
        if self._with_discovery:
            self.upnp.close()

    def discover(self, seconds=3):
        """
        Discover devices in the environment.

        @param seconds: Number of seconds to broadcast requests.
        @type seconds: int
        """
        log.info("Discovering devices")
        self.upnp.broadcast(seconds)

    def _found_device(self, sender, **kwargs):
        address = kwargs['address']
        headers = kwargs['headers']
        usn = headers['usn']
        if usn.startswith('uuid:Socket') and "Switch" in self._list_of_types:
            klass = Switch
        elif usn.startswith('uuid:Lightswitch') and "Switch" in self._list_of_types:
            klass = LightSwitch
        elif usn.startswith('uuid:Insight') and "Switch" in self._list_of_types:
            klass = Insight
        elif usn.startswith('uuid:Sensor') and "Motion" in self._list_of_types:
            klass = Motion
        elif usn.startswith('uuid:Bridge') and "Bridge" in self._list_of_types:
            klass = Bridge
        elif usn.startswith('uuid:Maker') and "maker" in self._list_of_types:
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

    def device_gone(self, device):
        #try:
        if self._with_discovery:
            self.upnp.connection_lost(device._config.UDN)
        if self._with_subscribers:
            self.registry.unregister(device)
        del self.devices[device.name]
        #except:
            #pass


    def _process_device(self, device):
        self.devices[device.name] = device
        if self._with_subscribers:
            self.registry.register(device)
            #self.registry.on(device, 'BinaryState',
                             #device._update_state)
        try:
            if isinstance(device, Bridge):
                pass
            else:
                device.ping()
        except DeviceUnreachable:
            return
        self._callback(device)

    def list_devices(self):
        """
        List switches discovered in the environment.
        """
        return [x for x in self.devices.keys()]


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
            assert name in self.list_switches()
            return self.devices[name]
        except KeyError:
            raise UnknownDevice(name)

    def get_motion(self, name):
        """
        Get a motion by name.
        """
        try:
            assert name in self.list_motions()
            return self.devices[name]
        except KeyError:
            raise UnknownDevice(name)

    def get_bridge(self, name):
        """
        Get a bridge by name.
        """
        try:
            assert name in self.list_bridges()
            return self.devices[name]
        except KeyError:
            raise UnknownDevice(name)

    def get_maker(self, name):
        """
        Get a maker by name.
        """
        try:
            assert name in self.list_makers()
            return self.devices[name]
        except KeyError:
            raise UnknownDevice(name)



