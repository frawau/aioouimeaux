import logging
import asyncio as aio
import socket
from struct import pack
from functools import partial

log = logging.getLogger(__name__)

UPNP_PORT = 1900
UPNP_ADDR = "239.255.255.250"
UPNP6_ADDR = "ff05::c"
#UPNP6_ADDR = "ff08::c"
#UPNP6_ADDR = "ff0e::c"

_DISCOVERYTIMEOUT = 360

class UPnPLoopbackException(Exception):
    """
    Using loopback interface as callback IP.
    """
class upnp_info(object):
    def __init__(self):
        self.name = None
        self.type = None
        self.port = None
        self.address = None
        self.mac = None
        self.properties = {}

    def __repr__(self):
        repr = 'name:\t{}\ntype:\t{}\nport:\t{}\naddress:{}\nmac:\t{}\nproperties:\n'.format(self.name,self.type, self.port, self.address, self.mac)
        for x,y in self.properties.items():
            repr += "\t{}:\t{}\n".format(x,y)
        return repr

class UPnP(aio.Protocol):
    def __init__(self, loop,addr,handler,future):
        super().__init__()
        self.loop = loop
        self.transport = None
        self.addr=addr
        self.handler = handler
        self.task = None
        self.clients = {}
        self.broadcast_cnt=0
        self.future=future

    def connection_made(self, transport):
        self.transport = transport
        self.future.set_result(self)
        sock = self.transport.get_extra_info('socket')
        sock.settimeout(3)
        addrinfo = socket.getaddrinfo(self.addr, None)[0]
        ttl = pack('@i', 1)
        if addrinfo[0] == socket.AF_INET: # IPv4
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        else:
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)

    def _broadcast(self):
        request = '\r\n'.join(("M-SEARCH * HTTP/1.1",
                               "HOST:{}:{}",
                               "ST:upnp:rootdevice",
                               "MX:2",
                               'MAN:"ssdp:discover"',
                               "", "")).format(self.addr,UPNP_PORT)
        self.transport.sendto(request.encode(), (self.addr,UPNP_PORT))


    def datagram_received(self, data, addr):
        info = upnp_info()
        info.address = addr[0]
        info.port = addr[1]
        headers = {}
        for line in data.decode("ascii").split("\r\n"):
            try:
                header, value = line.split(":", 1)
                headers[header.lower()] = value.strip()
            except:
                pass

        if (headers.get('x-user-agent', None) == 'redsonic'):
            usn=headers.get('usn',None)
            if usn is not None:
                usn = usn.split(":")[1]
                if usn not in self.clients:
                    log.debug("Found WeMo at {}".format(usn))
                    self.clients[usn] = headers
                    if self.handler:
                        self.handler(self,address=addr,headers=headers)
                else:
                    self.clients[usn] = headers

    def error_received(self, name):
        pass
        #print('Error received:', exc)

    def connection_lost(self, udn):
        udn = udn.split(":")[1]
        del self.clients[udn]
        pass

    def broadcast(self,seconds,timeout=_DISCOVERYTIMEOUT):
        self.task= aio.get_event_loop().create_task(self._do_broadcast(seconds,timeout))

    async def _do_broadcast(self,seconds,timeout):
        count = seconds
        while True:
            if count == 0:
                count = seconds
                await aio.sleep(timeout)
            self._broadcast()
            count -= 1
            await aio.sleep(1)

    def close(self):
        try:
            self.task.cancel()
        except:
            pass

def test():
    logging.basicConfig(level=logging.DEBUG)
    broadcaster = {}
    def handler(sender, **kwargs):
        print("I GOT ONE")
        print(kwargs['address'], kwargs['headers'])


    for maddr in [UPNP_ADDR]:
        addrinfo = socket.getaddrinfo(maddr, None)[0]
        sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
        loop = aio.get_event_loop()
        future = aio.Future()
        connect = loop.create_datagram_endpoint(
            lambda: UPnP(loop,maddr,handler,future),
            sock=sock
        )
        broadcaster[maddr] = loop.run_until_complete(connect)
        broadcaster[maddr][1].broadcast(2)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n", "Exiting at user's request")
    finally:
        # Close the server
        for transport, protocol in broadcaster.values():
            try:
                if protocol.task:
                    protocol.task.cancel()
            except:
                pass
            transport.close()
        loop.close()


if __name__ == "__main__":
    test()
