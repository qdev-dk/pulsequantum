import param


class PlotSettings(param.Parameterized):

    title = param.Parameter(default='Title', doc="Title")
    x_label = param.Parameter(default='X', doc="X label")
    y_label = param.Parameter(default='Y', doc="Y label")
    c_label = param.Parameter(default='C', doc="C label")
    c_max = param.Parameter(default=1, doc="colorbar max")
    c_min = param.Parameter(default=-1, doc="colorbar min")

