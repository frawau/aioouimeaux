from functools import wraps
import re
import struct
import time

import asyncio as aio
import aiohttp as aioh
import netifaces


def tz_hours():
    delta = time.localtime().tm_hour - time.gmtime().tm_hour
    sign = '-' if delta < 0 else ''
    return "%s%02d.00" % (sign, abs(delta))


def is_dst():
    return 1 if time.localtime().tm_isdst else 0


def get_timesync():
    timesync = """
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
 <s:Body>
  <u:TimeSync xmlns:u="urn:Belkin:service:timesync:1">
   <UTC>{utc}</UTC>
   <TimeZone>{tz}</TimeZone>
   <dst>{dst}</dst>
   <DstSupported>{dstsupported}</DstSupported>
  </u:TimeSync>
 </s:Body>
</s:Envelope>""".format(
        utc=int(time.time()),
        tz=tz_hours(),
        dst=is_dst(),
        dstsupported=is_dst()).strip()
    return timesync


def get_ip_address():
    return netifaces.ifaddresses(netifaces.gateways()["default"][netifaces.AF_INET][1])[netifaces.AF_INET][0]["addr"]

def matcher(match_string):
    pattern = re.compile('.*?'.join(re.escape(c) for c in match_string.lower()))
    def matches(s):
        return pattern.search(s.lower()) is not None
    return matches


# This is pretty arbitrary. I'm choosing, for no real reason, the length of
# a subscription.
_RETRIES = 3
_DELAY = 3


def get_retries():
    return _RETRIES

async def requests_get(url, *, allow_redirects=True, **kwargs):
    remaining = _RETRIES
    while remaining:
        remaining -= 1
        try:
            async with aioh.ClientSession() as session:
                async with session.get(url, allow_redirects=allow_redirects, **kwargs) as response:
                    if response.status != 200:
                        raise aioh.ClientConnectionError
                    response.raw_body = await response.read()
                    return response
        except aioh.ClientConnectionError:
            if not remaining:
                raise
            aio.sleep(_DELAY)

async def requests_post(url, *, data=None, **kwargs):
    remaining = _RETRIES
    while remaining:
        remaining -= 1
        try:
            async with aioh.ClientSession() as session:
                async with session.post(url, data = data, **kwargs) as response:
                    response.raw_body = await response.read()
                    return response
        except aioh.ClientConnectionError:
            if not remaining:
                raise
            aio.sleep(_DELAY)

async def requests_request(method, url, **kwargs):
    remaining = _RETRIES
    while remaining:
        remaining -= 1
        try:
            async with aioh.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    response.raw_body = await response.read()
                    return response
        except aioh.ClientConnectionError:
            if not remaining:
                raise
            aio.sleep(_DELAY)

