import time
import numpy as np
from broadbean import sequence
from pulsequantum.livestream.seqplot import plotter
import param
from panel import Column, Row, pane
from panel.widgets import Button
from pulsequantum.livestream.sweepintrument import SequenceBuilder

class SweepSettings(param.Parameterized):

    scan_options = param.ObjectSelector(default="Steps", objects=['Steps', 'Triangular', 'Sinusoidal', 'SinusidalOneTri'])
    fast_channel = param.Integer(1)
    slow_channel = param.Integer(2)
    fast_range = param.Parameter(label='Fast range (mV)', default=30, doc="x range")
    slow_range = param.Parameter(label='Slow range (mV)', default=30, doc="y range")
    #x_dc_offecet = param.Parameter(default=0, doc="x dc offecet")
    #y_dc_offecet = param.Parameter(default=0, doc="y dc offecet")
    fast_time = param.Parameter(label='Fast time (ms)', default=3, doc="x time")
    slow_steps = param.Parameter(label='Slow steps (Nr)', default=40, doc="y steps")
    marker_duration = param.Parameter(label='Marker Duration (ms)', default=1e-2, doc="marker duration")
    delay_time = param.Parameter(label='Delay time (ms)', default=0, doc="delay time")
    awg_sr = param.Parameter(label='Samplerate (Hz)', default=1.2e7, doc="AWG sample rate")
    applay_inverse_hp_filter = param.Boolean(default=False, doc="applay_inverse_HP_filter")
    hp_frequency = param.Parameter(label='HP frequency (Hz)', default=300, doc="frequency of the HP filter")


class SweepConfig():

    def __init__(self, video, awg=None,  moresettings=None):
        self.sequencebuilder = AWGController(f'awg{video.name}',awg=awg)
        self.video = video
        self.settings = SweepSettings()
        self.moresettings = moresettings
        #self.get_settings()
        self.set_button = Button(name='set', button_type='primary')
        self.set_button.on_click(self.config_event)
        self.get_button = Button(name='get', button_type='primary')
        self.get_button.on_click(self.get_settings_event)
        self.run_button = Button(name='Run', button_type='default')
        self.run_button.on_click(self.run_event)
        self.upload_button = Button(name='Upload',button_type='default')
        self.upload_button.on_click(self.upload_event)
        #self.fig = None #self.sequencebuilder.seq.plot()
        self.figpane = pane.Matplotlib(None, dpi=144)
        self.config()
        self.col = Row(Column(self.settings, self.get_button, self.set_button), Column(self.figpane, self.upload_button, self.run_button))

    def config_event(self, event):
        self.set_button.button_type = 'warning'
        self.set_button.disabled = True
        try:
            self.config()
            self.set_button.disabled = False
            self.set_button.button_type = 'primary'
        except Exception as config_ex:
            self.set_button.disabled = False
            self.set_button.button_type = 'primary'
            self.get_settings()

    def config(self):
        """
        function for config of 
        """
        self.sequencebuilder.fast_channel.set(self.settings.fast_channel)
        self.sequencebuilder.slow_channel.set(self.settings.slow_channel)
        self.sequencebuilder.fast_range.set(self.settings.fast_range*1e-3)
        self.sequencebuilder.slow_range.set(self.settings.slow_range*1e-3)
        self.sequencebuilder.fast_time.set(self.settings.fast_time*1e-3)
        self.sequencebuilder.slow_steps.set(self.settings.slow_steps)
        self.sequencebuilder.marker_duration.set(self.settings.marker_duration*1e-3)
        self.sequencebuilder.delay_time.set(self.settings.delay_time*1e-3)
        self.sequencebuilder.awg_sr.set(self.settings.awg_sr)
        self.sequencebuilder.applay_inverse_hp_filter.set(self.settings.applay_inverse_hp_filter)
        self.sequencebuilder.hp_frequency.set(self.settings.hp_frequency)
        
        self.sequencebuilder.awg_amplitude.set(self.moresettings.awg_amplitude)
        self.sequencebuilder.divider_fast.set(self.moresettings.divider_fast)
        self.sequencebuilder.divider_slow.set(self.moresettings.divider_slow)
        
        if self.settings.scan_options  == 'Steps':
            self.sequencebuilder.sweep_pulse()
        elif self.settings.scan_options == 'Sinusoidal':
            self.sequencebuilder.sweep_sine()
        elif self.settings.scan_options == 'SinusidalOneTri':
            self.sequencebuilder.sweep_sineone()
        self.video.x.V_start.set(-self.settings.fast_range*1e-3/2)
        self.video.x.V_stop.set(self.settings.fast_range*1e-3/2)
        self.video.x.V_axis.reset()
        self.video.y.V_start.set(-self.settings.slow_range*1e-3/2)
        self.video.y.V_stop.set(self.settings.slow_range*1e-3/2)
        self.video.y.V_axis.reset()
 
            
        self.get_settings()
        self.update_video()
        self.figpane.loading = True      
        self.fig = plotter(self.sequencebuilder.seq.get())
        self.figpane.object = self.fig
        self.figpane.loading = False
        #self.col = Row(Column(self.settings, self.get_button, self.set_button),self.plotpane())


        #self.aktion()

    def get_settings_event(self, event):
        self.get_settings()

    def get_settings(self):
        self.settings.fast_channel = self.sequencebuilder.fast_channel()
        self.settings.slow_channel = self.sequencebuilder.slow_channel()
        self.settings.fast_range = self.sequencebuilder.fast_range()*1e3
        self.settings.slow_range = self.sequencebuilder.slow_range()*1e3
        self.settings.fast_time = self.sequencebuilder.fast_time()*1e3
        self.settings.slow_steps = self.sequencebuilder.slow_steps()
        self.settings.marker_duration = self.sequencebuilder.marker_duration()*1e3
        self.settings.delay_time = self.sequencebuilder.delay_time()*1e3
        self.settings.awg_sr = self.sequencebuilder.awg_sr()
        self.settings.applay_inverse_hp_filter = self.sequencebuilder.applay_inverse_hp_filter()
        self.settings.hp_frequency = self.sequencebuilder.hp_frequency() 
        
        self.moresettings.awg_amplitude = self.sequencebuilder.awg_amplitude()
        self.moresettings.divider_fast = self.sequencebuilder.divider_fast()
        self.moresettings.divider_slow = self.sequencebuilder.divider_slow()

    def update_video(self):
        try:
            int_time = 1e-3*self.settings.fast_time*0.98
            min_sr = 2048/int_time
            allowed_srs = np.asarray(list(self.video.alazarsettings.settings.param.sample_rate.get_range().keys()))[:-2].astype(int)
            sr = allowed_srs[allowed_srs > min_sr].min()
            self.video.alazarsettings.settings.sample_rate = sr
            points = sr*int_time - (sr*int_time%128)
            int_time = points/sr
            self.video.alazarchansettings.settings.int_time = int_time*1e3

            self.video.alazarchansettings.settings.records_per_buffer = self.settings.slow_steps
            if self.settings.scan_options == 'Sinusoidal':
                self.video.alazarchansettings.settings.buffers_per_acquisition = self.settings.slow_steps
                self.video.alazarchansettings.settings.integrate_samples = True
                self.video.alazarchansettings.settings.int_time = self.settings.marker_duration
            self.video.alazarsettings.config()
            self.video.alazarchansettings.config()
        except Exception as update_video_ex:
            pass

    def upload_event(self, event):
        self.upload_button.button_type = 'danger'
        self.run_button.button_type = 'danger'
        self.sequencebuilder.uploadToAWG()
        self.upload_button.button_type = 'success'


    def run_event(self, event,button=None):
        self.sequencebuilder.runAWG(button = self.run_button)


    def plotpane(self):
        return pane.Matplotlib(plotter(self.sequencebuilder.seq.get()), dpi=144)








