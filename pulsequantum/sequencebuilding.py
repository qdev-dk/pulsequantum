import broadbean as bb
import time
import numpy as np
from pulsequantum.awg import AWG
class Gseq(AWG):
    """
    Class for sequencing 
    """

    def __init__(self, AWG, gelem):
        super().__init__()
        self.AWG = AWG
        self.gelem = gelem
        self.gseq = bb.Sequence()


    def loadSequence(self, pathseq):
        """
        Loads af sequence from as json file
        """
        self.gseq = bb.Sequence.init_from_json(pathseq)
    
    def changedSeqTable(self, seqtable):
        """
         Updates gseg from seqtable
        """
        if self.gseq.points == 0:
            return
        for i in range(seqtable.rowCount()):
            seqlist = []
            for j in range(4):
                seqlist.append(int(seqtable.item(i, j).text()))
            self.updategseq(i, seqlist)   
            
    def updategseq(self, row, seqlist):
        """
        Updates the repetition pattern of the sequence  
        """
        self.gseq.setSequencingTriggerWait(row+1, seqlist[0])
        self.gseq.setSequencingNumberOfRepetitions(row+1, seqlist[1])
        self.gseq.setSequencingEventJumpTarget(row+1, seqlist[2])
        self.gseq.setSequencingGoto(row+1, seqlist[3])
    
    def buildSequenceWrap(self, chbox, offbox, contseqbox, timevoltbox, whichpulse, sparambox, seqstart, seqstop, seqpts):
        """
        Build gseq from gelem
        """
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
           # for chan in self.gseq.channels:
            #    self.gseq.setChannelAmplitude(chan, (float(chbox[chan-1].text())))
            #    self.gseq.setChannelOffset(chan, (float(offbox[chan-1].text())))
            #return
        elif sparam!="-Special-":
            self.buildsequencetable(self.gelem, sparam, sstart, sstop, spts)
        else:
            self.buildsequencetable(self.gelem, newparam, sstart, sstop, spts)
          
        for chan in self.gseq.channels:
            self.gseq.setChannelAmplitude(chan,(float(chbox[chan-1].text())))
            self.gseq.setChannelOffset(chan,(float(offbox[chan-1].text())))  


    def filterCorrection(self,hfiltbox,lfiltbox):
        if self.gseq.points == 0:
            print("No sequence defined")
            return
        hptau = (float(hfiltbox.text()))*1e-6
        for i in range(4):
            self.gseq.setChannelFilterCompensation(i+1,'HP',order=1,tau=hptau)

    def buildsequencetable(self,param,start,stop,points):
        self.gseq.setSR(self.gelem.SR);
        value=np.linspace(start,stop,points);
        #if first letter is "N"
        #if second word is time
        #setpulseduration
        #if second word is volt
        #setpulselevel
        for n in range(points):
            self.setpulseparameter(param,value[n]); # tjek 
            self.correctionDelem() # tjek
            self.gseq.addElement(n+1, self.gelem)
            self.gseq.setSequencingTriggerWait(n+1, 0)
            self.gseq.setSequencingNumberOfRepetitions(n+1, 1)
            self.gseq.setSequencingEventJumpTarget(n+1, 0)
            self.gseq.setSequencingGoto(n+1, 0)
              
               


