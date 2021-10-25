import time
from broadbean import sequence
from pulsequantum.livestream.seqplot import plotter
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

    def __init__(self, aktion, awg=None):
        self.sequencebuilder = AWGController('ThisName',awg=awg)
        self.aktion = aktion
        self.settings = SweepSettings()
        #self.get_settings()
        self.set_button = Button(name='set', button_type='primary')
        self.set_button.on_click(self.config_event)
        self.get_button = Button(name='get', button_type='primary')
        self.get_button.on_click(self.get_settings_event)
        self.run_button = Button(name='Run')
        self.run_button.on_click(self.run_event)
        self.upload_button = Button(name='Upload')
        self.upload_button.on_click(self.upload_event)
        #self.fig = None #self.sequencebuilder.seq.plot()
        self.figpane = pane.Matplotlib(None, dpi=144)
        self.config()
        self.col = Row(Column(self.settings, self.get_button, self.set_button), Column(self.figpane, self.upload_button, self.run_button))

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
        self.fig = plotter(self.sequencebuilder.seq.get())
        self.figpane.object = self.fig
        #self.col = Row(Column(self.settings, self.get_button, self.set_button),self.plotpane())

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

    def upload_event(self, event):
        self.sequencebuilder.uploadToAWG()

    def run_event(self, event):
        self.sequencebuilder.runAWG()

    def plotpane(self):
        return pane.Matplotlib(plotter(self.sequencebuilder.seq.get()), dpi=144)








class AWGController(SequenceBuilder):
    def __init__(self, name: str, awg=None, **kwargs):
        super().__init__(name, **kwargs)
        self.awg = awg        
    def uploadToAWG(self, awg_amp: list = [0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5]) -> None:
        if '5014' in str(self.awg.__class__):
            #for i,  chan in enumerate(self.seq.get().channels):
            #    self.awg.channels[chan].AMP(float(chbox[chan-1].text()))
            self.awg.ch1_amp(awg_amp[0])
            self.awg.ch2_amp(awg_amp[1])
            self.awg.ch3_amp(awg_amp[2])
            self.awg.ch4_amp(awg_amp[3])
            package = self.seq.get().outputForAWGFile()
            start_time = time.time()
            self.awg.make_send_and_load_awg_file(*package[:])
            print("Sequence uploaded in %s seconds" %(time.time()-start_time));
        elif '5208' in str(self.awg.__class__):
            self.seq.get().name = 'sequence_from_gui'
            self.awg.mode('AWG')
            for chan in self.seq.get().channels:
                self.awg.channels[chan-1].resolution(12)
                self.awg.channels[chan-1].awg_amplitude(awg_amp[chan-1])
                self.seq.get().setChannelAmplitude(chan, self.awg.channels[chan-1].awg_amplitude())
            self.awg.clearSequenceList()
            self.awg.clearWaveformList()
            self.awg.sample_rate(self.seq.get().SR)
            self.awg.sample_rate(self.seq.get().SR)
            
            seqx_input = self.seq.get().outputForSEQXFile()
            start_time=time.time()
            seqx_output = self.awg.makeSEQXFile(*seqx_input)
            # transfer it to the awg harddrive
            self.awg.sendSEQXFile(seqx_output, 'sequence_from_gui.seqx')
            self.awg.loadSEQXFile('sequence_from_gui.seqx')
            #time.sleep(1.300)
            for i,  chan in enumerate(self.seq.get().channels):       
                self.awg.channels[chan-1].setSequenceTrack('sequence_from_gui', i+1)
                self.awg.channels[chan-1].state(1)
            print("Sequence uploaded in %s seconds" %(time.time()-start_time))
 
        else:
            print('Choose an AWG model')

    def runAWG(self):
        if '5014' in str(self.awg.__class__):
            self.awg.run()
        else:
            seq_chan = self.seq.get().channels
            for i, chan in enumerate(self.awg.channels):
                if i+1 in seq_chan:
                    chan.state(1)
                else:
                    chan.state(0)
            self.awg.play()