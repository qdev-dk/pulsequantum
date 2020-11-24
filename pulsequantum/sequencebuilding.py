import broadbean as bb
class Gseg():
    """
    Class for sequencing 
    """

    def __init__(self, AWG=None, gelem=None):
        self.AWG = AWG
        self.gelem = gelem
        self.gseq = bb.Sequence()

    def loadSequence(self, pathseq):
        self.gseq = bb.Sequence.init_from_json(pathseq)
    
    def changedSeqTable(self, seqtable): # make seqtable a normal array
        if self.gseq.points == 0:
            return
        for i in range(seqtable.rowCount()):
            seqlist = []
            for j in range(4):
                seqlist.append(int(seqtable.item(i, j).text()))
            self.updategseq(i, seqlist)   
            
    def updategseq(self, row, seqlist):
        self.gseq.setSequencingTriggerWait(row+1, seqlist[0])
        self.gseq.setSequencingNumberOfRepetitions(row+1, seqlist[1])
        self.gseq.setSequencingEventJumpTarget(row+1, seqlist[2])
        self.gseq.setSequencingGoto(row+1, seqlist[3])
    
    def buildSequenceWrap(self, chbox, offbox, contseqbox, timevoltbox, whichpulse, sparambox, seqstart, seqstop, seqpts):
        self.gseq= bb.Sequence()
        timevolt=str(timevoltbox.currentText())
        whichp=str(whichpulse.text())
        sparam=str(sparambox.currentText())
        sstart=float(seqstart.text())
        sstop=float(seqstop.text())
        spts=int(seqpts.text())
        if timevolt=="Time":
            newparam="N-"+timevolt+"-0-"+whichp
        else:
            newparam="N-"+"Volt"+"-"+timevolt[2]+"-"+whichp
        self.gseq.setSR(self.gelem.SR)

        if contseqbox.isChecked():
            self.gseq.addElement(1, self.gelem)
            self.gseq.setSequencingTriggerWait(1, 0)
            self.gseq.setSequencingNumberOfRepetitions(1, 0)
            self.gseq.setSequencingEventJumpTarget(1, 0)
            self.gseq.setSequencingGoto(1, 0)
            for chan in self.gseq.channels:
                self.gseq.setChannelAmplitude(chan, (float(chbox[chan-1].text())))
                self.gseq.setChannelOffset(chan, (float(offbox[chan-1].text())))
            return
        elif sparam!="-Special-":
            buildsequencetable(self.gelem, sparam, sstart, sstop, spts)
        else:
            buildsequencetable(self.gelem, newparam, sstart, sstop, spts)
          
        for chan in self.gseq.channels:
            self.gseq.setChannelAmplitude(chan,(float(chbox[chan-1].text())))
            self.gseq.setChannelOffset(chan,(float(offbox[chan-1].text())))  


    def filterCorrection(self,hfiltbox,lfiltbox):
        if self.gseq.points==0:
            print("No sequence defined")
            return
        hptau=(float(hfiltbox.text()))*1e-6
        for i in range(4):
            self.gseq.setChannelFilterCompensation(i+1,'HP',order=1,tau=hptau)

    def buildsequencetable(elem,param,start,stop,points):
        self.gseq.setSR(elem.SR);
        value=np.linspace(start,stop,points);
        #if first letter is "N"
        #if second word is time
        #setpulseduration
        #if second word is volt
        #setpulselevel
        for n in range(points):
            setpulseparameter(elem,param,value[n]);
            correctionDelem(elem);
            self.gseq.addElement(n+1, elem);
            self.gseq.setSequenceSettings(n+1,0,1,0,0);
            # Arguments are position, wait for trigger (0 means OFF), number of repetitions 
            #(0 is infinite, 1 is one), jump target (0 is off), goto (0 means next)
        self.gseq.setSequenceSettings(n+1,0,1,0,1);                
               