class AWGController(SequenceBuilder):
    def __init__(self, name: str, awg=None, **kwargs):
        super().__init__(name, **kwargs)
        self.awg = awg        
    def uploadToAWG(self) -> None:
        if '5014' in str(self.awg.__class__):
            #for i,  chan in enumerate(self.seq.get().channels):
            #    self.awg.channels[chan].AMP(float(chbox[chan-1].text()))
            self.awg.ch1_amp(self.awg_amplitude())
            self.awg.ch2_amp(self.awg_amplitude())
            self.awg.ch3_amp(self.awg_amplitude())
            self.awg.ch4_amp(self.awg_amplitude())
            self.seq.seq.setSR(self.awg_sr())
            self.awg.clock_freq(self.awg_sr())
            package = self.seq.get().outputForAWGFile()
            start_time = time.time()
            self.awg.make_send_and_load_awg_file(*package[:])
            print("Sequence uploaded in %s seconds" %(time.time()-start_time));
        elif '5208' in str(self.awg.__class__):
            self.seq.get().name = 'sequence_from_gui'
            self.awg.mode('AWG')
            for chan in self.seq.get().channels:
                self.awg.channels[chan-1].resolution(12)
                self.awg.channels[chan-1].awg_amplitude(self.awg_amplitude())
                self.seq.get().setChannelAmplitude(chan, self.awg.channels[chan-1].awg_amplitude())
            self.awg.clearSequenceList()
            self.awg.clearWaveformList()
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

    def runAWG(self,button):
        self.run_button = button
        if '5014' in str(self.awg.__class__):
            seq_chan = self.seq.get().channels
            for i in range(1, 5):
                chan_state = getattr(self.awg, f'ch{i}_state')
                if i in seq_chan:
                    chan_state(1)
                else:
                    chan_state(0)
            
            if self.awg.get_state()=='Idle':
                self.run_button.button_type = 'success'
                self.awg.run()
                print("AWGs Running")
            elif self.awg.get_state()=='Running':
                self.run_button.button_type = 'danger'
                self.awg.stop()
                print("AWGs Stopped")
        else:
            seq_chan = self.seq.get().channels
            for i, chan in enumerate(self.awg.channels):
                if i+1 in seq_chan:
                    chan.state(1)
                else:
                    chan.state(0)
            
            if self.awg.run_state() == 'Running':
                self.awg.stop()
                print(self.awg.run_state())
            elif self.awg.run_state() == 'Waiting for trigger':
                print(self.awg.run_state())
            else:
                self.awg.play()
                print(self.awg.run_state())
