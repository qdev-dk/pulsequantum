from pulsequantum.livestream.videoinstrument import VideoInstrument
from pulsequantum.livestream.alazarsettings import AlazarConfig
from pulsequantum.livestream.alazarchansettings import AlazarChannelConfig

class AlazarVideo(VideoInstrument):
    """[summary]

    Args:
        VideoInstrument ([type]): [description]
    """
    def __init__(self, name, alazar, controller, channel, **kwargs):
        self.alazar = alazar
        self.controller = controller
        self.channel = channel
        self.alazarsettings = AlazarConfig(self.alazar)

        self.dis_tabs = []
        self.dis_tabs.append(('Alazar settings', self.alazarsettings.col))
        self.dis_tabs.append(('Alazar Channel', self.alazarchansettings.col))

        super().__init__(name, data_func=self.channel.data,
                         n_points=(self.channel.records_per_buffer(),
                                   self.controller.samples_per_record()),
                         **kwargs)´

        self.alazarchansettings = AlazarChannelConfig(controller=self.controller,
                                                      channel=self.channel,
                                                      aktion=self.update_n_points)

