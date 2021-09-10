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
    to add controllers

        Attributes
        ----------
        data_func: Function that returns the data which should be livestreamed
                   ex. alazar_channel.get
        controller: Dict of the form {'name': (func_setget, step, value)

        Methods
        -------
        measure
            do0d on data_func

    """

    def __init__(self, data_func, voltagecontrolwidget,
                 port=12345, refresh_period=100):
        self.voltagecontrolwidget = voltagecontrolwidget
        self.port = port
        self.refresh_period = refresh_period
        self.data_func = data_func
        self.pipe = Pipe(data=[])
        self.data = self.data_func.get()
        self.counter = 1.0
        self.width = 100
        self.counter_wiget = pn.widgets.TextInput(name='counter', width=self.width,
                                                  value='None')
        self.image_dmap = hv.DynamicMap(hv.Image, streams=[self.pipe])
        self.image_dmap.opts(cmap='Magma', colorbar=True,
                             width=400,
                             height=350,
                             toolbar='above')
        self.set_colobar_scale()
        self.set_labels()

        self.measure_button = Button(name='Mesaure', button_type='primary',
                                     width=self.width)
        self.run_id_in_text = 'None'
        self.run_id_widget = pn.widgets.TextInput(name='run_id', width=self.width,
                                                  value=self.run_id_in_text)
        self.run_id_widget.force_new_dynamic_value

        self.measure_button.on_click(self.measure)
        self.plot_id_in_text = 'test'

        self.colorbar_button = Button(name='Reset colorbar', button_type='primary',
                                    width=self.width)
        self.colorbar_button.on_click(self.set_colobar_scale_event)

        self.close_button = Button(name='close server', button_type='primary',
                                   width=self.width)
        self.close_button.on_click(self.close_server_click)

        self.reset_average_button = Button(name='Reset average', button_type='primary',
                                    width=self.width)
        self.reset_average_button.on_click(self.reset_average)


        self.live_checkbox = pn.widgets.Checkbox(name='live_stream')

        self.voltage_control_widgets = []
        self.voltage_setget = []
        self.voltage_value_widget = []
        for key in voltagecontrolwidget.keys():
            self.voltage_control_create = VoltageWidget(displayname=key,
                                                        qchan=voltagecontrolwidget[key][0],
                                                        step=voltagecontrolwidget[key][1],
                                                        value=voltagecontrolwidget[key][2],
                                                        reset_average = self.reset_average)
            self.voltage_control_widgets.append([self.voltage_control_create.decreaseV_button,
                                                 self.voltage_control_create.voltage_display,
                                                 self.voltage_control_create.increaseV_button])
            self.voltage_setget.append(voltagecontrolwidget[key][0])
            self.voltage_value_widget.append(pn.widgets.TextInput(name=str(key), width=self.width,
                                             value='None'))

        self.dis()

    def dis(self):
        buttons = Column(self.measure_button,
                         self.run_id_widget,
                         self.reset_average_button,
                         self.counter_wiget,
                         self.colorbar_button,
                         self.close_button
                         )

        voltagesget = Column(*tuple(self.voltage_value_widget))
        voltagesset = Column()
        for i in self.voltage_control_widgets:
            voltagesset.append(Row(*tuple(i)))
        self.video_mode_callback = PeriodicCallback(self.data_grabber, self.refresh_period)

        self.gridspec = pn.GridSpec( width=800,
                                     height=600,)
        self.gridspec[:, 0] = buttons
        self.gridspec[:, 1:3] = Column(self.image_dmap, self.live_checkbox)
        self.gridspec[:, 3] = voltagesset + voltagesget

        self.video_mode_server = self.gridspec.show(port=self.port,
                                                    threaded=True)

        self.video_mode_callback.start()

    @gen.coroutine
    def data_grabber(self):
        for i, func in enumerate(self.voltage_setget):
            self.voltage_value_widget[i].value = str(func.get())
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
    def __init__(self, displayname, qchan, step, value, reset_average):
        self.qchan = qchan
        self.step = step
        self.voltage_value = value
        self.rest_average = reset_average
        self.width = 50
        self.increaseV_button = Button(name='+', button_type='primary',
                                       width=20, align=('start', 'end'))

        self.increaseV_button.on_click(self.voltage_increase)

        self.voltage_display = pn.widgets.TextInput(name=displayname,
                                                    value=str(self.voltage_value),
                                                    align=('start', 'end'),
                                                    disabled=False, width=self.width)
        self.decreaseV_button = Button(name='-', button_type='primary',
                                       width=20, align=('start', 'end'))
        self.decreaseV_button.on_click(self.voltage_decrease)

    def voltage_increase(self, event):
        self.voltage_change(self.step, event)

    def voltage_decrease(self, event):
        self.voltage_change(-self.step, event)

    def voltage_change(self, delta, event):
        self.voltage_value = float(self.voltage_display.value)
        self.voltage_value = self.voltage_value + delta
        self.voltage_display.value = str(self.voltage_value)
        self.qchan.set(self.voltage_value)
        self.rest_average(event)
