from .switch import Switch

class LightSwitch(Switch):

    def __repr__(self):
        return f'<WeMo LightSwitch "{self.name}">'
