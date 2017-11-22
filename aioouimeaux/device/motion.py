from aioouimeaux.device import Device

class Motion(Device):
    device_type = "Motion"

    def __repr__(self):
        return '<WeMo Motion "{}">'.format(self.name)
