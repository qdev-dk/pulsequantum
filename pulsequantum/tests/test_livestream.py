import pytest
import numpy as np
import time
import qcodes as qc
import os
import tempfile
from pulsequantum.livestream.example_instruments import FilterInstrument
from panel.io.server import StoppableThread
from pulsequantum.livestream.livestream import LiveStream
from qcodes import initialise_or_create_database_at, \
    load_or_create_experiment
from pulsequantum.livestream.videoinstrument import VideoInstrument
from qcodes.utils.dataset.doNd import do0d
from qcodes.dataset.data_set import load_by_id

@pytest.fixture
def source_db_path(tmp_path):
    source_db_path = os.path.join(tmp_path, 'source.db')
    return source_db_path

@pytest.fixture(scope="function")
def source_db(source_db_path):
    initialise_or_create_database_at(source_db_path)

@pytest.fixture(scope="function")
def set_up_station():
    exp = load_or_create_experiment('for_test', sample_name='no sample')
    yield
    exp.conn.close()


@pytest.fixture
def test_instrument():
    test_instrument = FilterInstrument("test_instrument")
    yield test_instrument
    test_instrument.close()

@pytest.fixture
def video(test_instrument):
    video = VideoInstrument(name='video',
                            data_func=test_instrument.spectrum_and_noise.get,
                            n_points=(121,121)
                           )  
    yield video
    video.close()

@pytest.fixture
def test_SC(video):
    station = qc.Station()
    station.add_component(video)
    yield station

@pytest.fixture(scope="function")
def live(test_instrument, video):

    controllers = {'phase_x': (test_instrument.phase_x,0.1,0),
                   'phase_y': (test_instrument.phase_y,0.1,0)}

    live = LiveStream(data_func=video.videoaverage,controllers=controllers, port=0, refresh_period=500)

    yield live

    live.video_mode_callback.stop()
    live.video_mode_server.stop()

def test_livestream(live):
    assert type(live.video_mode_server) == StoppableThread
    assert live.video_mode_server.is_alive()





def test_nr_average(source_db, set_up_station,video, test_SC,live):
    video.videoaverage.reset_average()
    data = do0d(video.videoaverage)
    blabla =load_by_id(data[0].run_id)
    assert blabla.snapshot['station']['instruments']['video']['parameters']['nr_average']['value'] == 1
    data = do0d(video.videoaverage)
    blabla =load_by_id(data[0].run_id)
    assert blabla.snapshot['station']['instruments']['video']['parameters']['nr_average']['value'] == 2
    live.measure(event=True)
    assert int(live.run_id_widget.value) == 3
    

