import QDevil_QDAC2 as QDAC2
qdac_addr = '192.168.8.15'
qdac = QDAC2.QDac2('QDAC-II', visalib='@py', address=f'TCPIP::{qdac_addr}::5025::SOCKET')

qdac.reset()




class Qdac2Controler:

    def __init__(self, qdac, mode,
                 v_fast_start, v_fast_end, npoints_fast,
                 v_slow_start, v_slow_end, npoints_slow,
                 chan_fast,
                 chan_slow,
                 **kwargs):
         
        self.qdac = qdac
        self.mode = mode
        self.chan_fast = chan_fast
        self.chan_slow = chan_slow
        self.v_fast_start = v_fast_start
        self.v_fast_end = v_fast_end
        self.npoints_fast = npoints_fast
        self.v_slow_start = v_slow_start
        self.v_slow_end = v_slow_end
        self.npoints_slow = npoints_slow
        self.v_fast = []
        self.v_slow = []



    def run(self) -> None:
            
        if mode == 'sin':
            self.sin()
        elif mode == 'staircase':
             self.staircase()
        
        self.qdac.run()

    def sin(self):
        pass

    def staircase(self):
        arrangement =self.qdac.arrange(
        # QDAC channels 2 & 3 connected to sample
        gates={'plunger2': self.chan_fast, 'plunger3': self.chan_slow},
        # DMM external trigger connected to QDAC Output Trigger 4
        output_triggers={'dmm': 4})


        sweep = arrangement.virtual_sweep2d(
                                            inner_gate='plunger2',
                                            inner_voltages=np.linspace(-0.2, 0.6, 5),
                                            outer_gate='plunger3',
                                            outer_voltages=np.linspace(-0.7, 0.15, 4),
                                            inner_step_time_s=10e-6,
                                            inner_step_trigger='dmm')

    def joost(self):
        channel_fast = self.qdac.channels[chan_fast]
        dwell_time_sweep_s = 150e-6
        
        channel_slow =  self.qdac.channels[chan_slow]        
        slew_rate_sweep = min(1000,abs(self.v_fast_end-self.v_fast_start)/dwell_time_sweep_s)
        slew_rate_step = slew_rate_sweep

        channel_fast.dc_slew_rate_V_per_s(slew_rate_sweep)
        channel_slow.dc_slew_rate_V_per_s(slew_rate_step)
        
        channel_fast.dc_constant_V(self.v_fast_start)
        channel_slow.dc_constant_V(self.v_slow_start)
        
        channel_fast.dc_sweep(self.v_fast_start,
                              self.v_fast_end,
                              self.npoints_fast,
                              repetitions=self.npoints_slow,
                              dwell_s=dwell_time_sweep_s)

        channel_slow.dc_sweep(self.v_slow_start,
                              self.v_slow_end,
                              self.npoints_slow,
                              repetitions=-1,
                              dwell_s=self.npoints_fast*dwell_time_sweep_s)
        
        channel_fast.output_filter('high')
        channel_slow.output_filter('med')
        
        self.qdac.write(f'sour{self.chan_fast}:dc:trig:sour int1')
        self.qdac.write(f'sour{self.chan_slow}:dc:trig:sour int1')
        
        trigger_width = dwell_time_sweep_s/10
        
        self.qdac.write(f'sour{self.chan_fast}:dc:mark:sst 2')
        self.qdac.write('outp:trig2:sour int2')
        self.qdac.write('outp:trig2:widt '+ str(trigger_width))
        
        self.qdac.write(f'sour{self.chan_fast}:dc:init')
        self.qdac.write(f'sour{self.chan_fast}:dc:init')
        return '2D scan set up'
        


alazar = SC.load_instrument('alazar')
alazarconfig(alazar, seqmode=True,external_clock=False)
alazar_ctrl = SC.load_instrument('alazar_ctrl')
channelA2 = SC.load_instrument('channelA2',parent=alazar_ctrl)


class AlazarVideo:
    def __init__(self,channel) -> None:
        pass



class GeneratedSetPoints(Parameter):
    """
    A parameter that generates a setpoint array from start, stop and num points
    parameters.
    """
    def __init__(self, startparam, stopparam, numpointsparam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._startparam = startparam
        self._stopparam = stopparam
        self._numpointsparam = numpointsparam

    def get_raw(self):
        return np.linspace(self._startparam(), self._stopparam(),
                              self._numpointsparam())
        

class AlazarVideo(ParameterWithSetpoints):
    
    def __init__(self, channel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = channel

    def get_raw(self):

        return self.channel.data.get()

class VideoInstrument(Instrument):

    def __init__(self, name, channel,  **kwargs):
        
        super().__init__(name, **kwargs)
        self.channel = channel

        self.add_parameter('V_fast_start',
                           initial_value=0,
                           unit='V',
                           label='V_fast start',
                           vals=Numbers(0,1e3),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('V_fast_end',
                           initial_value=0,
                           unit='V',
                           label='V_fast end',
                           vals=Numbers(0,1e3),
                           get_cmd=None,
                           set_cmd=None)
        
        self.add_parameter('V_slow_start',
                           initial_value=0,
                           unit='V',
                           label='V_slow start',
                           vals=Numbers(0,1e3),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('V_slow_end',
                           initial_value=0,
                           unit='V',
                           label='V_slow end',
                           vals=Numbers(0,1e3),
                           get_cmd=None,
                           set_cmd=None)
 
        self.add_parameter('n_pointsx',
                           unit='',
                           initial_value=100,
                           vals=Numbers(1,1e4),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('n_pointsy',
                           unit='',
                           initial_value=100,
                           vals=Numbers(1,1e4),
                           get_cmd=None,
                           set_cmd=None)
            
        self.add_parameter('V_fast',
                           unit='V',
                           label='V x',
                           parameter_class=GeneratedSetPoints,
                           startparam=self.V_fast_start,
                           stopparam=self.V_fast_stop,
                           numpointsparam=self.n_pointsx,
                           vals=Arrays(shape=(self.n_pointsx.get_latest,)))
        
        self.add_parameter('V_slow',
                           unit='V',
                           label='V y',
                           parameter_class=GeneratedSetPoints,
                           startparam=self.V_slow_start,
                           stopparam=self.V_fast_stop,
                           numpointsparam=self.n_pointsy,
                           vals=Arrays(shape=(self.n_pointsy.get_latest,)))


def sync_alazar():
    alazar_ctrl.int_delay(0e-6)
    alazar_ctrl.int_time(fast_time)
    alazar_ctrl.channels.append(channelA2)
    setpoint = SC.seqbuild.x_val()
    channelA2.num_averages(40)
    channelA2.records_per_buffer(slow_point_nr)
    channelA2.data.setpoint_labels = ('V_gate',)
    channelA2.data.setpoint_units = ('V',)
    channelA2.prepare_channel()
    channelA2.data.setpoints = (tuple(setpoint),)

