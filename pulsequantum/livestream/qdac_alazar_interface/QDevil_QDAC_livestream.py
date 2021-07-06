from qcodes.instrument_drivers.QDevil.QDevil_QDAC import QDac,Waveform
import time

class QDac_livestream(QDac):
    """
    Extension of the channelised driver for the QDevil QDAC voltage source.

    Exposes channels, temperature sensors and calibration output,
    and 'ramp_voltages' + 'ramp_voltages_2d' for multi channel ramping.

    In addition a 'mode_force' flag (default False) is exposed.
    'mode_force' (=True) is used to enable voltage range switching, via
    the channel 'mode' parameter, even at non-zero output voltages.

    Tested with Firmware Version: 1.07

    The driver assumes that the instrument is ALWAYS in verbose mode OFF
    and sets this as part of the initialization, so please do not change this.
    """

    # set nonzero value (seconds) to accept older status when reading settings
    max_status_age = 1

    def __init__(self,
                 name,
                 address,
                 update_currents=False,
                 **kwargs):
        """
        Instantiates the instrument.

        Args:
            name (str): The instrument name used by qcodes
            address (str): The VISA name of the resource
            update_currents (bool): Whether to query all channels for their
                current sensor value on startup, which takes about 0.5 sec
                per channel. Default: False.

        Returns:
            QDac object
        """

        super().__init__(name, address, update_currents, **kwargs)

  
    def ramp_voltages_2d_avg(self, slow_chans, slow_vstart, slow_vend,
                         fast_chans, fast_vstart, fast_vend,
                         step_length, slow_steps, fast_steps, n_avg):
        """
        Function for smoothly ramping two channel groups simultaneously with
        one slow (x) and one fast (y) group. used by 'ramp_voltages' where x is
        empty. Function generators and triggers are assigned automatically.

        Args:
            slow_chans:   List (int) of channels to be ramped (1 indexed) in
                          the slow-group\n
            slow_vstart:  List (int) of voltages to ramp from in the
                          slow-group.
                          MAY BE EMPTY. But if provided, time is saved by NOT
                          reading the present values from the instrument.\n
            slow_vend:    list (int) of voltages to ramp to in the slow-group.

            fast_chans:   List (int) of channels to be ramped (1 indexed) in
                          the fast-group.\n
            fast_vstart:  List (int) of voltages to ramp from in the
                          fast-group.
                          MAY BE EMPTY. But if provided, time is saved by NOT
                          reading the present values from the instrument.\n
            fast_vend:    list (int) of voltages to ramp to in the fast-group.

            step_length:  (float) Time spent at each step in seconds
                          (min. 0.001) multiple of 1 ms.\n
            slow_steps:   (int) number of steps in the slow direction.\n
            fast_steps:   (int) number of steps in the fast direction.\n
            n_avg:        (int) number of repetitions.\n

        Returns:
            Estimated time of the excecution of the 2D scan.\n
        NOTE: This function returns as the ramps are started.
        """
        channellist = [*slow_chans, *fast_chans]
        v_endlist = [*slow_vend, *fast_vend]
        v_startlist = [*slow_vstart, *fast_vstart]
        step_length_ms = int(step_length*1000)

        if step_length < 0.001:
            LOG.warning('step_length too short: {:.3f} s. \nstep_length set to'
                        .format(step_length_ms) + ' minimum (1ms).')
            step_length_ms = 1

        if any([ch in fast_chans for ch in slow_chans]):
            raise ValueError(
                    'Channel cannot be in both slow_chans and fast_chans!')

        no_channels = len(channellist)
        if no_channels != len(v_endlist):
            raise ValueError(
                    'Number of channels and number of voltages inconsistent!')

        for chan in channellist:
            if chan not in range(1, self.num_chans+1):
                raise ValueError(
                        f'Channel number must be 1-{self.num_chans}.')
            if not (chan in self._assigned_fgs):
                self._get_functiongenerator(chan)

        # Voltage validation
        for i in range(no_channels):
            self.channels[channellist[i]-1].v.validate(v_endlist[i])
        if v_startlist:
            for i in range(no_channels):
                self.channels[channellist[i]-1].v.validate(v_startlist[i])

        # Get start voltages if not provided
        if not slow_vstart:
            slow_vstart = [self.channels[ch-1].v.get() for ch in slow_chans]
        if not fast_vstart:
            fast_vstart = [self.channels[ch-1].v.get() for ch in fast_chans]

        v_startlist = [*slow_vstart, *fast_vstart]
        if no_channels != len(v_startlist):
            raise ValueError(
                'Number of start voltages do not match number of channels!')

        # Find trigger not aleady uses (avoid starting other
        # channels/function generators)
        if no_channels == 1:
            trigger = 0
        else:
            trigger = int(min(self._trigs.difference(
                                    set(self._assigned_triggers.values()))))

        # Make sure any sync outputs are configured
        for chan in channellist:
            if chan in self._syncoutputs:
                sync = self._syncoutputs[chan]
                sync_duration = int(
                                1000*self.channels[chan-1].sync_duration.get())
                sync_delay = int(1000*self.channels[chan-1].sync_delay.get())
                self.write('syn {} {} {} {}'.format(
                                            sync, self._assigned_fgs[chan].fg,
                                            sync_delay, sync_duration))

        # Now program the channel amplitudes and function generators
        msg = ''
        for i in range(no_channels):
            amplitude = v_endlist[i]-v_startlist[i]
            ch = channellist[i]
            fg = self._assigned_fgs[ch].fg
            if trigger > 0:  # Trigger 0 is not a trigger
                self._assigned_triggers[fg] = trigger
            msg += 'wav {} {} {} {}'.format(ch, fg, amplitude, v_startlist[i])
            # using staircase = function 4
            nsteps = slow_steps if ch in slow_chans else fast_steps
            repetitions = n_avg*slow_steps if ch in fast_chans else n_avg

            delay = step_length_ms \
                if ch in fast_chans else fast_steps*step_length_ms
            msg += ';fun {} {} {} {} {} {};'.format(
                        fg, Waveform.staircase, delay, int(nsteps),
                        repetitions, trigger)
            # Update latest values to ramp end values
            # (actually not necessary when called from _set_voltage)
            self.channels[ch-1].v.cache.set(v_endlist[i])
        self.write(msg[:-1])  # last semicolon is stripped

        # Fire trigger to start generators simultaneously, saving communication
        # time by not using triggers for single channel ramping
        if trigger > 0:
            self.write(f'trig {trigger}')

        # Update fgs dict so that we know when the ramp is supposed to end
        time_ramp = slow_steps * fast_steps * step_length_ms / 1000
        time_end = time_ramp + time.time()
        for chan in channellist:
            self._assigned_fgs[chan].t_end = time_end
        return time_ramp