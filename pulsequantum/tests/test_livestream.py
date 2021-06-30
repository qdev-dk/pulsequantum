import numpy as np
import time
import qcodes as qc
import random
import os
import tempfile
from qcodes.utils.validators import Numbers, Arrays
from qcodes.instrument.base import Instrument
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter
from pulsequantum.livestream.livestream import LiveStream
from qcodes import initialise_or_create_database_at, \
    load_or_create_experiment


db_path = os.path.join(tempfile.gettempdir(),
                       'data_access_example.db')
initialise_or_create_database_at(db_path)

experiment = load_or_create_experiment(
    experiment_name='alazar',
    sample_name='alazar-sample')

SC = qc.Station()


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


class DummyArray(ParameterWithSetpoints):

    def get_raw(self):
        ls_x = self.root_instrument.freq_axis_x.get()
        ls_y = self.root_instrument.freq_axis_y.get()
        phase_x = self.root_instrument.phase_x.get()
        phase_y = self.root_instrument.phase_y.get()
        xx, yy = np.meshgrid(ls_x, ls_y)
        output = (np.sin(xx+phase_x+random.random()))*np.cos(yy+phase_y)
        return output


class DummyInstrument(Instrument):

    def __init__(self, name, **kwargs):

        super().__init__(name, **kwargs)

        self.add_parameter('f_start',
                           initial_value=0,
                           unit='Hz',
                           label='f start',
                           vals=Numbers(0, 1e3),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('f_stop',
                           initial_value=10,
                           unit='Hz',
                           label='f stop',
                           vals=Numbers(1, 1e3),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('phase_x',
                           initial_value=0,
                           unit='Hz',
                           label='Phase X',
                           vals=Numbers(0, 1e3),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('phase_y',
                           initial_value=0,
                           unit='Hz',
                           label='Phase Y',
                           vals=Numbers(0, 1e3),
                           get_cmd=None,
                           set_cmd=None)

        self.add_parameter('n_points',
                           unit='',
                           initial_value=100,
                           vals=Numbers(1, 1e3),
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
                           setpoints=(self.freq_axis_x, self.freq_axis_y),
                           label='Spectrum',
                           parameter_class=DummyArray,
                           vals=Arrays(shape=(self.n_points.get_latest, self.n_points.get_latest)))


test_instrumment = DummyInstrument('test')

pi = np.pi
sliders = {'phase_x': (test_instrumment.phase_x, 0, pi, 0.1, 0),
           'phase_y': (test_instrumment.phase_y, 0, pi, 0.1, 0)}
test = LiveStream(data_func=test_instrumment.spectrum, sliders=sliders)


time.sleep(5)
test.video_mode_callback.stop()
test.video_mode_server.stop()
