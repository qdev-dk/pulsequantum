import numpy as np
import broadbean as bb
from qcodes import validators as vals
from sequencebuilder.back_of_beans import BagOfBeans



ramp = bb.PulseAtoms.ramp 



class SequenceBuilder(BagOfBeans):
    """
    Class for generating Sequences with predefined patterns

        Attributes
        ----------
        fast_channel : int
            channel used for the fast sweep
        slow_channel : int
            channel used for the slow sweep 
        fast_range : float
            range for the fast sweep
        slow_range : float
            range for the slow sweep
        fast_time : float
            time for the slow sweep
        slow_steps: int
            time for the slow sweep
        marker_offset : float
            releative offset with respect to the readout_time
        SR: float
            sampling rate 

        Methods
        -------
        MultiQ_SSB_Spec_NoOverlap
            sequence of two channels with orthogonal sine/cosine pulses and two channels for the readout
        MultiQ_Lifetime_overlap
            One channels containing a pi-pulse
            varying the time between the end of the pi-pulse and the readout and two channels for the readout
    """

    def __init__(self,name:str,number_read_freqs:int = 1,**kwargs):
        super().__init__(name, **kwargs)

        self.add_parameter('fast_channel',
                      label='Fast Channel',
                      unit='Nr',
                      set_cmd= lambda x : x,
                      vals=vals.Ints(0,50))
        self.add_parameter('slow_channel',
                      label='Slow Channel',
                      unit='Nr',
                      set_cmd= lambda x : x,
                      vals=vals.Ints(0,50))
        self.add_parameter('fast_range',
                      label='Fast Range',
                      unit='V',
                      set_cmd= lambda x : x,
                      vals=vals.Numbers(0,0.5))
        self.add_parameter('slow_range',
                      label='Slow Range',
                      unit='V',
                      set_cmd= lambda x : x,
                      vals=vals.Numbers(0,0.5))                      
        self.add_parameter('fast_time',
                      label='Fast Time',
                      unit='s',
                      set_cmd= lambda x : x,
                      vals=vals.Numbers(0,1.e-2))
        self.add_parameter('slow_steps',
                      label='Number of slow steps',
                      unit='Nr',
                      set_cmd= lambda x : x,
                      vals=vals.Ints(0,100))
        self.add_parameter('marker_offset',
                      label='Marker Offset',
                      unit='s',
                      set_cmd= lambda x : x,
                      vals=vals.Numbers(-1e-5,1e-5))
        for i in range(number_read_freqs):
            self.add_parameter('readout_freq_{}'.format(i+1),
                        label='Readout Frequency {}'.format(i+1),
                        unit='Hz',
                        set_cmd= lambda x : x,
                        vals=vals.Numbers(0,12.5e9))
        self.add_parameter('x_val',
                            label='',
                            unit='',
                            get_cmd=None,
                            set_cmd=None
                            )


    def sweep_pulse(self):
        self.seq.empty_sequence()
        fast_time = self.fast_time.get()
        delta_fast = self.fast_range.get()/2.0
        delta_slow = self.slow_range.get()/2.0
        steps = np.linspace(-delta_slow, delta_slow , self.slow_steps.get())
        seg_ramp = bb.BluePrint()
        seg_step = bb.BluePrint()
        for i, v in enumerate(steps):
            seg_ramp.insertSegment(i, ramp, (-delta_fast, delta_fast), dur=fast_time)
            seg_step.insertSegment(i, ramp, (v, v), dur=fast_time)
            if i == 0:
                seg_step.setSegmentMarker('ramp',(0,fast_time/2),1)
                seg_ramp.setSegmentMarker('ramp',(0,fast_time/2),1)
            else:             
                seg_ramp.setSegmentMarker(f'ramp{i+1}',(0,fast_time/2),1)

        seg_ramp.setSR(24*10/fast_time)
        seg_step.setSR(24*10/fast_time)
        elem = bb.Element()
        elem.addBluePrint(self.fast_channel.get(), seg_ramp)
        elem.addBluePrint(self.slow_channel.get(), seg_step)
        self.seq.seq.addElement(1,elem)
        self.seq.seq.setSR(24*10/fast_time)
        self.seq.seq.setSequencingNumberOfRepetitions(1, 0)
     