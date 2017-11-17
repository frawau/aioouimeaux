import logging
from urllib.parse import urlsplit

import asyncio as aio

from functools import partial
from .api.service import Service
from .api.xsd import device as deviceParser
from ..utils import requests_get


log = logging.getLogger(__name__)


class DeviceUnreachable(Exception): pass
class UnknownService(Exception): pass
class UnknownSignal(Exception): pass
class NotACallable(Exception): pass


class Device(object):
    def __init__(self, url):
        self._state = None
        self.host = urlsplit(url).hostname
        #self.port = urlsplit(url).port
        self.services = {}
        self.initialized = aio.Future()
        self._callback = {"statechange":None}
        xx = aio.ensure_future(self._get_xml(url))

    async def _get_xml(self,url):
        base_url = url.rsplit('/', 1)[0]
        xml = await requests_get(url)
        self._config = deviceParser.parseString(xml.raw_body).device
        sl = self._config.serviceList
        for svc in sl.service:
            svcname = svc.get_serviceType().split(':')[-2]
            service = Service(svc, base_url)
            await service.initialized
            service.eventSubURL = base_url + svc.get_eventSubURL()
            self.services[svcname] = service
            setattr(self, svcname, service)

        fut = self.basicevent.GetBinaryState()
        await fut
        self._state = fut.result()["BinaryState"]
        self.initialized.set_result(True)

    def register_callback(self,signal,func):
        if func is not None:
            if signal not in self._callback:
                raise UnknownSignal
            if not callable(func):
                raise NotACallable

        self._callback[signal]=func

    def _update_state(self, value):
        self._state = int(value)
        if self._callback["statechange"]:
            if aio.iscoroutinefunction(self._callback["statechange"]):
                aio.ensure_future(self._callback["statechange"](self))
            else:
                self._callback["statechange"](self)

    def get_state(self, force_update=False):
        """
        Returns 0 if off and 1 if on.
        """
        if force_update or self._state is None:
            xx = self.basicevent.GetBinaryState()
        return self._state

    def get_service(self, name):
        try:
            return self.services[name]
        except KeyError:
            raise UnknownService(name)

    def list_services(self):
        return self.services.keys()

    def ping(self):
        try:
            self.get_state()
        except Exception:
            raise DeviceUnreachable(self)

    def explain(self,prefix=""):
        for name, svc in self.services.items():
            print(f"{prefix}{name}")
            print(prefix+'-' * len(name))
            for aname, action in svc.actions.items():
                print("%s  %s(%s)" % (prefix,aname, ', '.join(action.args)))
            print()

    @property
    def model(self):
        return self._config.get_modelDescription()

    @property
    def name(self):
        return self._config.get_friendlyName()

    @property
    def serialnumber(self):
        return self._config.get_serialNumber()


def test():
    device = Device("http://10.42.1.102:49152/setup.xml")
    print(device.get_service('basicevent').SetBinaryState(BinaryState=1))


if __name__ == "__main__":
    test()

