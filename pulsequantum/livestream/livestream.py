import panel as pn
import numpy as np
import time
import holoviews as hv
from panel.widgets import Button, Toggle
from panel import Row, Column
from qcodes.utils.dataset.doNd import do0d
from holoviews import opts
from holoviews.streams import Pipe
from holoviews import opts
from tornado.ioloop import PeriodicCallback
from tornado import gen

hv.extension('bokeh')

class LiveStream():
    """
    Class for live streaming data, without saving and with the possibility to add sliders/controllers

        Attributes
        ----------
        data_func: Function that returns the data which should be livestreamed
                   ex. alazar_channel.get
        sliders: Dict of the form {'name': (func_set, min_value,max_value)

        Methods
        -------
        set_averages
            set the number of averages on the Alazar cart

    """

    def __init__(self,data_func,sliders):
        self.data_func = data_func
        #self.measure_func = measure_func
        self.pipe = Pipe(data=[])
        self.image_dmap = hv.DynamicMap(hv.Image, streams=[self.pipe])
        self.image_dmap.opts(cmap = 'Magma', xlim=(-0.6, 0.6), ylim=(-0.6, 0.6))
        self.measure_button = Button(name='mesaure',button_type = 'primary',
                              width=100)
        def measure(event):
            data1 = do0d(self.data_func)
        self.measure_button.on_click(measure)
        
        self.sliders = []
        self.sliders_func = []
        for key in sliders.keys():
            self.sliders_func.append(sliders[key][0])
            self.sliders.append(pn.widgets.FloatSlider(name=str(key),
                                              start=0,
                                              end=3.141,
                                              step=0.01,
                                              value=1.57))
            
    
    def mesaure(event):
        data1 = do0d(self.data_func)
        
    def dis(self):
        col = (self.measure_button,)+tuple(self.sliders)
        refresh_period = 100
        port = 12355
        video_mode_callback = PeriodicCallback(self.data_grabber, refresh_period)
        video_mode_server = Row(self.image_dmap, Column(*col)).show(port=port)
    
    @gen.coroutine
    def data_grabber(self):
        for i, func in enumerate(self.sliders_func):
            func(self.sliders[i].value)
            self.pipe.send(self.data_func())

    ##refresh_period = 100
    #video_mode_callback = PeriodicCallback(self.data_grabber, refresh_period)
        
    def run(self):
        for i in np.linspace(0, np.pi*10, 200):
            for i, func in enumerate(self.sliders_func):
                func(self.sliders[i].value)
            time.sleep(0.1)
            self.pipe.send(self.data_func())