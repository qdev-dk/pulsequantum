import param


class MoreSettings(param.Parameterized):
    awg_amplitude = param.Parameter(default=4.5, doc='AWG amp')

    divider_fast = param.Parameter(default=10, doc='Divider fast channel')
    divider_slow = param.Parameter(default=10, doc='Divider slow channel')
