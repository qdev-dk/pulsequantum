import param
from panel import Column, Row, pane
from panel.widgets import Button
from panel import extension


class MoreSettings(param.Parameterized):
    channel_1_amp = param.Parameter(default =4.5, doc='Channel amp')
    channel_2_amp = param.Parameter(default =4.5, doc='Channel amp')
    channel_3_amp = param.Parameter(default =4.5, doc='Channel amp')
    channel_4_amp = param.Parameter(default =4.5, doc='Channel amp')


class MoreConfig():
    def __init__(self,sequencebuilder,video):
        self.sequencebuilder = sequencebuilder
        self.video = video
        self.settings = MoreSettings()
        self.set_button = Button(name='set', button_type='primary')
        self.set_button.on_click(self.config_event)
        self.get_button = Button(name='get', button_type='primary')
        self.get_button.on_click(self.get_settings_event)
        self.upload_button = Button(name='Upload')
        self.upload_button.on_click(self.upload_event)
        self.config()
        self.get_settings()
        self.col = Row(Column(self.settings, self.set_button,self.get_button),Column(self.upload_button))

    def config_event(self, event):
        self.config()

    def config(self):
        self.sequencebuilder.channel_1_amp.set(self.settings.channel_1_amp)
        self.sequencebuilder.channel_2_amp.set(self.settings.channel_2_amp)
        self.sequencebuilder.channel_3_amp.set(self.settings.channel_3_amp)
        self.sequencebuilder.channel_4_amp.set(self.settings.channel_4_amp)
    
    def get_settings_event(self, event):
        self.get_settings()

    def get_settings(self):
        self.settings.channel_1_amp = self.sequencebuilder.channel_1_amp()
        self.settings.channel_2_amp = self.sequencebuilder.channel_2_amp()
        self.settings.channel_3_amp = self.sequencebuilder.channel_3_amp()
        self.settings.channel_4_amp = self.sequencebuilder.channel_4_amp()

    def upload_event(self, event):
        self.upload_button.button_type = 'danger'
        self.sequencebuilder.uploadToAWG()
        self.upload_button.button_type = 'success'

