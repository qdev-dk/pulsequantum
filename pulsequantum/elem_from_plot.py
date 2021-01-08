import numpy as np
import matplotlib.pyplot as plt
import broadbean as bb
from string import ascii_lowercase
from qcodes.dataset.plotting import plot_by_id

class LineBuilder:
    def __init__(self, line, ax, color):
        self.line = line
        self.ax = ax
        self.color = color
        self.xs = []
        self.ys = []
        self.cid = line.figure.canvas.mpl_connect('button_press_event', self)
        self.counter = 0
        self.shape_counter = 0
        self.shape = {}
        self.precision = 0.001

    def __call__(self, event):
        if event.inaxes != self.line.axes:
            return
        if self.counter == 0:
            self.xs.append(event.xdata)
            self.ys.append(event.ydata)
        if np.abs(event.xdata-self.xs[0])<=self.precision and np.abs(event.ydata-self.ys[0])<=self.precision and self.counter != 0:
            self.xs.append(self.xs[0])
            self.ys.append(self.ys[0])
            self.ax.scatter(self.xs,self.ys,s=120,color=self.color)
            self.ax.scatter(self.xs[0],self.ys[0],s=80,color='blue')
            self.ax.plot(self.xs,self.ys,color=self.color)
            self.line.figure.canvas.draw()
            self.shape[self.shape_counter] = [self.xs,self.ys]
            self.shape_counter = self.shape_counter + 1
            self.xs = []
            self.ys = []
            self.counter = 0
        else:
            if self.counter != 0:
                self.xs.append(event.xdata)
                self.ys.append(event.ydata)
            self.ax.scatter(self.xs,self.ys,s=120,color=self.color)
            self.ax.plot(self.xs,self.ys,color=self.color)
            self.line.figure.canvas.draw()
            self.counter = self.counter + 1


def elem_on_plot(id: int) -> tuple:
    fig, ax = plt.subplots(1)
    axes, cbaxes = plot_by_id(id, axes=ax)
    line = LineBuilder(axes[0],ax,'red')
    plt.show()
    return (line.xs, line.ys)


ramp = bb.PulseAtoms.ramp


def elem_from_lists(step_list_a: list, step_list_b: list,
                    duration: float = 1e-6, dac_a: float = 0, dac_b: float = 0,
                    divider_a: float = 1.0, divider_b: float = 1.0,
                    SR: float = 1e9,
                    chx: int = 1, chy: int = 2) -> bb.Element:
    #Make element from pulse table
    elem = bb.Element()
    blueprint_a = bb.BluePrint()
    blueprint_a.setSR(SR)
    blueprint_b = bb.BluePrint()
    blueprint_b.setSR(SR)
    for i in range(len(step_list_a)):
        step_a = (step_list_a[i]-dac_a)*divider_a
        step_b = (step_list_b[i]-dac_b)*divider_b
        blueprint_a.insertSegment(i, ramp, (step_a, step_a), name=ascii_lowercase[i], dur=duration)
        blueprint_b.insertSegment(i, ramp, (step_b, step_b), name=ascii_lowercase[i], dur=duration)

    elem.addBluePrint(chx, blueprint_a)
    elem.addBluePrint(chy, blueprint_b)
    elem.validateDurations()
    return elem
