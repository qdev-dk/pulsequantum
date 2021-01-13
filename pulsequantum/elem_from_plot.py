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
        self.ramp = []
        self.cid = line.figure.canvas.mpl_connect('button_press_event', self)
        self.counter = 0
        self.precision = 0.0005

    def __call__(self, event):
        if event.inaxes != self.line.axes:
            return
        if event.dblclick:
            if self.counter == 0:
                self.xs.append(event.xdata)
                self.ys.append(event.ydata)
                self.right_or_left(str(event.button))
            if np.abs(event.xdata-self.xs[self.counter - 1]) <= self.precision and np.abs(event.ydata-self.ys[self.counter - 1]) <= self.precision and self.counter != 0:
                self.xs.append(self.xs[self.counter - 1])
                self.ys.append(self.ys[self.counter - 1])
                self.right_or_left(str(event.button))
                self.plot_line()
                self.counter = self.counter + 1
            else:
                if self.counter != 0:
                    self.xs.append(event.xdata)
                    self.ys.append(event.ydata)
                    self.right_or_left(str(event.button))
                self.plot_line()
                self.counter = self.counter + 1

    def right_or_left(self, rightleftmouse: str) -> None:
        if rightleftmouse == 'MouseButton.RIGHT':
            self.ramp.append(1)
        else:
            self.ramp.append(0)

    def plot_line(self) -> None:
        plateau = list(zip(*[(self.xs[i], self.ys[i]) for i in range(len(self.ramp)) if self.ramp[i] == 0]))
        ramp = list(zip(*[(self.xs[i], self.ys[i]) for i in range(len(self.ramp)) if self.ramp[i] == 1]))
        if plateau != []:
            self.ax.scatter(plateau[0], plateau[1], s=120, color=self.color, marker='o')
        if ramp != []:
            self.ax.scatter(ramp[0], ramp[1], s=120, color='black', marker='x')
        self.plot_line_segment()
        self.line.figure.canvas.draw()

    def plot_line_segment(self):
        for i in range(len(self.xs)):
            if i > 0:
                if self.ramp[i] == 1:
                    linestyle = '-'
                else:
                    linestyle = '--'
                self.ax.plot(self.xs[i-1:i+1], self.ys[i-1:i+1], color=self.color, linestyle=linestyle)


def elem_on_plot(id: int) -> tuple:
    fig, ax = plt.subplots(1)
    axes, cbaxes = plot_by_id(id, axes=ax)
    line = LineBuilder(axes[0], ax, 'red')
    plt.show()
    return (line.xs, line.ys, line.ramp)


ramp = bb.PulseAtoms.ramp


def elem_from_lists(step_list_a: list, step_list_b: list, ramplist: list,
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
    step_a_old = 0
    step_b_old = 0
    for i in range(len(step_list_a)):
        if ramplist[i] == 1:
            step_a = (step_list_a[i]-dac_a)*divider_a
            step_b = (step_list_b[i]-dac_b)*divider_b
            blueprint_a.insertSegment(i, ramp, (step_a_old, step_a), name=ascii_lowercase[i], dur=duration)
            blueprint_b.insertSegment(i, ramp, (step_b_old, step_b), name=ascii_lowercase[i], dur=duration)
        else:
            step_a = (step_list_a[i]-dac_a)*divider_a
            step_b = (step_list_b[i]-dac_b)*divider_b
            blueprint_a.insertSegment(i, ramp, (step_a, step_a), name=ascii_lowercase[i], dur=duration)
            blueprint_b.insertSegment(i, ramp, (step_b, step_b), name=ascii_lowercase[i], dur=duration)
        step_a_old = step_a
        step_b_old = step_b

    elem.addBluePrint(chx, blueprint_a)
    elem.addBluePrint(chy, blueprint_b)
    elem.validateDurations()
    return elem
