import param


class AlazarSettings(param.Parameterized):
    clock_source = param.ObjectSelector(objects=['INTERNAL_CLOCK', 'FAST_EXTERNAL_CLOCK', 'EXTERNAL_CLOCK_10MHz_REF'])
    sample_rate =
    coupling1 = param.ObjectSelector(objects=['DC', 'AC'])
    coupling2 = param.ObjectSelector(objects=['DC', 'AC'])

    trigger_operation = param.ObjectSelector(objects=['TRIG_ENGINE_OP_J',
                                                      'TRIG_ENGINE_OP_K',
                                                      'TRIG_ENGINE_OP_J_OR_K',
                                                      'TRIG_ENGINE_OP_J_AND_K',
                                                      'TRIG_ENGINE_OP_J_XOR_K',
                                                      'TRIG_ENGINE_OP_J_AND_NOT_K',
                                                      'TRIG_ENGINE_OP_NOT_J_AND_K'])

    trigger_engine1 = param.ObjectSelector(objects=['TRIG_ENGINE_J',
                                                    'TRIG_ENGINE_K'])

    trigger_source1 = param.ObjectSelector(objects=['CHANNEL_A',
                                                    'CHANNEL_B',
                                                    'EXTERNAL',
                                                    'DISABLE'])

    trigger_slope1 = param.ObjectSelector(objects=['TRIG_SLOPE_POSITIVE',
                                                   'TRIG_SLOPE_NEGATIVE'])

    trigger_level1 = param.Integer(140, bounds=(0, 255))
    trigger_engine2= param.ObjectSelector(objects=['TRIG_ENGINE_J',
                                                   'TRIG_ENGINE_K'])

    trigger_source2 = param.ObjectSelector(objects=['CHANNEL_A',
                                                    'CHANNEL_B',
                                                    'EXTERNAL',
                                                    'DISABLE'])

    trigger_slope2 = param.ObjectSelector(objects=['CHANNEL_A',
                                                   'CHANNEL_B',
                                                   'EXTERNAL',
                                                   'DISABLE'])

    trigger_level2 = param.Integer(140, bounds=(0,255))
    external_trigger_coupling = param.ObjectSelector(objects=['AC', 'DC'])
    external_trigger_range = param.ObjectSelector(objects=['ETR_TTL', 'ETR_2V5'])
    trigger_delay = param.Integer(0, bounds=(0,255))
    timeout_ticks = param.Integer(0, bounds=(0, 255))
    seqmode = param.Boolean(True, doc="A sample Boolean parameter")
    apply  = param.Action(lambda x: x, doc="""Record timestamp.""", precedence=0.7)



class AlazarConfig():

    def __init__(self, alazar):

        self.alazar = alazar
        self.settings = AlazarSettings()

    def config(self):
        """
        function for config of alazar
        """
        with self.alazar.syncing():
            self.alazar.clock_source(self.settings.clock_source)    
            self.alazar.external_sample_rate(self.settings.external_sample_rate)
            self.alazar.clock_edge(self.settings.clock_edge)
            self.alazar.decimation(self.settings.decimation)
            self.alazar.coupling1(self.settings.coupling1)
            self.alazar.coupling2(self.settings.coupling2)
            self.alazar.trigger_operation(self.settings.trigger_operation)
            self.alazar.trigger_engine1(self.settings.trigger_engine1)
            self.alazar.trigger_source1(self.settings.trigger_source1)
            self.alazar.trigger_level1(self.settings.trigger_level1)
            self.alazar.trigger_engine2(self.settings.trigger_engine2)
            self.alazar.trigger_source2(self.settings.trigger_source2)
            self.alazar.trigger_level2(self.settings.trigger_level2)
            self.alazar.external_trigger_coupling(self.settings.external_trigger_coupling)
            self.alazar.external_trigger_range(self.settings.external_trigger_range)
            self.alazar.trigger_delay(self.settings.trigger_delay)
            self.alazar.timeout_ticks(self.settings.timeout_ticks)
            if self.settings:
                self.alazar.aux_io_mode('AUX_IN_TRIGGER_ENABLE') 
                self.alazar.aux_io_param('TRIG_SLOPE_POSITIVE') 
            else:
                self.alazar.aux_io_mode('AUX_IN_TRIGGER_ENABLE') 
                self.alazar.aux_io_param('TRIG_SLOPE_POSITIVE') 

    def get_settings(self):
        self.settings.clock_source = self.alazar.clock_source()    
        self.settings.external_sample_rate = self.alazar.external_sample_rate()
        self.settings.clock_edge = self.alazar.clock_edge()
        self.settings.decimation = self.alazar.decimation()
        self.settings.coupling1 = self.alazar.coupling1()
        self.settings.coupling2 = self.alazar.coupling2()
        self.settings.trigger_operation = self.alazar.trigger_operation()
        self.settings.trigger_engine1 = self.alazar.trigger_engine1()
        self.settings.trigger_source1 = self.alazar.trigger_source1()
        self.settings.trigger_level1 = self.alazar.trigger_level1()
        self.settings.trigger_engine2 = self.alazar.trigger_engine2()
        self.settings.trigger_source2 = self.alazar.trigger_source2()
        self.settings.trigger_level2 = self.alazar.trigger_level2()
        self.settings.external_trigger_coupling = self.alazar.external_trigger_coupling()
        self.settings.external_trigger_range = self.alazar.external_trigger_range()
        self.settings.trigger_delay = self.alazar.trigger_delay()
        self.settings.timeout_ticks = self.alazar.timeout_ticks()

