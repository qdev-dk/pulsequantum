
from qcodes import Parameter
import numpy as np
from qcodes.utils.validators import Numbers, Arrays
from qcodes.instrument.base import Instrument
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter
from typing import Any, Iterable, Tuple, Union

class GeneratedSetPoints(Parameter):
    """
    A parameter that generates a setpoint array from start, stop and num points
    parameters.
    """
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()

    def set_raw(self, value: Iterable[Union[float, int]]) -> None:
        self.sweep_array = value

    def get_raw(self):
        return self.sweep_array

    def reset(self):
        V_dc = self.instrument.V_dc.get()
        V_start = self.instrument.V_start.get() + V_dc
        V_stop = self.instrument.V_stop.get() + V_dc
        nr = self.instrument.n_points.get()
        self.sweep_array = np.linspace(V_start, V_stop, nr)

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
        
        # Add the channel to the instrument
        for i, dim in enumerate(['x', 'y']):
            channel = VideoAxes(self, dim, dim, n_points[i])
            self.add_submodule(dim, channel)
     
        self.add_parameter('video',
                           unit='V',
                           setpoints=(self.x.V_axis,self.y.V_axis),
                           label='Video',
                           parameter_class=Video,
                           data_func = self.data_func,
                           vals=Arrays(shape=(self.x.n_points.get_latest,self.y.n_points.get_latest)))

        self.add_parameter('nr_average',
                           initial_value=1,
                           unit='Nr',
                           label='nr_average',
                           vals=Numbers(1,10e1000),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('videoaverage',
                           unit='V',
                           setpoints=(self.x.V_axis,self.y.V_axis),
                           label='VideoAverage',
                           parameter_class=VideoAverage,
                           vals=Arrays(shape=(self.x.n_points.get_latest,self.y.n_points.get_latest)))

            
class VideoAxes(InstrumentChannel):
    def __init__(self, parent: Instrument, name: str, channel: str, n_points,  **kwargs):
        super().__init__(parent, name, **kwargs)
        self.dim = channel
        self.add_parameter('V_dc',
                           initial_value=0,
                           unit='V',
                           label='V_'+self.dim+' dc',
                           vals=Numbers(-1,1),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('V_start',
                           initial_value=0,
                           unit='V',
                           label='V_'+self.dim+' start',
                           vals=Numbers(-1,1),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('V_stop',
                           initial_value=0.1,
                           unit='V',
                           label='V_'+self.dim+' stop',
                           vals=Numbers(-1,1),
                           get_cmd=None,
                           set_cmd=None)
        
        self.add_parameter('n_points',
                           unit='',
                           initial_value=n_points,
                           vals=Numbers(1,2e4),
                           get_cmd=None,
                           set_cmd=None)
            
        self.add_parameter('V_axis',
                           unit='V',
                           label='V Axis '+self.dim,
                           parameter_class=GeneratedSetPoints,
                           vals=Arrays(shape=(self.n_points.get_latest,)))
        