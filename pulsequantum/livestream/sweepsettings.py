import param


class SweepSettings(param.Parameterized):

    scan_options = param.ObjectSelector(objects=['Steps', 'Triangular', 'Sinusoidal'])
    channel_x = param.Integer(1)
    channel_y = param.Integer(2)
    x_range = param.Parameter(default=3e-2, doc="x range")
    y_range = param.Parameter(default=3e-2, doc="y range")
    x_dc_offecet = param.Parameter(default=0, doc="x dc offecet")
    y_dc_offecet = param.Parameter(default=0, doc="y dc offecet")
    x_time = param.Parameter(default=3e-2, doc="x time")
    y_steps = param.Parameter(default=40, doc="y steps")
    apply  = param.Action(lambda x: x, doc="""Record timestamp.""", precedence=0.7)