import numpy as np
import matplotlib
import qcodes as qc
import matplotlib.pyplot as plt
from qcodes.dataset.data_set import load_by_id
from qcodes.dataset.plotting import plot_by_id
import broadbean as bb
from broadbean.plotting import plotter

qc.config["core"]["db_location"] = 'C:\\Users\\rbcma\\repos\\PulsedMeasurementCode\\Amber.db' 

def annotateshape(plotid,x1,y1,elem,chx,chy,divx,divy):
    '''
    plotid: experiment id of the plot of interest, for example a 2D honeycomb diagram
    x1 and yl: x and y component of the initial pulsing point
    elem: element (existing in kernel) created with PULSEGUI or broadbean
    chx and chy: AWG channel associated with the x and y direction in the plotid
    returns centre of gravity of single pulses and also the entire pulse sequence in x and y (COGx, COGy) to make sure this coincides with DC point
    '''
    
    
    
    fig, ax = plt.subplots(1)
    axes, cbaxes = plot_by_id(plotid, axes=ax)
    data = load_by_id(plotid)
    s = data.paramspecs
    names = list(s.keys())
    #ax.set_ylabel(f'{s[names[1]].label} ({s[names[1]].unit})',size=20)
    #ax.set_xlabel(f'{s[names[0]].label} ({s[names[0]].unit})',size=20)
    
    ax.set_title('#PulseB sequence on data {}'.format(plotid),size=20)
    #cbaxes = cbaxes[0]
    cbaxes[0].set_label(f'{s[names[2]].label} ({s[names[2]].unit})',size=20)
    
    #divx=11.5
    #divy=11.75

    x2 = []
    y2 = []
    seg_dur = []
    num=len(elem.description['{}'.format(chx)])-4
    pulse_names = []
    color=['yellow','red','green','lightblue','violet','pink','yellow','red','green','lightblue','violet','pink']

    for i in range(num):
        x2.append((elem.description['{}'.format(chx)]['segment_%02d'%(i+1)]['arguments']['stop'])/divx)
        y2.append((elem.description['{}'.format(chy)]['segment_%02d'%(i+1)]['arguments']['stop'])/divy)
        seg_dur.append(elem.description['{}'.format(chy)]['segment_%02d'%(i+1)]['durations'])
        pulse_names.append(elem.description['{}'.format(chx)]['segment_%02d'%(i+1)]['name'])
        print(elem.description['{}'.format(chx)]['segment_%02d'%(i+1)]['name'])

    COGx = np.sum(np.array(x2)*np.array(seg_dur)/elem.duration)
    COGy = np.sum(np.array(y2)*np.array(seg_dur)/elem.duration)
    
    for n in range(len(x2)):
        print(pulse_names[n])
        xf=(x1+np.sum(x2[n])) if x2[n]!=0 else x1    
        yf=(y1+np.sum(y2[n])) if y2[n]!=0 else y1    
        xi=x1 if n==0 else (x1+np.sum(x2[n-1]))
        yi=y1 if n==0 else (y1+np.sum(y2[n-1]))
        if x2[n]==0 and y2[n]==0:
            ax.arrow(xi,yi,xf-xi,yf-yi,color='blue',width=0.0002,head_width=0.0005)
        else:
            ax.arrow(xi,yi,xf-xi,yf-yi,color=f'{color[n]}',width=0.0002,head_width=0.0005)      
        if x2[n]!=0 or y2[n]!=0:
            ax.plot(x1+COGx-x2[n],y1+COGy-y2[n],marker='o',markersize=10,color=f'{color[n]}',label=pulse_names[n]+f' {round(x2[n]*1000,2)},{round(y2[n]*1000,2)} mV')   
       
    ax.plot(x1+COGx,y1+COGy,marker='o',markersize=20,color='black',label='center of gravity')
#    ax.plot(x1,y1,marker='o',markersize=10,color='black',label='initial point')    
    ax.legend(fontsize='xx-large')
    ax.xaxis.label.set_size(20)
    ax.yaxis.label.set_size(20)
    ax.tick_params(labelsize=20)
    ax.axis('equal')
    #cbaxes[0].ax.label.set_size(20) #labelsize(20)
    cbaxes[0].ax.tick_params(labelsize=20)
    
    return None  # COGx,COGy

