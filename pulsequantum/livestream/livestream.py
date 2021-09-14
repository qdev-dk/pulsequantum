import holoviews as hv
from panel import GridSpec
from panel.widgets import Button, TextInput, Checkbox
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
        controllers: Dict of the form {'name': (func_setget, step, value)}

        Methods
        -------
        measure
            do0d on data_func

    """

    def __init__(self, data_func, controllers,
                 port=0, refresh_period=100):
        self.controllers = controllers
        self.port = port
        self.refresh_period = refresh_period
        self.data_func = data_func
        self.pipe = Pipe(data=[])
        self.data = self.data_func.get()
        self.nr_average = 1.0
        self.button_width = 100
        self.nr_average_wiget = TextInput(name='nr_average',
                                          width=self.button_width,
                                          value='None')
        self.image_dmap = hv.DynamicMap(hv.Image, streams=[self.pipe])
        self.image_dmap.opts(cmap='Magma', colorbar=True,
                             width=400,
                             height=350,
                             toolbar='above')
        self.set_colobar_scale()
        self.set_labels()

        self.measure_button = Button(name='Mesaure', button_type='primary',
                                     width=self.button_width)
        self.measure_button.on_click(self.measure)

        self.run_id_in_text = 'None'
        self.run_id_widget = TextInput(name='run_id',
                                       width=self.button_width,
                                       value=self.run_id_in_text)
        self.run_id_widget.force_new_dynamic_value

        self.colorbar_button = Button(name='Reset colorbar',
                                      button_type='primary',
                                      width=self.button_width)
        self.colorbar_button.on_click(self.set_colobar_scale_event)

        self.close_button = Button(name='close server', button_type='primary',
                                   width=self.button_width)
        self.close_button.on_click(self.close_server_click)

        self.reset_average_button = Button(name='Reset average',
                                           button_type='primary',
                                           width=self.button_width)
        self.reset_average_button.on_click(self.reset_average)

        self.live_checkbox = Checkbox(name='live_stream')

        self.control_widgets = []
        self.control_setget = []
        self.controle_value_widget = []
        for key in controllers.keys():
            self.control_create = ControleWidget(displayname=key,
                                                 qchan=controllers[key][0],
                                                 step=controllers[key][1],
                                                 value=controllers[key][2],
                                                 reset_average=self.reset_average)
            self.control_widgets.append([self.control_create.decrease_button_big,
                                         self.control_create.decrease_button_small,
                                         self.control_create.controle_display,
                                         self.control_create.increase_button_small,
                                         self.control_create.increase_button_big])
            self.control_setget.append(controllers[key][0])
            self.controle_value_widget.append(TextInput(name=str(key),
                                                        width=self.button_width,
                                                        value='None'))

        self.dis()

    def dis(self):
        buttons = Column(self.measure_button,
                         self.run_id_widget,
                         self.reset_average_button,
                         self.nr_average_wiget,
                         self.colorbar_button,
                         self.close_button
                         )

        controlersget = Column(*tuple(self.controle_value_widget))
        controlersset = Column()
        for i in self.control_widgets:
            controlersset.append(Row(*tuple(i)))
        self.video_mode_callback = PeriodicCallback(self.data_grabber,
                                                    self.refresh_period)

        self.gridspec = GridSpec(width=800,
                                 height=600)
        self.gridspec[:, 0] = buttons
        self.gridspec[:, 1:3] = Column(self.image_dmap, self.live_checkbox)
        self.gridspec[:, 3] = controlersset + controlersget

        self.video_mode_server = self.gridspec.show(port=self.port,
                                                    threaded=True)

        self.video_mode_callback.start()

    @gen.coroutine
    def data_grabber(self):
        for i, func in enumerate(self.control_setget):
            self.controle_value_widget[i].value = str(func.get())
        if self.live_checkbox.value:
            self.data_average()
            self.pipe.send((self.data_func.setpoints[1].get(),
                            self.data_func.setpoints[0].get(),
                            self.data))

    def data_average(self):
        self.nr_average_wiget.value = str(self.nr_average)
        self.data = ((self.nr_average-1)*self.data + self.data_func.get())/self.nr_average
        self.nr_average += 1.0

    def reset_average(self, event):
        self.nr_average = 1

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


class ControleWidget():
    def __init__(self, displayname, qchan, step, value, reset_average):
        self.qchan = qchan
        self.step = step
        self.controle_value = value
        self.rest_average = reset_average
        self.button_width = 100
        button_options = dict(button_type='primary', margin=(0, 15),
                              width=15, align=('start', 'end'))

        self.increase_button_big = Button(name='++', **button_options)
        self.increase_button_small = Button(name='+', **button_options)

        self.increase_button_big.on_click(self.controle_increase_big)
        self.increase_button_small.on_click(self.controle_increase_small)

        self.controle_display = TextInput(name=displayname,
                                          value=str(self.controle_value),
                                          align=('start', 'end'),
                                          disabled=False, width=self.button_width,margin=(0, 15))

        self.decrease_button_big = Button(name='- -', **button_options)
        self.decrease_button_small = Button(name='-', **button_options)
        self.decrease_button_big.on_click(self.controle_decrease_big)
        self.decrease_button_small.on_click(self.controle_decrease_small)

    def controle_increase_big(self, event):
        self.controle_change(self.step, event)

    def controle_decrease_big(self, event):
        self.controle_change(-self.step, event)

    def controle_increase_small(self, event):
        self.controle_change(self.step/10, event)

    def controle_decrease_small(self, event):
        self.controle_change(self.step/10, event)

    def controle_change(self, step, event):
        self.controle_value = float(self.controle_display.value)
        self.controle_value = self.controle_value + step
        self.controle_display.value = str(self.controle_value)
        self.qchan.set(self.controle_value)
        self.rest_average(event)
