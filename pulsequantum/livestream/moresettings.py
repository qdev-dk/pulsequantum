import param
from panel import Column, Row, pane
from panel.widgets import Button


class MoreSettings(param.Parameterized):
    channelamps = [4.5,4.5,4.5,4.5]
    channelselect = param.ObjectSelector(default="Channel 1", objects=['Channel 1', 'Channel 2', 'Channel 3', 'Channel 4'], doc='Channel Select')
    channelamp = param.Parameter(default =channelamps[0], doc='Channel amp')
    @param.depends('channelselect', watch=True)
    def _update_channelamp(self):
        self.channelamp = self.channelamps[self.param['channelselect'].objects.index(self.channelselect)]



class MoreConfig():
    def __init__(self,sequencebuilder,video):
        self.sequencebuilder = sequencebuilder
        self.video = video
        self.settings = MoreSettings()
        self.set_button = Button(name='set', button_type='primary')
        self.set_button.on_click(self.config_event)
        self.get_button = Button(name='get', button_type='primary')
        self.get_button.on_click(self.get_settings_event)
        self.col = Row(Column(self.settings, self.set_button,self.get_button))

    def config_event(self, event):
        self.config()

    def config(self):
        self.settings.channelamps[self.settings.param['channelselect'].objects.index(self.settings.channelselect)] = 3
    
    def get_settings_event(self, event):
        self.get_settings()

    def get_settings(self):
        pass
