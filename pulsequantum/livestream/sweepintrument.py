import numpy as np
import broadbean as bb
from qcodes import validators as vals
from sequencebuilder.back_of_beans import BagOfBeans


ramp = bb.PulseAtoms.ramp  # args: start, stop
sine = bb.PulseAtoms.sine  # args: freq, ampl, off, phase



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
        marker_duration: float
            duration of marker
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
                      vals=vals.Numbers(0,1))
        self.add_parameter('slow_steps',
                      label='Number of slow steps',
                      unit='Nr',
                      set_cmd= lambda x : x,
                      vals=vals.Ints(0,100))
        self.add_parameter('marker_duration',
                      label='Marker duration',
                      unit='s',
                      set_cmd= lambda x : x,
                      vals=vals.Numbers(0,1))
        self.add_parameter('marker_offset',
                      label='Marker Offset',
                      unit='s',
                      set_cmd= lambda x : x,
                      vals=vals.Numbers(-1e-1,1e-1))
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
        self.add_parameter('delay_time',
                      label='Delay time',
                      unit='s',
                      set_cmd= lambda x : x,
                      vals=vals.Numbers(0,1))
        self.add_parameter('awg_sr',
                      label='AWG sample rate',
                      unit='s',
                      set_cmd= lambda x : x,
                      vals=vals.Numbers(1e7,1.2e9))

    def sweep_pulse(self):
        self.seq.empty_sequence()
        marker_duration = self.marker_duration.get()
        total_time = self.fast_time.get() + self.delay_time.get()
        delay_time = self.delay_time.get()
        fast_time = self.fast_time.get()
        awg_sr = self.awg_sr.get()
        delta_fast = self.fast_range.get()/2.0
        delta_slow = self.slow_range.get()/2.0
        steps = np.linspace(-delta_slow, delta_slow, self.slow_steps.get())
        seg_ramp = bb.BluePrint()
        seg_step = bb.BluePrint()
        if delay_time*awg_sr >= 1.5:
            for i, v in enumerate(steps):
                seg_ramp.insertSegment(2*i, ramp, (-delta_fast, -delta_fast), dur=delay_time)
                seg_ramp.insertSegment(2*i+1, ramp, (-delta_fast, delta_fast), dur=fast_time)
                seg_step.insertSegment(i, ramp, (v, v), dur=total_time)
                
                if i == 0:
                    seg_step.setSegmentMarker('ramp', (0, marker_duration), 1)
                    seg_ramp.setSegmentMarker('ramp', (0, marker_duration), 1)
                else:
                    seg_ramp.setSegmentMarker(f'ramp{2*i+1}', (0, marker_duration), 1)
        else:
            for i, v in enumerate(steps):
                seg_ramp.insertSegment(i, ramp, (-delta_fast, delta_fast), dur=fast_time)
                seg_step.insertSegment(i, ramp, (v, v), dur=fast_time)
                if i == 0:
                    seg_step.setSegmentMarker('ramp', (0, marker_duration), 1)
                    seg_ramp.setSegmentMarker('ramp', (0, marker_duration), 1)
                else:
                    seg_ramp.setSegmentMarker(f'ramp{i+1}', (0, marker_duration), 1)
            

        seg_ramp.setSR(awg_sr)
        seg_step.setSR(awg_sr)
        elem = bb.Element()
        elem.addBluePrint(self.fast_channel.get(), seg_ramp)
        elem.addBluePrint(self.slow_channel.get(), seg_step)
        self.seq.seq.addElement(1,elem)
        self.seq.seq.setSR(awg_sr)
        self.seq.seq.setSequencingNumberOfRepetitions(1, 0)
        self.seq.set_all_channel_amplitude_offset(amplitude=1, offset=0)

    def sweep_sine(self):
        self.seq.empty_sequence()
        total_time = self.fast_time.get() + self.delay_time.get()
        delay_time = self.delay_time.get()
        fast_time = self.fast_time.get()
        awg_sr = self.awg_sr.get()
        amplitude = self.fast_range.get()
        freq = 1.0/fast_time
        range_slow = self.slow_range.get()
        v_slow = -range_slow/2
        nr_steps = self.slow_steps.get()
        nr_steps_fast = nr_steps
        delta_slow = range_slow/(nr_steps+1)
        seg_sines = bb.BluePrint()
        seg_one_sine = bb.BluePrint()
        seg_step = bb.BluePrint()
        if delay_time*awg_sr >= 1.5:
            seg_one_sine.insertSegment(1, sine, (freq, amplitude/2.0, 0, -np.pi/2), dur=fast_time)
            seg_one_sine.insertSegment(0, ramp, (-amplitude/2, -amplitude/2), dur=delay_time)

            marker_times = np.arccos(np.linspace(-1, 1, nr_steps_fast))*fast_time/(2*np.pi)
            marker_times.sort()
            marker_duration_max = np.diff(marker_times).min()/2
            if self.marker_duration.get() > marker_duration_max:
                self.marker_duration.set(marker_duration_max)
            marker_duration = self.marker_duration.get()


            for i in range(nr_steps):
                seg_step.insertSegment(i, ramp, (v_slow, v_slow), dur=total_time)
                v_slow += delta_slow
                if i == 0:
                    seg_sines = seg_one_sine
                    seg_step.setSegmentMarker('ramp',(0,total_time),1)
                    for time in marker_times:
                        seg_sines.marker1.append((delay_time+time, marker_duration))

                else:
                    seg_sines = seg_sines + seg_one_sine
                    for time in marker_times:
                        seg_sines.marker1.append((delay_time+time+total_time*i,marker_duration))
        else:
            seg_one_sine.insertSegment(0, sine, (freq, amplitude/2.0, 0, -np.pi/2), dur=fast_time)

            marker_times = np.arccos(np.linspace(-1, 1, nr_steps_fast))*fast_time/(2*np.pi)
            marker_times.sort()
            marker_duration_max = np.diff(marker_times).min()/2
            if self.marker_duration.get() > marker_duration_max:
                self.marker_duration.set(marker_duration_max)
            marker_duration = self.marker_duration.get()


            for i in range(nr_steps):
                seg_step.insertSegment(i, ramp, (v_slow, v_slow), dur=fast_time)
                v_slow += delta_slow
                if i == 0:
                    seg_sines = seg_one_sine
                    seg_step.setSegmentMarker('ramp',(0,fast_time),1)
                    for time in marker_times:
                        seg_sines.marker1.append((time, marker_duration))

                else:
                    seg_sines = seg_sines + seg_one_sine
                    for time in marker_times:
                        seg_sines.marker1.append((time+fast_time*i,marker_duration))

        seg_sines.setSR(awg_sr)
        seg_step.setSR(awg_sr)
        elem = bb.Element()
        elem.addBluePrint(self.fast_channel.get(), seg_sines)
        elem.addBluePrint(self.slow_channel.get(), seg_step)
        self.seq.seq.addElement(1,elem)
        self.seq.seq.setSR(awg_sr)
        self.seq.seq.setSequencingNumberOfRepetitions(1, 0)
        self.seq.set_all_channel_amplitude_offset(amplitude=1, offset=0)


    def sweep_sineupdown(self):
        marker_duration = self.marker_duration.get()
        self.seq.empty_sequence()
        fast_time = self.fast_time.get()
        amplitude = self.fast_range.get()
        freq = 1.0/fast_time
        range_slow = self.slow_range.get()/2.0
        v_slow = -range_slow/2
        nr_steps = self.slow_steps.get()
        nr_steps_fast = nr_steps
        delta_slow = 2*range_slow/(nr_steps+1)
        marker_duration = 2e-5
        
        seg_sines = bb.BluePrint()
        seg_one_sine = bb.BluePrint()
        seg_step = bb.BluePrint()
        seg_one_sine.insertSegment(0, sine, (freq, amplitude, 0, -np.pi/2), dur=fast_time)

        marker_times_up = np.arccos(np.linspace(-1, 1, nr_steps_fast+1))*fast_time/(2*np.pi)
        marker_times_down = marker_times_up + fast_time/2
        marker_times = np.append(marker_times_up[1:], marker_times_down[1:])

        for i in range(nr_steps):
            seg_step.insertSegment(i*2, ramp, (v_slow, v_slow), dur=fast_time/2)
            v_slow += delta_slow
            seg_step.insertSegment(i*2+1, ramp, (v_slow, v_slow), dur=fast_time/2)
            v_slow += delta_slow
            if i == 0:
                seg_sines = seg_one_sine
                seg_step.setSegmentMarker('ramp',(0,fast_time/2),1)
                for time in marker_times:
                    seg_sines.marker1.append((time,marker_duration))

            else:
                seg_sines = seg_sines + seg_one_sine
            for time in marker_times:
                seg_sines.marker1.append((time+fast_time*i,marker_duration))

        seg_sines.setSR(24*10/fast_time)
        seg_step.setSR(24*10/fast_time)
        elem = bb.Element()
        elem.addBluePrint(self.fast_channel.get(), seg_sines)
        elem.addBluePrint(self.slow_channel.get(), seg_step)
        self.seq.seq.addElement(1,elem)
        self.seq.seq.setSR(24*10/fast_time)
        self.seq.seq.setSequencingNumberOfRepetitions(1, 0)
        self.seq.set_all_channel_amplitude_offset(amplitude=1, offset=0)

    def sweep_sineone(self):
        self.seq.empty_sequence()
        marker_duration = self.marker_duration.get()
        fast_time = 2*self.fast_time.get()
        amplitude = self.fast_range.get()
        freq = 1.0/fast_time
        range_slow = self.slow_range.get()
        v_slow = -range_slow/2
        nr_steps = self.slow_steps.get()
        nr_steps_fast = nr_steps
        delta_slow = range_slow/(nr_steps+1)
        
        seg_sines = bb.BluePrint()
        seg_one_sine = bb.BluePrint()
        seg_step = bb.BluePrint()
        seg_one_sine.insertSegment(0, sine, (freq, amplitude/2.0, 0, -np.pi/2), dur=fast_time)

        marker_times = np.arccos(np.linspace(-1, 1, nr_steps_fast+1))*fast_time/(2*np.pi)

        for i in range(nr_steps):
            seg_step.insertSegment(i, ramp, (v_slow, v_slow), dur=fast_time)
            v_slow += delta_slow
            seg_sines.insertSegment(i, sine,  (freq, amplitude/2.0, 0, -np.pi/2), dur=fast_time)

            if i == 0:
                seg_sines.setSegmentMarker('sine',(0,marker_duration),1)
                seg_step.setSegmentMarker('ramp',(0,marker_duration),1)
            else:
                 seg_sines.setSegmentMarker(f'sine{i+1}',(0,marker_duration),1)

        seg_sines.setSR(24*10/fast_time)
        seg_step.setSR(24*10/fast_time)
        elem = bb.Element()
        elem.addBluePrint(self.fast_channel.get(), seg_sines)
        elem.addBluePrint(self.slow_channel.get(), seg_step)
        self.seq.seq.addElement(1,elem)
        self.seq.seq.setSR(24*10/fast_time)
        self.seq.seq.setSequencingNumberOfRepetitions(1, 0)
        self.seq.set_all_channel_amplitude_offset(amplitude=1, offset=0)
