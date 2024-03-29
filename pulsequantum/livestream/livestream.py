from logging import disable
import panel as pn
import holoviews as hv
from panel.io import state
from panel.pane.markup import Str
from panel.widgets import Button
from panel import Row, Column
from qcodes.utils.dataset.doNd import do0d
from holoviews.streams import Pipe
from tornado.ioloop import PeriodicCallback
from tornado import gen


hv.extension('bokeh')
#hv.extension('matplotlib')

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
        #self.image_dmap = hv.DynamicMap(hv.HeatMap, streams=[self.pipe])

        self.image_dmap.opts(cmap='Magma', colorbar=True,
                             clim=(-2, 2),
                             width=500,
                             height=400,
                             toolbar='above')
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
        self.live_checkbox = pn.widgets.Checkbox(name='live_stream')

        self.increaseV_button = Button(name='+', button_type='primary',
                                        width=20, align=('start','end'))

        self.increaseV_button.on_click(self.voltage_increase)
        self.decreaseV_button = Button(name='-', button_type='primary',
                                        width=20,align=('start','end'))

        self.decreaseV_button.on_click(self.voltage_decrease)
        
        self.voltage_value = 5
        self.voltage_display = pn.widgets.TextInput(name='Voltage', value=str(self.voltage_value),align=('start','end'),disabled=True)
        self.slider_value_widget = []
        self.sliders = []
        self.sliders_func = []
        for key in sliders.keys():
            self.sliders_func.append(sliders[key][0])
            self.sliders.append(pn.widgets.FloatSlider(name=str(key),
                                                       start=sliders[key][1],
                                                       end=sliders[key][2],
                                                       step=sliders[key][3],
                                                       value=sliders[key][4]))
            self.slider_value_widget.append(pn.widgets.TextInput(name=str(key), value='None'))
        self.dis()

    def dis(self):
        col1 = (Row(self.measure_button, self.close_button),
               self.run_id_widget) + tuple(self.sliders)
        col2 = tuple(self.slider_value_widget) + (self.live_checkbox,)
        col3 = (self.decreaseV_button, self.voltage_display,self.increaseV_button)

        self.video_mode_callback = PeriodicCallback(self.data_grabber, self.refresh_period)
        self.video_mode_server = pn.GridSpec(width=800, height=600)


        self.video_mode_server[:2, :2] = self.image_dmap
        self.video_mode_server[2:3, 0] = Column(*col1)
        self.video_mode_server[2:3, 1] = Column(*col2)
        self.video_mode_server[0, 2] = Row(*col3)

        self.video_mode_server.show(port=self.port,threaded=True)

    
        self.video_mode_callback.start()

    @gen.coroutine
    def data_grabber(self):
        for i, func in enumerate(self.sliders_func):
            func(self.sliders[i].value)
            self.slider_value_widget[i].value = str(func.get())
        if self.live_checkbox.value:
            self.pipe.send((self.data_func.setpoints[1].get(),
                            self.data_func.setpoints[0].get(),
                            self.data_func.get()))

    def measure(self, event):
        data_do0d = do0d(self.data_func)
        self.run_id_widget.value = f'{data_do0d[0].run_id}'

    def close_server_click(self, event):
        self.video_mode_server.stop()

    def voltage_increase(self, event):
        self.voltage_value = self.voltage_value +1
        self.voltage_display.value = str(self.voltage_value)

    def voltage_decrease(self, event):
        self.voltage_value = self.voltage_value -1
        self.voltage_display.value = str(self.voltage_value)


    def set_labels(self):
        xlabel = self.data_func.setpoints[0].label + ' ('+self.data_func.setpoints[0].unit + ')'
        ylabel = self.data_func.setpoints[1].label + ' ('+self.data_func.setpoints[1].unit + ')'
        clabel = self.data_func.label + ' (' + self.data_func.unit + ')'
        self.image_dmap.opts(xlabel=xlabel,
                             ylabel=ylabel,
                             clabel=clabel)
