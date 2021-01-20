import broadbean as bb
from pulsequantum.elem_from_plot import elem_from_lists
# setting up a simple step pulse
ramp = bb.PulseAtoms.ramp  # args: start, stop
bp1 = bb.BluePrint()  # Do-nothing initialisation
bp1.insertSegment(0, ramp, (11.7*1e-3, 11.7*1e-3), name='a', dur=3e-6)
bp1.insertSegment(1, ramp, (11.7*2*1e-3, 11.7*2*1e-3), name='b', dur=3e-6)
bp1.setSR(1e9)
bp2 = bb.BluePrint()  # Do-nothing initialisation
bp2.insertSegment(0, ramp, (11.7*2*1e-3, 11.7*2*1e-3), name='a', dur=3e-6)
bp2.insertSegment(1, ramp, (11.7*1e-3, 11.7*1e-3), name='b', dur=3e-6)
bp2.setSR(1e9)
elemstep = bb.Element()
elemstep.addBluePrint(1, bp1)
elemstep.addBluePrint(2, bp2)


dividers = [11.7,11.7,11.7,11.7]
a=[1e-3,2e-3]
ad = [v/dividers[0] for v in a]
b=[2e-3,1e-3]
bd = [v/dividers[1] for v in b]
duration=3e-6
ramplist = [0, 0]

def test_elem_from_lists(testelem=elemstep,
                         step_list_a=a,
                         step_list_b=b,
                         ramplist=ramplist, 
                         duration=duration,
                         dac_a=0,
                         dac_b=0,
                         divider_a=dividers[0],
                         divider_b=dividers[1],
                         SR=1e9,
                         chx=1,
                         chy=2):
   
    elem = elem_from_lists(step_list_a,step_list_b,ramplist,duration,dac_a,dac_b,divider_a,divider_b,SR,chx,chy)
    assert elem.description == testelem.description
