import param
from panel import Column
from panel.widgets import Button


class AlazarChannel(param.Parameterized):
    int_delay = param.Number(0, precedence=0)
    int_time = param.Number(4e-6, precedence=1)
    samples_per_record = param.Integer(200)
    alazar_channel = param.ObjectSelector(objects=['A', 'B'])
    buffers_per_acquisition = param.Integer(23)
    num_averages = param.Integer(23)
    records_per_buffer = param.Integer(23)


class AlazarChannelConfig():

    def __init__(self, controler, channel):

        self.controler = controler
        self.channel == channel
        self.settings = AlazarChannel()
        self.get_settings()
        self.set_button = Button(name='set', button_type='primary')
        self.set_button.on_click(self.config_event)
        self.get_button = Button(name='get', button_type='primary')
        self.get_button.on_click(self.get_settings_event)
        self.col = Column(self.settings, self.get_button, self.set_button)

    def config_event(self, event):
        self.config()

    def config(self):
        self.controler.int_delay.set(self.settings.int_delay)
        self.controler.int_time.set(self.settings.int_time)
        # self.controler.sample_per_records.set(self.settings.sample_per_records)

        self.channel.alzar_channel.set(self.settings.alazar_channel)
        self.channel.buffers_per_acquisition.set(self.settings.buffers_per_acquisition)
        self.channel.num_averages.set(self.settings.num_averages)
        self.channel.records_per_buffer.set(self.settings.records_per_buffer)
        self.channel.prepare_channel()

    def get_settings_event(self, event):
        self.get_settings()

    def get_settings(self):
        self.settings.int_delay = self.controler.int_delay()
        self.settings.int_time = self.controler.int_time()
        self.settings.sample_per_records = self.controler.sample_per_records()

        self.settings.alzar_channel = self.channel.alazar_channel()
        self.settings.buffers_per_acquisition = self.channel.buffers_per_acquisition()
        self.settings.num_averages = self.channel.num_averages()
        self.settings.records_per_buffer = self.channel.records_per_buffer()
