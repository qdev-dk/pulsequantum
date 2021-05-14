import panel as pn
import holoviews as hv
from panel.widgets import Button
from panel import Row, Column
from qcodes.utils.dataset.doNd import do0d
from holoviews.streams import Pipe
from tornado.ioloop import PeriodicCallback
from tornado import gen


hv.extension('bokeh')


class LiveStream():
    """
    Class for live streaming data, without saving and with the possibility
    to add sliders/controllers

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

    def __init__(self, data_func, sliders, port=12345, refresh_period=100):
        self.port = port
        self.refresh_period = refresh_period
        self.data_func = data_func
        self.pipe = Pipe(data=[])
        self.image_dmap = hv.DynamicMap(hv.Image, streams=[self.pipe])
        self.image_dmap.opts(cmap='Magma')
        self.set_labels()
        self.measure_button = Button(name='Mesaure', button_type='primary',
                                     width=100)
        self.run_id_in_text = 'None'
        self.run_id_widget = pn.widgets.TextInput(name='run_id', value=self.run_id_in_text)
        self.run_id_widget.force_new_dynamic_value

        self.measure_button.on_click(self.measure)
        self.plot_id_in_text = 'test'

        self.close_button = Button(name='close server', button_type='primary',
                                   width=100)

        self.close_button.on_click(self.close_server_click)

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
        col = (self.measure_button, self.close_button,
               self.run_id_widget,) + tuple(self.sliders)

        self.video_mode_callback = PeriodicCallback(self.data_grabber, self.refresh_period)
        self.video_mode_server = Row(self.image_dmap,
                                     Column(*col)).show(port=self.port, threaded=True)
        self.video_mode_callback.start()

    @gen.coroutine
    def data_grabber(self):
        for i, func in enumerate(self.sliders_func):
            func(self.sliders[i].value)
        self.pipe.send((self.data_func.setpoints[0].get(),
                       self.data_func.setpoints[1].get(),
                       self.data_func.get()))

    def measure(self, event):
        data_do0d = do0d(self.data_func)
        self.run_id_widget.value = f'{data_do0d[0].run_id}'

    def close_server_click(self, event):
        self.video_mode_server.stop()

    def set_labels(self):
        xlabel = self.data_func.setpoints[0].label + ' ('+self.data_func.setpoints[0].unit + ')'
        ylabel = self.data_func.setpoints[1].label + ' ('+self.data_func.setpoints[1].unit + ')'
        self.image_dmap.opts(xlabel=xlabel,
                             ylabel=ylabel)
