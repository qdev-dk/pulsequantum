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
from qcodes.utils.dataset.doNd import do0d

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
        measure
            do0d on data_func

    """

    def __init__(self,data_func,sliders):
        self.data_func = data_func
        self.pipe = Pipe(data=[])
        self.image_dmap = hv.DynamicMap(hv.Image, streams=[self.pipe])
        self.image_dmap.opts(cmap = 'Magma', xlim=(-0.6, 0.6), ylim=(-0.6, 0.6))
        self.measure_button = Button(name='mesaure',button_type = 'primary',
                              width=100)
        self.run_id_in_text = 'None'
        self.run_id_widget = pn.widgets.TextInput(name='run_id', value=self.run_id_in_text)


        def measure(event):
            data_do0d = do0d(self.data_func)
            self.run_id_widget.value = f'{data_do0d[0].run_id}'

        self.measure_button.on_click(measure)
        self.plot_id_in_text = 'test'
        
        self.sliders = []
        self.sliders_func = []
        for key in sliders.keys():
            self.sliders_func.append(sliders[key][0])
            self.sliders.append(pn.widgets.FloatSlider(name=str(key),
                                              start=sliders[key][1],
                                              end=sliders[key][2],
                                              step=sliders[key][3],
                                              value=sliders[key][4]))
        self.dis()


    def dis(self):
        col = (self.measure_button,
                self.run_id_widget,) + tuple(self.sliders)
        refresh_period = 500
        port = 12359
        self.video_mode_callback = PeriodicCallback(self.data_grabber, refresh_period)


        self.video_mode_server = Row(self.image_dmap, Column(*col)).show(port=port,threaded=True)
        self.video_mode_callback.start() 

    @gen.coroutine  
    def data_grabber(self):
        for i, func in enumerate(self.sliders_func):
            func(self.sliders[i].value)
        self.pipe.send(self.data_func())


        