# not sure were functions below belong 
#############################################################################################
###################            SET PULSE PARAMETER          #################################
#############################################################################################

    def setpulseparameter(self,param,value):
        #Define your own parameters here! For setting a segment name use setpulse()
        ch=0;
        if param[0]=='N':
            ch=int(param[7]);
            seg=param[9:len(param)];
            if param[2:6]=="Time":
                self.setpulseduration(ch,seg,value);
            else:
                self.setpulselevel(ch,seg,value);
        if param=='det':
            self.setpulselevel(1,'separate',value*0.8552);#For 20-11
            self.setpulselevel(2,'separate',-value*0.5183);#For 20-11
            #self.setpulselevel(1,'separate',value*0.9558);#For 40-31
            #self.setpulselevel(2,'separate',-value*0.2940);#For 40-31
            
        if param=='psm':
            self.setpulselevel(1,'detuning',value*0.8);
            self.setpulselevel(2,'detuning',-value*0.5);
    ##detuning load        
    #    if param=='psm_load':
    #        alpha_x = -0.6597
    #        beta_y = 0.7516
    #        self.setpulselevel(1,'detuning_up',value*(1)*alpha_x); #BNC43
    #        self.setpulselevel(2,'detuning_up',value*(1)*beta_y); #BNC17
    #        self.setpulselevel(1,'detuning_up_b',value*(1)*alpha_x); #BNC43
    #        self.setpulselevel(2,'detuning_up_b',value*(1)*beta_y); #BNC17

        if param=='dephasing_corrD':
            corrD_K0 = -1.8102
            corrD_K1 = 0.44531
            corrD_K2 = 0.0004064
            corrD_K3 = -1.0403e-7
            
            corrD_X = corrD_K0 + corrD_K1*value + corrD_K2*value*value + corrD_K3*value*value*value
            corrD_y = corrD_K0 + corrD_K1*value + corrD_K2*value*value + corrD_K3*value*value*value

            #corr amplitudes for 2ms separation
            # corrD_amp_BNC12 = -7.3569
            # corrD_amp_BNC17 = 3.07129
            self.setpulseduration(1,'corrD', corrD_X)
            self.setpulseduration(2,'corrD', corrD_Y)
            self.setpulseduration(1,'Separate',value)
            self.setpulseduration(2,'Separate',value)



    #detuning load        
        if param=='psm_load':
            alpha_x = -0.621
            beta_y = 0.7838
            self.setpulselevel(1,'detuning_up',value*(1)*alpha_x); #BNC43
            self.setpulselevel(2,'detuning_up',value*(1)*beta_y); #BNC17
            self.setpulselevel(1,'detuning_up_b',value*(1)*alpha_x); #BNC43
            self.setpulselevel(2,'detuning_up_b',value*(1)*beta_y); #BNC17

    #detuning load symmetric       
        if param=='psm_load_sym':
            alpha_x = 0.974
            beta_y = -0.226
            self.setpulselevel(1,'detuning_up',value*(0.5)*alpha_x); #BNC12
            self.setpulselevel(2,'detuning_up',value*(0.5)*beta_y); #BNC17
            self.setpulselevel(1,'detuning_up_b',value*(0.5)*alpha_x); #BNC12
            self.setpulselevel(2,'detuning_up_b',value*(0.5)*beta_y); #BNC17
            self.setpulselevel(1,'down',value*(-0.5)*alpha_x); #BNC12
            self.setpulselevel(2,'down',value*(-0.5)*beta_y); #BNC17
            self.setpulselevel(1,'down_b',value*(-0.5)*alpha_x); #BNC12
            self.setpulselevel(2,'down_b',value*(-0.5)*beta_y); #BNC17        
            
            


    #detuning unload symmetric       
        if param=='psm_unload_sym':
            alpha_x = 0.4832
            beta_y = -0.8755
            self.setpulselevel(1,'detuning_up',value*(0.5)*alpha_x); #BNC43
            self.setpulselevel(2,'detuning_up',value*(0.5)*beta_y); #BNC17
            self.setpulselevel(1,'detuning_up_b',value*(0.5)*alpha_x); #BNC43
            self.setpulselevel(2,'detuning_up_b',value*(0.5)*beta_y); #BNC17
            self.setpulselevel(1,'down',value*(-0.5)*alpha_x); #BNC43
            self.setpulselevel(2,'down',value*(-0.5)*beta_y); #BNC17
            self.setpulselevel(1,'down_b',value*(-0.5)*alpha_x); #BNC43
            self.setpulselevel(2,'down_b',value*(-0.5)*beta_y); #BNC17     
            
            
            
                    
    #detuning unload        
        if param=='psm_unload':
            alpha_x = 0.6761
            beta_y = -0.7368
            self.setpulselevel(1,'detuning_up',value*(1)*alpha_x); #BNC43
            self.setpulselevel(2,'detuning_up',value*(1)*beta_y); #BNC17
            self.setpulselevel(1,'detuning_up_b',value*(1)*alpha_x); #BNC43
            self.setpulselevel(2,'detuning_up_b',value*(1)*beta_y); #BNC17
                    

                


    #############################################################################################
    ###################    CHANGE PULSE LEVEL OR DURATION       #################################
    #############################################################################################
    def setpulselevel(self,ch,seg,lvl,div=11.7):
        #Change a pulse within an element
        lvl=lvl*self.divider_ch[ch-1]*1e-3;
    #    print(lvl);
        self.gelem.changeArg(ch,seg,0,lvl,False);
        self.gelem.changeArg(ch,seg,1,lvl,False);

    def setpulseduration(ch,seg,dur):
        dur=dur*1e-6;
        ch=self.gelem.channels;
        for i in range(len(ch)):
            gelem.changeDuration(ch[i],seg,dur,False);

    #############################################################################################
    ###################            correctionD Pulse            #################################
    #############################################################################################
    def correctionDelem(self):
        awgclock = self.gelem.SR
        global corrDflag;
        
        
        #If no correctionD pulse exists print error and just return
        if(corrDflag==0):
            return
        #Set up variables
        start=[];
        stop=[];
        ramp=[];
        name=[];
        seg_dur=[];
        tottime=0;
        awgclockinus=awgclock/1e6;
        
        
        #Number of pulses in element
        num=len(self.gelem.description['{}'.format(self.gelem.channels[0])])-4
        chs=len(self.gelem.channels)
        #Get all pulses in element
        for j in range(chs):
            #Reinitialise pulses and total time
            start=[];stop=[];ramp=[];name=[];seg_dur=[];
            tottime=0;
            tottimevolt=0;
            timeD=0;voltD=0;
            #Get all pulses for that channel
            for i in range(num):
                pulsestart=1e3*(self.gelem.description['{}'.format(j+1)]['segment_%02d'%(i+1)]['arguments']['start'])/self.divider_ch[j+1]
                pulsestop=1e3*(self.gelem.description['{}'.format(j+1)]['segment_%02d'%(i+1)]['arguments']['stop'])/self.divider_ch[j+1] #Need correct channel dividers!
                start.append(pulsestart)
                stop.append(pulsestop)
                if(pulsestart==pulsestop):
                    ramp.append(0);
                else:
                    ramp.append(1);
                pulsedur=1e6*self.gelem.description['{}'.format(j+1)]['segment_%02d'%(i+1)]['durations']
                seg_dur.append(pulsedur)
                pulsename=self.gelem.description['{}'.format(j+1)]['segment_%02d'%(i+1)]['name']
                name.append(pulsename)
                #Add duration to total time
                if pulsename!='corrD':
                    tottime=tottime+pulsedur; #In us  
            #Calculate correctionD time, 65% of the total pulse cycle time
            timeD=round(tottime/1.65*(awgclockinus))/awgclockinus;
            self.setpulseduration(j+1,'corrD',timeD);
            #Calculate tottimevolt
            for i in range(num):
                if name[i]!='corrD':
                    if(ramp[i]==0):
                        tottimevolt=tottimevolt+(start[i]*seg_dur[i]); #If not ramp take start or stop
                    if(ramp[i]==1):
                        tottimevolt=tottimevolt+(((start[i]+stop[i])/2)*seg_dur[i]); #If ramp take midpoint of start and stop
            #Calculate correctionD for that channel
            voltD=-tottimevolt/timeD;
            #Change level of correctionD pulse
            setpulselevel(self.gelem,j+1,'corrD',voltD)            