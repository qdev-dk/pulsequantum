#import qcodes.instrument_drivers.QDevil.QDevil_QDAC as QDac
from pulsequantum.livestream.qdac_alazar_interface.QDevil_QDAC_livestream import QDac_livestream as QDac
from qdev_wrappers.alazar_controllers.ATSChannelController import ATSChannelController


class MyATSChannelController_livestream(ATSChannelController):
    
    """additional paramteres taht this subclass has:

    """
    def __init__(self, name,
                 alazar_name: str,
                 qdac: QDac,
                 filter: str = 'win',
                 numtaps: int =101,
                 start_slow: float = -0.275,
                 start_fast: float = -0.245,
                 step_slow: float = 30e-3,
                 step_fast: float = 30e-3,
                 slow_channel: int = 10,
                 fast_channel: int = 12,
 #                sync_output_slow: int = 2,
                 sync_output_fast: int = 1,
                 slow_steps: int = 30,
                 fast_steps: int = 30,
                 step_length: float = 0.001,
                 n_avg: int = 1,
                 run_qdac: bool = True,                 
                 **kwargs):
        super().__init__(name, alazar_name, filter, numtaps, **kwargs)
        self.qdac = qdac
        self.run_qdac = run_qdac
        self.start_slow = start_slow
        self.start_fast = start_fast
        self.step_slow = step_slow
        self.step_fast = step_fast
        self.slow_channel = slow_channel
        self.fast_channel = fast_channel
 #       self.fsync_output_slow = sync_output_slow
        self.sync_output_fast = sync_output_fast
        self.slow_steps = slow_steps
        self.fast_steps = fast_steps
        self.step_length = step_length
        self.n_avg = n_avg
    def pre_acquire(self):
        if self.run_qdac is True:
    #        self.qdac.channels[self.slow_channel-1].sync(self.sync_output_slow)
            self.qdac.channels[self.fast_channel-1].sync(self.sync_output_fast)
            self.qdac.ramp_voltages_2d_avg(slow_chans=[self.slow_channel],
                                       slow_vstart=[self.start_slow],
                                       slow_vend=[self.start_slow + self.step_slow],
                                       fast_chans=[self.fast_channel],
                                       fast_vstart=[self.start_fast],
                                       fast_vend=[self.start_fast + self.step_fast],
                                       slow_steps=self.slow_steps,
                                       fast_steps=self.fast_steps,
                                       step_length=self.step_length,
                                       n_avg = self.n_avg)
