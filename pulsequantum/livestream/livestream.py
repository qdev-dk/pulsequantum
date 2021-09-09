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

    def __init__(self, data_func, sliders, voltagecontrolwidget,
                 port=12345, refresh_period=100):
        self.voltagecontrolwidget = voltagecontrolwidget
        self.port = port
        self.refresh_period = refresh_period
        self.data_func = data_func
        self.pipe = Pipe(data=[])
        self.data = self.data_func.get()
        self.counter = 1.0
        self.counter_wiget = pn.widgets.TextInput(name='counter',
                                            value='None')
        self.image_dmap = hv.DynamicMap(hv.Image, streams=[self.pipe])
        self.image_dmap.opts(cmap='Magma', colorbar=True,
                             width=500,
                             height=400,
                             toolbar='above')
        self.set_colobar_scale()
        self.set_labels()

        self.measure_button = Button(name='Mesaure', button_type='primary',
                                     width=100)
        self.run_id_in_text = 'None'
        self.run_id_widget = pn.widgets.TextInput(name='run_id',
                                                  value=self.run_id_in_text)
        self.run_id_widget.force_new_dynamic_value

        self.measure_button.on_click(self.measure)
        self.plot_id_in_text = 'test'

        self.colorbar_button = Button(name='Reset colorbar', button_type='primary',
                                    width=100)
        self.colorbar_button.on_click(self.set_colobar_scale_event)

        self.close_button = Button(name='close server', button_type='primary',
                                   width=100)
        self.close_button.on_click(self.close_server_click)

        self.reset_average_button = Button(name='Reset average', button_type='primary',
                                    width=100)
        self.reset_average_button.on_click(self.reset_average)


        self.live_checkbox = pn.widgets.Checkbox(name='live_stream')

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
            self.slider_value_widget.append(pn.widgets.TextInput(name=str(key),
                                            value='None'))
        self.voltage_control_widgets = []
        for key in voltagecontrolwidget.keys():
            self.voltage_control_create = VoltageWidget(displayname=voltagecontrolwidget[key][0],
                                                        step=voltagecontrolwidget[key][2],
                                                        value=voltagecontrolwidget[key][3])
            self.voltage_control_widgets.append([self.voltage_control_create.decreaseV_button,
                                                 self.voltage_control_create.voltage_display,
                                                 self.voltage_control_create.increaseV_button])

        print(type(self.voltage_control_widgets))
        print(self.voltage_control_widgets[0])
        self.dis()

    def dis(self):
        col1 = (Row(self.measure_button, self.close_button, self.colorbar_button,self.reset_average_button,self.counter_wiget),
                self.run_id_widget) + tuple(self.sliders)
        col2 = tuple(self.slider_value_widget) + (self.live_checkbox,)
        col3 = Column()
        for i in self.voltage_control_widgets:
            col3.append(Row(*tuple(i)))
        self.video_mode_callback = PeriodicCallback(self.data_grabber, self.refresh_period)
        self.gridspec = pn.GridSpec(sizing_mode='stretch_both')
        self.gridspec[:2, :2] = self.image_dmap
        self.gridspec[2:3, 0] = Column(*col1)
        self.gridspec[2:3, 1] = Column(*col2)
        self.gridspec[0, 2] = col3

        self.video_mode_server = self.gridspec.show(port=self.port,
                                                    threaded=True)

        self.video_mode_callback.start()

    @gen.coroutine
    def data_grabber(self):
        for i, func in enumerate(self.sliders_func):
            func(self.sliders[i].value)
            self.slider_value_widget[i].value = str(func.get())
        if self.live_checkbox.value:
            self.data_average()
            self.pipe.send((self.data_func.setpoints[1].get(),
                            self.data_func.setpoints[0].get(),
                            self.data))
    def data_average(self):
        self.counter_wiget.value = str(self.counter)
        self.data = ((self.counter-1)*self.data + self.data_func.get())/self.counter
        self.counter += 1.0

    def reset_average(self, event):
        self.counter = 1

    def measure(self, event):
        self.measure_button.loading = True
        data_do0d = do0d(self.data_func)
        self.run_id_widget.value = f'{data_do0d[0].run_id}'
        self.measure_button.loading = False

    def close_server_click(self, event):
        self.video_mode_server.stop()

    def voltage_increase(self, event):
        self.voltage_value = self.voltage_value + 1
        self.voltage_display.value = str(self.voltage_value)

    def voltage_decrease(self, event):
        self.voltage_value = self.voltage_value - 1
        self.voltage_display.value = str(self.voltage_value)

    def set_labels(self):
        xlabel = self.data_func.setpoints[0].label + ' ('+self.data_func.setpoints[0].unit + ')'
        ylabel = self.data_func.setpoints[1].label + ' ('+self.data_func.setpoints[1].unit + ')'
        clabel = self.data_func.label + ' (' + self.data_func.unit + ')'
        self.image_dmap.opts(xlabel=xlabel,
                             ylabel=ylabel,
                             clabel=clabel)

    def set_colobar_scale_event(self, event):
        self.colorbar_button.loading = True
        self.set_colobar_scale()
        self.colorbar_button.loading = False


    def set_colobar_scale(self):
        cmin = self.data.min()
        cmax = self.data.max()
        self.image_dmap.opts(clim=(cmin, cmax))

class VoltageWidget():
    def __init__(self, displayname, step, value):
        self.step = step
        self.voltage_value = value  # change later to get the value of the initialized voltage value
        self.increaseV_button = Button(name='+', button_type='primary',
                                       width=20, align=('start', 'end'))

        self.increaseV_button.on_click(self.voltage_increase)

        self.voltage_display = pn.widgets.TextInput(name=displayname,
                                                    value=str(self.voltage_value),
                                                    align=('start', 'end'),
                                                    disabled=True)
        self.decreaseV_button = Button(name='-', button_type='primary',
                                       width=20, align=('start', 'end'))
        self.decreaseV_button.on_click(self.voltage_decrease)

    def voltage_increase(self, event):
        self.voltage_value = self.voltage_value + self.step
        self.voltage_display.value = str(self.voltage_value)

    def voltage_decrease(self, event):
        self.voltage_value = self.voltage_value - self.step
        self.voltage_display.value = str(self.voltage_value)
