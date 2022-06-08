import param
from panel import Column
from panel.widgets import Button
from measfunc.AlazarAcquisitionController import zero_if_none


class AlazarChannelSettings(param.Parameterized):
    #int_delay = param.Number(0, precedence=0, label='Int delay (ms)')
    int_time = param.Number(4e-6, precedence=1, label='Int time (ms)')
    samples_to_exclude_start = param.Integer(0, label='Samples to skip start (Nr)')
    samples_to_exclude_end = param.Integer(0, label='Samples to skip end (Nr)')
    samples_per_record = param.Integer(200, label='Samples per record (Nr)')
    alazar_channel = param.ObjectSelector(default='A', objects=['A', 'B'])
    buffers_per_acquisition = param.Integer(23, label='Buffers per acquisition (Nr)')
    num_averages = param.Integer(23, label='Num averages (Nr)')
    records_per_buffer = param.Integer(23, label='Records per buffer (Nr)')
    integrate_samples= param.Boolean(False, doc="Intergrade Samples")


class AlazarChannelConfig():

    def __init__(self, controller, aktion):

        self.controller = controller
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
        acquisition_kwargs = {'mode': 'NPT',
                              'records_per_buffer': self.settings.records_per_buffer,
                              'buffers_per_acquisition': self.settings.buffers_per_acquisition,
                              'channel_selection': self.settings.alazar_channel,
                              'buffer_timeout': 3000,
                              'interleave_samples': 'ENABLED'}

        self.controller.setup_acquisition(self.settings.int_time*1e-3,
                                          self.settings.samples_per_record,
                                          acquisition_kwargs=acquisition_kwargs,
                                          alazar_kwargs={})
        self.controller.samples_to_exclude_start(self.settings.samples_to_exclude_start)
        self.controller.samples_to_exclude_end(self.settings.samples_to_exclude_end)
        #self.controller.int_delay.set(self.settings.int_delay*1e-3)
        self.get_settings()
        if self.settings.integrate_samples:
            #self.channel.buffers_per_acquisition.set(self.settings.buffers_per_acquisition)
            self.aktion(self.settings.records_per_buffer,
                        self.settings.buffers_per_acquisition)
        else:
            self.aktion(self.settings.records_per_buffer,
                        self.settings.samples_per_record -self.settings.samples_to_exclude_start -self.settings.samples_to_exclude_end)

    def get_settings_event(self, event):
        self.get_settings()

    def get_settings(self):
        self.controller.acquisition_config
        #self.settings.int_delay = self.controller.int_delay()*1e3
        self.settings.int_time = self.controller.acquisition_time*1e3
        self.settings.samples_per_record = self.controller.acquisition_config['samples_per_record']
        self.settings.samples_to_skip_start = zero_if_none(self.controller.samples_to_exclude_start())
        self.settings.samples_to_skip_end = zero_if_none(self.controller.samples_to_exclude_end())
        self.settings.alzar_channel = self.controller.acquisition_config['channel_selection']
        self.settings.buffers_per_acquisition = self.controller.acquisition_config['buffers_per_acquisition']
        self.settings.records_per_buffer = self.controller.acquisition_config['records_per_buffer']
