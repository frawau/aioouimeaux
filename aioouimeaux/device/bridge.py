
import asyncio as aio
from aioouimeaux.device import Device

from xml.etree import cElementTree as et


class Bridge(Device):
    device_type = "Bridge"
    Lights = {}
    Groups = {}

    def __repr__(self):
        self.bridge_get_lights()
        self.bridge_get_groups()
        return '<WeMo Bridge "{}", Lights: {}, Groups: {}>'.format(self.name, len(self.Lights), len(self.Groups))
    def bridge_get_lights(self):
        endfuture = aio.Future()
        future = self.basicevent.GetMacAddr().get('PluginUDN')
        aio.ensure_future(self.bridge_get_lights_UDN(future,endfuture))

    async def bridge_get_lights_UDN(self,future, endfuture):
        await future
        try:
            UDN = future.result()
            future = self.bridge.GetEndDevices(DevUDN=UDN,ReqListType='PAIRED_LIST')
            await future
            endDevices = future.result()
            endDeviceList = et.fromstring(endDevices.get('DeviceLists'))

            for light in endDeviceList.iter('DeviceInfo'):
                if self.light_name(light) in self.Lights:
                    pass
                else:
                    self.Lights[self.light_name(light)] = light
            endfuture.set_result(self.Lights)
        except Exception as e:
            endfuture.set_exception(e)


    def bridge_get_groups(self):
        endfuture = aio.Future()
        future = self.basicevent.GetMacAddr().get('PluginUDN')
        aio.ensure_future(self.bridge_get_groups_UDN(future,endfuture))

    async def bridge_get_groups_UDN(self,future, endfuture):
        await future
        try:
            UDN = future.result()
            future = self.bridge.GetEndDevices(DevUDN=UDN,ReqListType='PAIRED_LIST')
            await future
            endDevices = future.result()
            endDeviceList = et.fromstring(endDevices.get('DeviceLists'))

            for group in endDeviceList.iter('GroupInfo'):
                if self.group_name(group) in self.Groups:
                    pass
                else:
                    self.Groups[self.group_name(group)] = group
            endfuture.set_result(self.Groups)
        except Exception as e:
            endfuture.set_exception(e)

    def light_attributes(self, light):
        return {
            'devIndex' : light.find('DeviceIndex').text,
            'devID' : light.find('DeviceID').text,
            'name' : light.find('FriendlyName').text,
            'iconvalue' : light.find('IconVersion').text,
            'firmware' : light.find('FirmwareVersion').text,
            'capabilities' : light.find('CapabilityIDs').text,
            'state' : light.find('CurrentState').text,
            'manufacturer' : light.find('Manufacturer').text,
            'model' : light.find('ModelCode').text,
            'certified' : light.find('WeMoCertified').text
        }

    def group_attributes(self, group):
        return {
            'GroupID' : group.find('GroupID').text,
            'name' : group.find('GroupName').text,
            'capabilities' : group.find('GroupCapabilityIDs').text,
            'state': group.find('GroupCapabilityValues').text
        }

    def light_name(self, light):
        return self.light_attributes(light).get('name')

    def group_name(self, group):
        return self.group_attributes(group).get('name')

    def light_get_id(self, light):
        return self.light_attributes(light).get('devID')

    def group_get_id(self, group):
        return self.group_attributes(group).get('GroupID')

    def light_get_state(self, light):
        attr = self.light_attributes(light).get('state').split(':', 1)[0].split(',')
        state = attr[0] # 0 (off) or 1 (on)
        dim = attr[1]   # 0-255 dark to bright
        return {
            'state' : state,
            'dim' : dim
        }

    def group_get_state(self, group):
        attr = self.group_attributes(group).get('state').split(':', 1)[0].split(',')
        state = attr[0] # 0 (off) or 1 (on)
        dim = attr[1]   # 0-255 dark to bright
        return {
            'state' : state,
            'dim' : dim
        }

    def light_set_state(self, light, state=None, dim=None):
        if state == None:
            state = self.light_get_state(light).get('state')
        if dim == None:
            dim = self.light_get_state(light).get('dim')

        sendState = '&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;&lt;DeviceStatus&gt;&lt;IsGroupAction&gt;NO&lt;/IsGroupAction&gt;&lt;DeviceID available=&quot;YES&quot;&gt;{devID}&lt;/DeviceID&gt;&lt;CapabilityID&gt;10006&lt;/CapabilityID&gt;&lt;CapabilityValue&gt;{state}&lt;/CapabilityValue&gt;&lt;CapabilityID&gt;10008&lt;/CapabilityID&gt;&lt;CapabilityValue&gt;{dim}&lt;/CapabilityValue&gt;&lt;/DeviceStatus&gt;'.format(devID=self.light_get_id(light),state=state,dim=dim)
        result = aio.Future
        future = self.bridge.SetDeviceStatus(DeviceStatusList=sendState)
        aio.ensure_future(self.light_set_state_bottom(future,result))
        return result

    async def light_set_state_bottom(self,future, result_fut):
        await future
        try:
            result_fut.set_result(future.result())
        except Exception as e:
            result_fut.set_exception(e)


    def group_set_state(self, group, state=None, dim=None):
        if state == None:
            state = self.group_get_state(group).get('state')
        if dim == None:
            dim = self.group_get_state(group).get('dim')

        sendState = '&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;&lt;DeviceStatus&gt;&lt;IsGroupAction&gt;YES&lt;/IsGroupAction&gt;&lt;DeviceID available=&quot;YES&quot;&gt;{groupID}&lt;/DeviceID&gt;&lt;CapabilityID&gt;10006&lt;/CapabilityID&gt;&lt;CapabilityValue&gt;{state}&lt;/CapabilityValue&gt;&lt;CapabilityID&gt;10008&lt;/CapabilityID&gt;&lt;CapabilityValue&gt;{dim}&lt;/CapabilityValue&gt;&lt;/DeviceStatus&gt;'.format(groupID=self.group_get_id(group),state=state,dim=dim)
        result = aio.Future
        future = self.bridge.SetDeviceStatus(DeviceStatusList=sendState)
        aio.ensure_future(self.group_set_state_bottom(future,result))
        return result

    async def group_set_state_bottom(self,future, result_fut):
        await future
        try:
            result_fut.set_result(future.result())
        except Exception as e:
            result_fut.set_exception(e)

