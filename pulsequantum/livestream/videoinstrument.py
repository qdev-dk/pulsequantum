
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
        

class Video(ParameterWithSetpoints):
    
    def __init__(self, data_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_func = data_func

    def get_raw(self):

        return self.data_func()


class VideoAverage(ParameterWithSetpoints):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.nr_average = self.root_instrument.nr_average.get()
        self.data_func = self.root_instrument.video.get
        self.data = self.data_func()

    def get_raw(self):
        self.nr_average = self.root_instrument.nr_average.get()
        #self.nr_average += 1.0
        self.data = ((self.nr_average-1)*self.data + self.data_func())/self.nr_average
        self.nr_average += 1.0
        self.root_instrument.nr_average.set(self.nr_average)
        
        return self.data

    def reset_average(self):
        self.nr_average = 1
        self.root_instrument.nr_average.set(self.nr_average)


class VideoInstrument(Instrument):

    def __init__(self, name, data_func, n_points,  **kwargs):
        
        super().__init__(name, **kwargs)
        self.data_func = data_func

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
        
        self.add_parameter('n_pointsx',
                           unit='',
                           initial_value=n_points[0],
                           vals=Numbers(1,2e4),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('n_pointsy',
                           unit='',
                           initial_value=n_points[1],
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
        
        self.add_parameter('video',
                           unit='V',
                           setpoints=(self.V_axis_x,self.V_axis_y),
                           label='Video',
                           parameter_class=Video,
                           data_func = self.data_func,
                           vals=Arrays(shape=(self.n_pointsx.get_latest,self.n_pointsy.get_latest)))

        self.add_parameter('nr_average',
                           initial_value=1,
                           unit='Nr',
                           label='nr_average',
                           vals=Numbers(1,10e1000),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('videoaverage',
                           unit='V',
                           setpoints=(self.V_axis_x,self.V_axis_y),
                           label='VideoAverage',
                           parameter_class=VideoAverage,
                           vals=Arrays(shape=(self.n_pointsx.get_latest,self.n_pointsy.get_latest)))