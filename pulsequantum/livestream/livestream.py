import holoviews as hv
from panel import Tabs, bind
from panel import GridSpec
from panel.widgets import Button, TextInput, Checkbox, Select
from panel import Row, Column
from qcodes.utils.dataset.doNd import do0d
from holoviews.streams import Pipe
from tornado.ioloop import PeriodicCallback
from tornado import gen
from typing import Optional, Tuple
from pulsequantum.livestream.plotsettings import PlotSettings
from pulsequantum.livestream.alazarsettings import AlazarConfig
from pulsequantum.livestream.alazarchansettings import AlazarChannelConfig
from pulsequantum.livestream.sweepsettings import SweepSettings
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

    def __init__(self, video, controllers,
                 dc_controllers: Optional[Tuple] = None,
                 port=0, refresh_period=100,
                 alazar=None,
                 acontroller=None,
                 achannel=None
                 ):
        self.video = video
        self.controllers = controllers
        self.port = port
        self.refresh_period = refresh_period
        self.data_func = video.videorunningaverage
        self.alazar = alazar
        self.acontroller = acontroller
        self.achannel = achannel

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

        self.plotsettings = PlotSettings()
        self.bound_plotsettings = bind(self.setplotsettings,
                                       title=self.plotsettings.param.title,
                                       xlabel=self.plotsettings.param.x_label,
                                       ylabel=self.plotsettings.param.y_label,
                                       clabel=self.plotsettings.param.c_label,
                                       cmin=self.plotsettings.param.c_min,
                                       cmax=self.plotsettings.param.c_max)

        self.set_colobar_scale()
        self.set_labels()
        self.sweepsettings = SweepSettings()
        if self.alazar:
            self.alazarsettings = AlazarConfig(self.alazar)
        if self.achannel and self.acontroller:
            self.alazarchansettings = AlazarChannelConfig(controller=self.acontroller, channel=self.achannel)

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

        self.average = Select(name='Average',
                              options=['Off', 'Continues', 'Running'])

        self.set_average = Button(name='Set Average', button_type='primary',
                                  width=self.button_width)
        self.set_average.on_click(self.set_data_func)
        self.max_average_text = TextInput(name='max # number of averages',
                                          value=str(self.video.videorunningaverage.max_average),
                                          align=('start', 'end'),
                                          disabled=False, width=self.button_width, margin=(0, 15))

        self.live_checkbox = Checkbox(name='live_stream')
        self.auto_colobar_scale = Checkbox(name='auto_colobar_scale')

        self.control_widgets = []
        self.control_setget = []
        self.controle_value_widget = []
        self.axes = (self.video.x, self.video.y)
        if dc_controllers:
            for i, key in enumerate(dc_controllers.keys()):
                self.add_controle_wiget(key, dc_controllers[key],
                                        dcWidget, self.axes[i])
        for key in controllers.keys():
            self.add_controle_wiget(key, controllers[key], ControleWidget)

        self.dis()

    def dis(self):
        buttons = Column(self.measure_button,
                         self.run_id_widget,
                         self.reset_average_button,
                         self.nr_average_wiget,
                         self.colorbar_button,
                         self.close_button
                         )

        controllersget = Column(*tuple(self.controle_value_widget))
        controllersset = Column()
        for i in self.control_widgets:
            controllersset.append(Row(*tuple(i)))
        self.video_mode_callback = PeriodicCallback(self.data_grabber,
                                                    self.refresh_period)

        self.gridspec = GridSpec(width=800,
                                 height=600)
        self.gridspec[:, 0] = buttons
        self.gridspec[:, 1:3] = Column(self.image_dmap,
                                       Column(self.live_checkbox,
                                              self.auto_colobar_scale),
                                       self.average,
                                       self.set_average,
                                       self.max_average_text)
        self.gridspec[:, 3] = controllersset + controllersget
        self.dis_tabs = [('Video', self.gridspec),
                    ('Plot Settings', Row(self.plotsettings, self.bound_plotsettings)),
                    ('Sweep settings', self.sweepsettings),
                    ]
        if self.alazar:
            self.dis_tabs.append(('Alazar settings', self.alazarsettings.col))
            
        if self.achannel and self.acontroller:
            self.dis_tabs.append(('Alazar Channel', self.alazarchansettings.col))

        self.video_mode_server = Tabs(*self.dis_tabs,
                                      dynamic=True).show(port=self.port,
                                                         threaded=True)

        self.video_mode_callback.start()

    @gen.coroutine
    def data_grabber(self):
        for i, func in enumerate(self.control_setget):
            self.controle_value_widget[i].value = str(func.get())
        if self.live_checkbox.value:
            self.auto_set_collorbar()
            self.data = self.data_func.get()
            self.nr_average_wiget.value = str(self.data_func.root_instrument.nr_average.get())
            self.pipe.send((self.data_func.setpoints[1].get(),
                            self.data_func.setpoints[0].get(),
                            self.data))

    def reset_average(self, event):
        self.data_func.reset_average()

    def measure(self, event):
        self.measure_button.loading = True
        data_do0d = do0d(self.data_func)
        self.run_id_widget.value = f'{data_do0d[0].run_id}'
        self.measure_button.loading = False

    def close_server_click(self, event):
        self.video_mode_server.stop()

    def set_labels(self):
        self.plotsettings.x_label = self.data_func.setpoints[1].label + ' ('+self.data_func.setpoints[1].unit + ')'
        self.plotsettings.y_label = self.data_func.setpoints[0].label + ' ('+self.data_func.setpoints[0].unit + ')'
        self.plotsettings.c_label = self.data_func.label + ' (' + self.data_func.unit + ')'

    def set_colobar_scale_event(self, event):
        self.colorbar_button.loading = True
        self.set_colobar_scale()
        self.colorbar_button.loading = False

    def auto_set_collorbar(self):
        if self.auto_colobar_scale.value:
            self.set_colobar_scale()

    def set_colobar_scale(self):
        cmin = self.data.min()
        cmax = self.data.max()
        self.plotsettings.c_min = cmin
        self.plotsettings.c_max = cmax

    def setplotsettings(self, title, xlabel, ylabel, clabel, cmin, cmax):
        return self.image_dmap.opts(title=title,
                                    xlabel=xlabel,
                                    ylabel=ylabel,
                                    clabel=clabel,
                                    clim=(cmin, cmax))

    def add_controle_wiget(self, name, controller, controllertype, axis=None):
        control_create = controllertype(displayname=name,
                                        qchan=controller[0],
                                        step=controller[1],
                                        value=controller[2],
                                        reset_average=self.reset_average,
                                        axis=axis)

        self.control_widgets.append([control_create.decrease_button_big,
                                     control_create.decrease_button_small,
                                     control_create.controle_display,
                                     control_create.increase_button_small,
                                     control_create.increase_button_big])

        self.control_setget.append(controller[0])
        self.controle_value_widget.append(TextInput(name=name,
                                                    width=self.button_width,
                                                    value='None'))

    def set_data_func(self, event):
        if self.average.value == 'Running':
            self.video.videorunningaverage.max_average = int(self.max_average_text.value)
            self.data_func = self.video.videorunningaverage
            self.data_func.reset_average()
        elif self.average.value == 'Continues':
            self.data_func = self.video.videoaverage
            self.data_func.reset_average()
        else:
            self.data_func = self.video.video
            self.data_func.reset_average()

    def callback(self, target, event):
        target.opts(clim=(event.new, event.new+1))


class ControleWidget():
    def __init__(self, displayname, qchan, step, value, reset_average, axis,
                 *args, **kwargs):
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
                                          disabled=False,
                                          width=self.button_width, margin=(0, 15))

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
        self.controle_change(-self.step/10, event)

    def controle_change(self, step, event):
        self.controle_value = float(self.controle_display.value)
        self.controle_value = self.controle_value + step
        self.controle_display.value = str(self.controle_value)
        self.qchan.set(self.controle_value)
        self.rest_average(event)


class dcWidget(ControleWidget):
    def __init__(self, displayname, qchan,
                 step, value, reset_average, axis,
                 *args, **kwargs):
        super().__init__(displayname, qchan, step,
                         value, reset_average, axis=None,
                         *args, **kwargs)
        self.axis = axis

    def controle_change(self, step, event):
        self.controle_value = float(self.controle_display.value)
        self.controle_value = self.controle_value + step
        self.controle_display.value = str(self.controle_value)
        self.qchan.set(self.controle_value)
        self.axis.V_dc.set(self.qchan.get())
        self.axis.V_axis.reset()
        self.rest_average(event)
