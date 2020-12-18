import time
class AWG():
    """
    Class for AWG control
    """

    def __init__(self, AWG = None, gseq = None):
        self.AWG = AWG
        self.gseq = gseq
#############################################################################################
# AWG functions (uploading, running AWG, turning on outputs. Note that in this section 
# the AWG name is hardcoded. Probably first thing that needs to be changed.
#############################################################################################
    def uploadToAWG(self,Choose_awg,chbox):
        if Choose_awg == 'AWG5014':
            #for i,  chan in enumerate(self.gseq.channels):
            #    self.AWG.channels[chan].AMP(float(chbox[chan-1].text()))
            self.AWG.ch1_amp(float(chbox[0].text()))
            self.AWG.ch2_amp(float(chbox[1].text()))
            self.AWG.ch3_amp(float(chbox[2].text()))
            self.AWG.ch4_amp(float(chbox[3].text()))
            package = self.gseq.outputForAWGFile()
            start_time=time.time()
            self.AWG.make_send_and_load_awg_file(*package[:])
            print("Sequence uploaded in %s seconds" %(time.time()-start_time));
        elif Choose_awg == 'AWG5208':
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
            
            seqx_input = self.gseq.outputForSEQXFile()
            start_time=time.time()
            seqx_output = self.AWG.makeSEQXFile(*seqx_input)
            # transfer it to the awg harddrive
            self.AWG.sendSEQXFile(seqx_output, 'sequence_from_gui.seqx')
            self.AWG.loadSEQXFile('sequence_from_gui.seqx')
            #time.sleep(1.300)
            for i,  chan in enumerate(self.gseq.channels):       
                self.AWG.channels[chan-1].setSequenceTrack('sequence_from_gui', i+1)
                self.AWG.channels[chan-1].state(1)
            print("Sequence uploaded in %s seconds" %(time.time()-start_time))
 
        else:
            print('Choose an AWG model')
  
        
    def runAWG(self,Choose_awg):
        if Choose_awg == 'AWG5014':
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
            


    def runChan(self,outputbox,whichbox, Choose_awg):
        if Choose_awg == 'AWG5014':
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
        else:
            if whichbox==0:
                if outputbox.isChecked():
                    self.AWG.ch1.state(1);
                    self.AWG.ch2.state(1);
                    self.AWG.ch3.state(1);
                    self.AWG.ch4.state(1);
                else:
                    self.AWG.ch1.state(0);
                    self.AWG.ch2.state(0);
                    self.AWG.ch3.state(0);
                    self.AWG.ch4.state(0);
            if whichbox==1:
                if outputbox.isChecked():
                    self.AWG.ch1.state(1);
                else:
                    self.AWG.ch1.state(0);
            if whichbox==2:
                if outputbox.isChecked():
                    self.AWG.ch2.state(1);
                else:
                    self.AWG.ch2.state(0);
            if whichbox==3:
                if outputbox.isChecked():
                    self.AWG.ch3.state(1);
                else:
                    self.AWG.ch3.state(0);
            if whichbox==4:
                if outputbox.isChecked():
                    self.AWG.ch4.state(1);
                else:
                    self.AWG.ch4.state(0);
