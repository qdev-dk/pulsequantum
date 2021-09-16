import numpy as np
import random
from qcodes.utils.validators import Numbers, Arrays
from qcodes.instrument.base import Instrument
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter

#Setting up array which contains recent spectrums
output_filt = []

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
        start = self.root_instrument.f_start()
        end = self.root_instrument.f_stop()
        npoints = self.root_instrument.n_points.get_latest()

        return np.linspace(start, end, npoints)

#Class that 
class DummyArray(ParameterWithSetpoints):

    def get_raw(self):
        npoints = self.root_instrument.n_points.get_latest()
        ls_x = self.root_instrument.freq_axis_x.get()
        ls_y = self.root_instrument.freq_axis_y.get()
        phase_x = self.root_instrument.phase_x.get()
        phase_y = self.root_instrument.phase_y.get()
        xx, yy = np.meshgrid(ls_x, ls_y)
        output = (np.sin(xx+phase_x+random.random()))*np.cos(yy+phase_y)
        return output

#Class that creates noise        
class NoiseArray(ParameterWithSetpoints):

    def get_raw(self):
        npoints = self.root_instrument.n_points.get_latest()
        output = np.asarray([np.random.rand(npoints) for i in range(npoints)])
        return output


# Class that filters out the noise by averaging recent samples and removing the average noise value
class FilterArray(ParameterWithSetpoints):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_filt = []

    def get_raw(self):
        spectrum = self.root_instrument.spectrum()
        spectrum_noise = self.root_instrument.spectrum_noise()
        self.output_filt.append(spectrum + spectrum_noise)
        self.output_filt = self.output_filt[-121:]
        output = (np.sum(np.asarray(self.output_filt), axis=0)/121)-0.5

        return output


class SpectrumNoise(ParameterWithSetpoints):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nr_average = 1
        self.data = self.root_instrument.spectrum()

    def get_raw(self):
        spectrum = self.root_instrument.spectrum()
        spectrum_noise = self.root_instrument.spectrum_noise()
        return spectrum + spectrum_noise

    def get_data(self):
        self.data = ((self.nr_average-1)*self.data + self.get_raw())/self.nr_average
        self.nr_average += 1.0
        
        return self.data


#Class that intialises the instrument which contains the filtered spectrum (spectrum_filt).
class FilterInstrument(Instrument):

    def __init__(self, name, **kwargs):

        super().__init__(name, **kwargs)

        self.add_parameter('f_start',
                           initial_value=0,
                           unit='Hz',
                           label='f start',
                           vals=Numbers(0,1e3),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('f_stop',
                           initial_value=20,
                           unit='Hz',
                           label='f stop',
                           vals=Numbers(1,1e3),
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

        self.add_parameter('n_points',
                           unit='',
                           initial_value=121,
                           vals=Numbers(1,1e3),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('freq_axis_x',
                           unit='Hz',
                           label='Freq Axis X',
                           parameter_class=GeneratedSetPoints,
                           startparam=self.f_start,
                           stopparam=self.f_stop,
                           numpointsparam=self.n_points,
                           vals=Arrays(shape=(self.n_points.get_latest,)))
        
        self.add_parameter('freq_axis_y',
                           unit='Hz',
                           label='Freq Axis Y',
                           parameter_class=GeneratedSetPoints,
                           startparam=self.f_start,
                           stopparam=self.f_stop,
                           numpointsparam=self.n_points,
                           vals=Arrays(shape=(self.n_points.get_latest,)))
        
        self.add_parameter('spectrum',
                   unit='dBm',
                   setpoints=(self.freq_axis_x,self.freq_axis_y),
                   label='Spectrum',
                   parameter_class=DummyArray,
                   vals=Arrays(shape=(self.n_points.get_latest,self.n_points.get_latest)))
                   
        self.add_parameter('spectrum_noise',
                   unit='dBm',
                   setpoints=(self.freq_axis_x,self.freq_axis_y),
                   label='Spectrum',
                   parameter_class=NoiseArray,
                   vals=Arrays(shape=(self.n_points.get_latest,self.n_points.get_latest)))

        self.add_parameter('spectrum_filt',
                   unit='dBm',
                   setpoints=(self.freq_axis_x,self.freq_axis_y),
                   label='Spectrum',
                   parameter_class=FilterArray,
                   vals=Arrays(shape=(self.n_points.get_latest,self.n_points.get_latest)))
        
        self.add_parameter('spectrum_and_noise',
                   unit='dBm',
                   setpoints=(self.freq_axis_x,self.freq_axis_y),
                   label='Spectrum',
                   parameter_class=SpectrumNoise,
                   vals=Arrays(shape=(self.n_points.get_latest,self.n_points.get_latest)))
