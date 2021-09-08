
from qcodes import Parameter
import numpy as np
from qcodes.utils.validators import Numbers, Arrays
from qcodes.instrument.base import Instrument
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter

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

        self.add_parameter('V_x_start',
                           initial_value=0,
                           unit='V',
                           label='V_x start',
                           vals=Numbers(-1,1),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('V_x_stop',
                           initial_value=0.1,
                           unit='V',
                           label='V_x stop',
                           vals=Numbers(-1,1),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('V_y_start',
                           initial_value=0,
                           unit='V',
                           label='V_y start',
                           vals=Numbers(-1,1),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('V_y_stop',
                           initial_value=0.1,
                           unit='V',
                           label='V_y stop',
                           vals=Numbers(-1,1),
                           get_cmd=None,
                           set_cmd=None)
        
        self.add_parameter('phase_x',
                           initial_value=0,
                           unit='Hz',
                           label='Phase X',
                           vals=Numbers(0,1e3),
                           get_cmd=None,
                           set_cmd=None)
        
        self.add_parameter('phase_y',
                           initial_value=0,
                           unit='Hz',
                           label='Phase Y',
                           vals=Numbers(0,1e3),
                           get_cmd=None,
                           set_cmd=None) 

        self.add_parameter('n_pointsx',
                           unit='',
                           initial_value=100,
                           vals=Numbers(1,2e4),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('n_pointsy',
                           unit='',
                           initial_value=100,
                           vals=Numbers(1,2e4),
                           get_cmd=None,
                           set_cmd=None)
            
        self.add_parameter('V_axis_x',
                           unit='V',
                           label='V Axis X',
                           parameter_class=GeneratedSetPoints,
                           startparam=self.V_x_start,
                           stopparam=self.V_y_stop,
                           numpointsparam=self.n_pointsx,
                           vals=Arrays(shape=(self.n_pointsx.get_latest,)))
        
        self.add_parameter('V_axis_y',
                           unit='V',
                           label='V Axis Y',
                           parameter_class=GeneratedSetPoints,
                           startparam=self.V_y_start,
                           stopparam=self.V_y_stop,
                           numpointsparam=self.n_pointsy,
                           vals=Arrays(shape=(self.n_pointsy.get_latest,)))
        
        self.add_parameter('Alazarvideo',
                   unit='V',
                   setpoints=(self.V_axis_x,self.V_axis_y),
                   label='Alazar',
                   parameter_class=AlazarVideo,
                   channel = self.channel,
                   vals=Arrays(shape=(self.n_pointsx.get_latest,self.n_pointsy.get_latest)))