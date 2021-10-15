import param
from panel import Column
from panel.widgets import Button


class AlazarChannelSettings(param.Parameterized):
    int_delay = param.Number(0, precedence=0)
    int_time = param.Number(4e-6, precedence=1)
    samples_per_record = param.Integer(200)
    alazar_channel = param.ObjectSelector(default='A', objects=['A', 'B'])
    buffers_per_acquisition = param.Integer(23)
    num_averages = param.Integer(23)
    records_per_buffer = param.Integer(23)


class AlazarChannelConfig():

    def __init__(self, controller, channel, aktion):

        self.controller = controller
        self.channel = channel
        self.aktion = aktion
        self.settings = AlazarChannelSettings()
        self.get_settings()
        self.set_button = Button(name='set', button_type='primary')
        self.set_button.on_click(self.config_event)
        self.get_button = Button(name='get', button_type='primary')
        self.get_button.on_click(self.get_settings_event)
        self.col = Column(self.settings, self.get_button, self.set_button)

    def config_event(self, event):
        self.config()

    def config(self):
        self.controller.int_delay.set(self.settings.int_delay)
        self.controller.int_time.set(self.settings.int_time)
        # self.controller.sample_per_records.set(self.settings.sample_per_records)

        self.channel.alazar_channel.set(self.settings.alazar_channel)
        #self.channel.buffers_per_acquisition.set(self.settings.buffers_per_acquisition)
        self.channel.num_averages.set(self.settings.num_averages)
        self.channel.records_per_buffer.set(self.settings.records_per_buffer)
        self.channel.prepare_channel()
        self.get_settings()
        self.aktion(self.settings.records_per_buffer,
                    self.settings.samples_per_record)

    def get_settings_event(self, event):
        self.get_settings()

    def get_settings(self):
        self.settings.int_delay = self.controller.int_delay()
        self.settings.int_time = self.controller.int_time()
        self.settings.samples_per_record = self.controller.samples_per_record()

        self.settings.alzar_channel = self.channel.alazar_channel() 
        self.settings.buffers_per_acquisition = self.channel.buffers_per_acquisition()
        self.settings.num_averages = self.channel.num_averages()
        self.settings.records_per_buffer = self.channel.records_per_buffer()
