import logging
from xml.etree import cElementTree as et

from ...utils import requests_get, requests_post
from .xsd import service as serviceParser
import asyncio as aio

log = logging.getLogger(__name__)

REQUEST_TEMPLATE = """
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
 <s:Body>
  <u:{action} xmlns:u="{service}">
   {args}
  </u:{action}>
 </s:Body>
</s:Envelope>
"""


class Action(object):
    def __init__(self, service, action_config):
        self._action_config = action_config
        self.name = action_config.get_name()
        self.serviceType = service.serviceType
        self.controlURL = service.controlURL
        self.args = {}
        self.headers = {
            'Content-Type': 'text/xml',
            'SOAPACTION': '"{}#{}"'.format(self.serviceType,self.name)
        }
        arglist = action_config.get_argumentList()
        if arglist is not None:
            for arg in arglist.get_argument():
                name = arg.get_name()
                if name:
                    # TODO: Get type instead of setting 0
                    self.args[arg.get_name()] = 0

    def __call__(self,**kwargs):
        future = aio.Future()
        aio.ensure_future(self.__do__call__(future,**kwargs))
        return future

    async def __do__call__(self, future, **kwargs):
        try:
            arglist = '\n'.join('<{0}>{1}</{0}>'.format(arg, value)
                                for arg, value in kwargs.items())
            body = REQUEST_TEMPLATE.format(
                action=self.name,
                service=self.serviceType,
                args=arglist
            )
            response = await requests_post(self.controlURL, data=body.strip(), headers=self.headers)
            d = {}
            resp = response.raw_body
            for r in et.fromstring(resp).getchildren()[0].getchildren()[0].getchildren():
                d[r.tag] = r.text
            future.set_result(d)
        except Exception as e:
            future.set_exception(e)

    def __repr__(self):
        return "<Action {} ({}>".format(self.name, ', '.join(self.args))


class Service(object):
    """
    Represents an instance of a service on a device.
    """

    def __init__(self, service, base_url):
        self._base_url = base_url.rstrip('/')
        self._config = service
        self.actions = {}
        self.initialized = aio.Future()
        xx = aio.ensure_future(self._get_xml())
        self._svc_config = None

    async def _get_xml(self):
        url = '%s/%s' % (self._base_url, self._config.get_SCPDURL().strip('/'))
        xml = await requests_get(url)
        self._svc_config = serviceParser.parseString(xml.raw_body).actionList
        for action in self._svc_config.get_action():
            act = Action(self, action)
            name = action.get_name()
            self.actions[name] = act
            setattr(self, name, act)
        self.initialized.set_result(True)


    @property
    def hostname(self):
        return self._base_url.split('/')[-1]

    @property
    def controlURL(self):
        return '%s/%s' % (self._base_url,
                          self._config.get_controlURL().strip('/'))

    @property
    def serviceType(self):
        return self._config.get_serviceType()
