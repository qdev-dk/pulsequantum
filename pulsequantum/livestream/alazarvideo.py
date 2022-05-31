from pulsequantum.livestream.videoinstrument import VideoInstrument
from pulsequantum.livestream.alazarsettings import AlazarConfig
from pulsequantum.livestream.alazarchansettings import AlazarChannelConfig

class AlazarVideo(VideoInstrument):
    """[summary]

    Args:
        VideoInstrument ([type]): [description]
    """
    def __init__(self, name, alazar, controller, **kwargs):
        self.alazar = alazar
        self.controller = controller
  

        super().__init__(name, data_func=self.controller.dataset_acquisition,
                         n_points=(self.controller.acquisition_config['records_per_buffer'],
                                   self.controller.acquisition_config['samples_per_record']),
                         **kwargs)

        self.alazarchansettings = AlazarChannelConfig(controller=self.controller,
                                                      aktion=self.update_n_points)
        self.alazarsettings = AlazarConfig(self.alazar,
                                           aktion=self.alazarchansettings.config)

        self.dis_tabs = []
        self.dis_tabs.append(('Alazar settings', self.alazarsettings.col))
        self.dis_tabs.append(('Alazar Channel', self.alazarchansettings.col))

