from broadbean import sequence
import param
from panel import Column, Row, pane
from panel.widgets import Button
from pulsequantum.livestream.sweepintrument import SequenceBuilder

class SweepSettings(param.Parameterized):

    scan_options = param.ObjectSelector(objects=['Steps', 'Triangular', 'Sinusoidal'])
    fast_channel = param.Integer(1)
    slow_channel = param.Integer(2)
    fast_range = param.Parameter(default=3e-2, doc="x range")
    slow_range = param.Parameter(default=3e-2, doc="y range")
    x_dc_offecet = param.Parameter(default=0, doc="x dc offecet")
    y_dc_offecet = param.Parameter(default=0, doc="y dc offecet")
    fast_time = param.Parameter(default=3e-3, doc="x time")
    slow_steps = param.Parameter(default=40, doc="y steps")




class SweepConfig():

    def __init__(self, aktion):
        self.sequencebuilder = SequenceBuilder('ThisName')
        self.aktion = aktion
        self.settings = SweepSettings()
        #self.get_settings()
        self.set_button = Button(name='set', button_type='primary')
        self.set_button.on_click(self.config_event)
        self.get_button = Button(name='get', button_type='primary')
        self.get_button.on_click(self.get_settings_event)
        self.config()
        self.fig = self.sequencebuilder.seq.plot()
        self.figpane = pane.Matplotlib(self.fig, dpi=144)
        self.col = Row(Column(self.settings, self.get_button, self.set_button),self.figpane)

    def config_event(self, event):
        self.config()

    def config(self):
        """
        function for config of 
        """
        self.sequencebuilder.fast_channel.set(self.settings.fast_channel)
        self.sequencebuilder.slow_channel.set(self.settings.slow_channel)
        self.sequencebuilder.fast_range.set(self.settings.fast_range)
        self.sequencebuilder.slow_range.set(self.settings.slow_range)
        self.sequencebuilder.fast_time.set(self.settings.fast_time)
        self.sequencebuilder.slow_steps.set(self.settings.slow_steps)
        self.sequencebuilder.sweep_pulse()
        self.fig = self.sequencebuilder.seq.plot()
        self.figpane = pane.Matplotlib(self.fig, dpi=144)

        self.get_settings()
        #self.aktion()

    def get_settings_event(self, event):
        self.get_settings()

    def get_settings(self):
        self.settings.fast_channel = self.sequencebuilder.fast_channel()
        self.settings.slow_channel = self.sequencebuilder.slow_channel()
        self.settings.fast_range = self.sequencebuilder.fast_range()
        self.settings.slow_range = self.sequencebuilder.slow_range()
        self.settings.fast_time = self.sequencebuilder.fast_time()
        self.settings.slow_steps = self.sequencebuilder.slow_steps()




