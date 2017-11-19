from collections import defaultdict
import logging
from xml.etree import cElementTree
from functools import partial

import asyncio as aio
import aiohttp as aioh
from aiohttp_wsgi import WSGIHandler

from aioouimeaux.utils import get_ip_address, requests_request
from aioouimeaux.device.insight import Insight
from aioouimeaux.device.maker import Maker

from random import randint



log = logging.getLogger(__name__)

NS = "{urn:schemas-upnp-org:event-1-0}"
SUCCESS = b'<html><body><h1>200 OK</h1></body></html>'


class SubscriptionRegistry(object):
    def __init__(self):
        self._devices = {}
        self._subscriptions = {}
        self._callbacks = defaultdict(list)
        self.port = randint(8300, 8990)


    def register(self, device):
        if not device:
            log.error("Received an invalid device: %r", device)
            return
        log.info("Subscribing to basic events from %r", device)
        self._devices[device.host] = device
        self._do_resubscribe(device, device.basicevent.eventSubURL)

    def unregister(self, device):
        if device.host in self._subscriptions:
            try:
                self._subscriptions[device.host].cancel()
                del self._subscriptions[device.host]
            except:
                pass
            finally:
                del self._devices[device.host]

    def _do_resubscribe(self, device, url, sid=None):
        if device.host not in self._subscriptions:
            self._subscriptions[device.host] = aio.ensure_future(self._resubscribe(device,url,sid))

    async def _resubscribe(self, device, url, sid=None):
        try:
            headers = {'TIMEOUT': 'Second-%d' % 1800}
            if sid is not None:
                headers['SID'] = sid
            else:
                host = get_ip_address()
                headers.update({
                    "CALLBACK": '<http://%s:%d>'%(host, self.port),
                    "NT": "upnp:event"
                })
            response = await requests_request(method="SUBSCRIBE", url=url,
                                    headers=headers)
            if response.status == 412 and sid:
                # Invalid subscription ID. Send an UNSUBSCRIBE for safety and
                # start over.
                await requests_request(method='UNSUBSCRIBE', url=url,
                                headers={'SID': sid})
                return await self._resubscribe(url)
            timeout = int(response.headers.get('timeout', '1801').replace(
                'Second-', ''))
            sid = response.headers.get('sid', sid)
            self._subscriptions[device.host] = aio.get_event_loop().call_later(int(timeout * 0.75), partial(self._do_resubscribe,url, sid))
        except:
            del self._subscriptions[device.host]

    def _handle(self, environ, start_response):
        device = self._devices.get(environ['REMOTE_ADDR'])
        if device is not None:
            data = environ['wsgi.input'].read().decode("UTF-8")
            # trim garbage from end, if any
            data = data.split("\n\n")[0]
            doc = cElementTree.fromstring(data)
            for propnode in doc.findall(f'./{NS}property'):
                for property_ in propnode.getchildren():
                    text = property_.text
                    if isinstance(device, Insight) and property_.tag=='BinaryState':
                        text = text.split('|')[0]
                    self._event(device, property_.tag, text)
        start_response('200 OK', [
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(SUCCESS)))
        ])
        return [SUCCESS]

    def _event(self, device, type_, value):
        for t, callback in self._callbacks.get(device, ()):
            if t == type_:
                callback(value)

    def on(self, device, type, callback):
        self._callbacks[device].append((type, callback))


    @property
    def server(self):
        """
        UDP server to listen for responses.
        """
        server = getattr(self, "_server", None)
        if server is None:
            wsgi_handler = WSGIHandler(self._handle)
            app=aioh.web.Application()
            app.router.add_route("*",'/{path_info:.*}', wsgi_handler)
            whandler = app.make_handler(logger=log)
            server = aio.get_event_loop().create_server(whandler,host='',port=self.port)
        return server