#############################################################################################
# AWG functions (uploading, running AWG, turning on outputs. Note that in this section 
# the AWG name is hardcoded. Probably first thing that needs to be changed.
#############################################################################################
    def uploadToAWG(self,Choose_awg,chbox):
        if Choose_awg.currentText() == 'AWG5014':
            #for i,  chan in enumerate(self.gseq.channels):
            #    self.AWG.channels[chan].AMP(float(chbox[chan-1].text()))
            self.AWG.ch1_amp(float(chbox[0].text()))
            self.AWG.ch2_amp(float(chbox[1].text()))
            self.AWG.ch3_amp(float(chbox[2].text()))
            self.AWG.ch4_amp(float(chbox[3].text()))
            package = self.gseq.outputForAWGFile()
            start_time=time.time();
            self.AWG.make_send_and_load_awg_file(*package[:])
            print("Sequence uploaded in %s seconds" %(time.time()-start_time));
        if Choose_awg.currentText() == 'AWG5208':
            self.gseq.name = 'sequence_from_gui'
            self.AWG.mode('AWG')
            for chan in self.gseq.channels:
                self.AWG.channels[chan-1].resolution(12)
                self.AWG.channels[chan-1].awg_amplitude(0.5)
                self.gseq.setChannelAmplitude(chan, self.AWG.channels[chan-1].awg_amplitude())
            self.AWG.clearSequenceList()
            self.AWG.clearWaveformList()
            self.AWG.sample_rate(self.gseq.SR)
            self.AWG.sample_rate(self.gseq.SR)
            print(Choose_awg.currentText() )
            
            seqx_input = self.gseq.outputForSEQXFile()
            start_time=time.time();
            seqx_output = self.AWG.makeSEQXFile(*seqx_input)
            # transfer it to the awg harddrive
            self.AWG.sendSEQXFile(seqx_output, 'sequence_from_gui.seqx')
            self.AWG.loadSEQXFile('sequence_from_gui.seqx')
            #time.sleep(1.300)
            for i,  chan in enumerate(self.gseq.channels):       
                self.AWG.channels[chan-1].setSequenceTrack('sequence_from_gui', i+1)
                self.AWG.channels[chan-1].state(1)
            print("Sequence uploaded in %s seconds" %(time.time()-start_time));
 
        else:
            print('Choose an AWG model')
  
        
    def runAWG(self,Choose_awg):
        if Choose_awg.currentText() == 'AWG5014':
            if self.AWG.get_state()=='Idle':
                self.AWG.run();
                print("AWGs Running");
            elif self.AWG.get_state()=='Running':
                self.AWG.stop();
                print("AWGs Stopped");
        else:
            if self.AWG.run_state() == 'Running':
                self.AWG.stop()
                print(self.AWG.run_state())
            elif self.AWG.run_state() == 'Waiting for trigger':
                print(self.AWG.run_state())
            else:  
                self.AWG.play()
                print(self.AWG.run_state())
            
            self.AWG.stop();


    def runChan(self,outputbox,whichbox):
        if whichbox==0:
            if outputbox.isChecked():
                self.AWG.ch1_state(1);
                self.AWG.ch2_state(1);
                self.AWG.ch3_state(1);
                self.AWG.ch4_state(1);
            else:
                self.AWG.ch1_state(0);
                self.AWG.ch2_state(0);
                self.AWG.ch3_state(0);
                self.AWG.ch4_state(0);
        if whichbox==1:
            if outputbox.isChecked():
                self.AWG.ch1_state(1);
            else:
                self.AWG.ch1_state(0);
        if whichbox==2:
            if outputbox.isChecked():
                self.AWG.ch2_state(1);
            else:
                self.AWG.ch2_state(0);
        if whichbox==3:
            if outputbox.isChecked():
                self.AWG.ch3_state(1);
            else:
                self.AWG.ch3_state(0);
        if whichbox==4:
            if outputbox.isChecked():
                self.AWG.ch4_state(1);
            else:
                self.AWG.ch4_state(0);