import numpy as np
import time
import qcodes as qc
import os
from pulsequantum.livestream.example_instruments import FilterInstrument
from panel.io.server import StoppableThread
import tempfile
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


def test_livestream():

    test_instrumment = FilterInstrument('test')
    pi = np.pi
    sliders = {'phase_x': (test_instrumment.phase_x, 0, pi, 0.1, 0),
               'phase_y': (test_instrumment.phase_y, 0, pi, 0.1, 0)}
    test = LiveStream(data_func=test_instrumment.spectrum, sliders=sliders)
    time.sleep(5)

    assert type(test.video_mode_server) == StoppableThread
    assert test.video_mode_server.is_alive()
    test.video_mode_callback.stop()
    test.video_mode_server.stop()
