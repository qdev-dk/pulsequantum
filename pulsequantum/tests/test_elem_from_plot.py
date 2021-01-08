# setting up a simple step pulse
ramp = bb.PulseAtoms.ramp  # args: start, stop
bp1 = bb.BluePrint()  # Do-nothing initialisation
bp1.insertSegment(0, ramp, (11.7*1e-3, 11.7*1e-3), name='', dur=3e-6)
bp1.insertSegment(1, ramp, (11.7*2*1e-3, 11.7*2*1e-3), name='', dur=3e-6)
bp1.setSR(1e9)
bp2 = bb.BluePrint()  # Do-nothing initialisation
bp2.insertSegment(0, ramp, (11.7*2*1e-3, 11.7*2*1e-3), name='', dur=3e-6)
bp2.insertSegment(1, ramp, (11.7*1e-3, 11.7*1e-3), name='', dur=3e-6)
bp2.setSR(1e9)
elemstep = bb.Element()
elemstep.addBluePrint(1, bp1)
elemestep.addBluePrint(2, bp2)

def test_elem_from_lists(testelem,step_list_a,step_list_b,duration,dac_a,dac_b,divider_a=1.0,divider_b=1.0,SR=1e9,chx=1,chy=2):
   
    elem = elem_from_lists(step_list_a,step_list_b,duration,dac_a,dac_b,divider_a=1.0,divider_b=1.0,SR=1e9,chx=1,chy=2)
    assert elem == testelem
