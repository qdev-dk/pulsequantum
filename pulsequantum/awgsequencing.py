#todo: 
#- fix sampling rate to match clock speed when changed

# import and initialise the driver and ensure that the sample
# rate and channel voltage is correct


import numpy as np
import matplotlib
import time
import pickle 
import broadbean as bb
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QMainWindow, QPushButton, QAction, QMessageBox, QLineEdit, QLabel, QSizePolicy
from PyQt5.QtWidgets import QCheckBox, QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QComboBox, QGridLayout
from broadbean.plotting import plotter
matplotlib.use('QT5Agg')

#############################################################################################
#Hardcoded stuff, should incorporate into main code
#############################################################################################


gseq = bb.Sequence()

divch1=11.5;divch2=11.75;divch3=11.7;divch4=1; #Hardcoded channel dividers
divch=[divch1,divch2,divch3,divch4];

awgclock=1.2e9;
corrDflag=0; #Global flag: Is correction D pulse already defined in the pulse table?

#Any new parameter defined for the "Special" sequencing tab needs to go here in order to appear in the dropdown menu
params=["det","psm_load","psm_unload","psm_load_sym","psm_unload_sym","dephasing_corrD"]
 


class Sequencing(QDialog):
    """
    Class for sequencing (secondary) window
    """

    def __init__(self,AWG = None, gelem = None):
        #super(sequencing, self).__init__()
        super().__init__()
        self.setGeometry(200, 200, 900, 500)
        self.setWindowTitle("Sequencing")
        self.setMinimumWidth(350)
        self.home()
        self.AWG = AWG
        self.gelem = gelem

    def home(self):
        
        
        # Create channel voltage, divider and offset boxes and buttons
        win4 = QWidget(self);
        lay4= QGridLayout(win4);
        vpp = QLabel(self);
        vpp.setText('Vpp');
        offset= QLabel(self);
        offset.setText('Offset');
        lay4.addWidget(vpp,0,1,1,1);
        lay4.addWidget(offset,0,2,1,1);
        number_channels = 4
        chlabel = list(range(number_channels))
        chbox = list(range(number_channels))
        offbox = list(range(number_channels))
        for i in range(4):
            chlabel[i] = QLabel(self)
            chlabel[i].setText('Ch%d'%(i+1))
            chbox[i] = QLineEdit(self)
            chbox[i].setText('4.5')
            offbox[i] = QLineEdit(self)
            offbox[i].setText('0')
            lay4.addWidget(chlabel[i],i+1,0,1,1)
            lay4.addWidget(chbox[i],i+1,1,1,1)
            lay4.addWidget(offbox[i],i+1,2,1,1)
        win4.move(10,100);
        
        #Continuous sequence?
        contseqboxlabel= QLabel(self);
        contseqboxlabel.setText('Simple continuous element?');
        contseqboxlabel.move(20, 280);
        contseqboxlabel.resize(contseqboxlabel.sizeHint())
        contseqbox = QCheckBox(self);
        contseqbox.move(200, 280);
        
        #Upload to AWG
        #Function
        uploadbtn = QPushButton('Upload To AWG', self);
        uploadbtn.clicked.connect(lambda state: self.uploadToAWG(Choose_awg,chbox))
        
        #Choose awg
        Choose_awg = QComboBox(self)
        Choose_awg.addItem('AWG5014')
        Choose_awg.addItem('AWG5208')

        #Update sequencing parameters: table and update button
        win2 = QWidget(self);
        lay2= QVBoxLayout(win2);
        seqtable=QTableWidget(4,4,self)
        seqtable.setColumnCount(4);
        #Set top headers
        hlist=["TrigWait", "NumReps", "JumpTarget","Goto"];
        for i in range(4):
            seqtable.setColumnWidth(i,70);
            seqtable.setHorizontalHeaderItem(i, QTableWidgetItem(hlist[i]));
        seqtable.setRowCount(0);
        updateseqbtn = QPushButton('Update sequence', self)
        updateseqbtn.clicked.connect(lambda state:self.changedSeqTable(seqtable))
        updateseqbtn.resize(updateseqbtn.sizeHint())
        lay2.addWidget(seqtable);
        lay2.addWidget(updateseqbtn);
        win2.move(450,30);win2.resize(win2.sizeHint());
        
        #Update sequencing parameters: do this?
        changeseqbox = QCheckBox(self);changeseqbox.move(630,10);
        changeseqbox.stateChanged.connect(lambda state: self.seqchangeWidget(changeseqbox,win2,seqtable,seqpts))
        changeseqboxlabel= QLabel(self);changeseqboxlabel.setText('Change sequencing options?');changeseqboxlabel.move(450,10);changeseqboxlabel.resize(changeseqboxlabel.sizeHint())
        
        
        #Build Sequence and take parameters
        win3 = QWidget(self);
        lay3= QGridLayout(win3);
        buildseqlabel= QLabel(self);buildseqlabel.setText('Select a parameter to build the sequence:');
        buildseqlabel.resize(buildseqlabel.sizeHint())
        buildseqbtn = QPushButton('Build sequence', self)
        buildseqbtn.clicked.connect(lambda state:self.buildSequenceWrap(chbox,offbox,contseqbox,timevoltbox,whichpulse,sparambox,seqstart,seqstop,seqpts))
        buildseqbtn.resize(buildseqbtn.sizeHint())
        buildseqbtn.move(350, 100)
        
        #Native and special parameters
        timevoltbox=QComboBox(self);
        timevoltbox.addItem("Time");
        timevoltbox.addItem("Ch1 Voltage");
        timevoltbox.addItem("Ch2 Voltage");
        timevoltbox.addItem("Ch3 Voltage");
        timevoltbox.addItem("Ch4 Voltage");
        whichpulse=QLineEdit(self);
        whichpulse.setText('Which pulse?');
        whichpulse.resize(whichpulse.sizeHint());
        sparambox=QComboBox(self);
        sparambox.addItem("-Special-")
        for i in range(len(params)):
            sparambox.addItem(params[i]);
        #Start/stop and build
        lay32= QHBoxLayout();
        lay32.addStretch();
        startslabel= QLabel(self);
        startslabel.setText('Start:');
        stopslabel= QLabel(self);
        stopslabel.setText('Stop:');
        pointsslabel= QLabel(self);
        pointsslabel.setText('Points:');
        seqstart=QLineEdit(self);
        seqstart.setText('0');
        seqstart.resize(seqstart.sizeHint());
        seqstop=QLineEdit(self);seqstop.setText('0');seqstop.resize(seqstop.sizeHint());
        seqpts=QLineEdit(self);seqpts.setText('0');seqpts.resize(seqpts.sizeHint());
        
        lay3.addWidget(buildseqlabel,0,0,1,3);
        lay3.addWidget(timevoltbox,1,0,1,1);lay3.addWidget(whichpulse,1,1,1,1);lay3.addWidget(sparambox,1,2,1,1);
        lay3.addWidget(startslabel,2,0,1,1);lay3.addWidget(stopslabel,2,1,1,1);lay3.addWidget(pointsslabel,2,2,1,1);
        lay3.addWidget(seqstart,3,0,1,1);lay3.addWidget(seqstop,3,1,1,1);lay3.addWidget(seqpts,3,2,1,1);
        lay3.addWidget(buildseqbtn,4,0,1,3);
        lay3.addWidget(uploadbtn,5,0,1,3);
        lay3.addWidget(Choose_awg,6,0,1,2);
        Choose_awg 
        win3.move(10,300);
        win3.resize(win3.sizeHint());
        
        
        #Element and sequence saving and loading
        #Functions
        win1 = QWidget(self);
        lay1= QGridLayout(win1);
        loadebtn = QPushButton('Load Element', self);
        #loadebtn.clicked.connect(lambda state:self.sloadElement())
        saveebtn = QPushButton('Save Element', self);
        #saveebtn.clicked.connect(lambda state: self.ssaveElement())
        plotebtn = QPushButton('Plot Element', self);
        plotebtn.clicked.connect(lambda state: self.splotElement())
        # load sequence
        whichSeq = QLineEdit(self)
        whichSeq.setText('enter file name')
        #whichSeq.setGeometry(110,60,70,20)
        loadsbtn = QPushButton('Load Sequence', self)
        loadsbtn.clicked.connect(lambda state:self.loadSequence(whichSeq.text()))
        # save sequence
        SeqTo = QLineEdit(self)
        SeqTo.setText('enter file name')
       #SeqTo.setGeometry(20,60,70,20)
        savesbtn = QPushButton('Save Sequence', self)
        savesbtn.clicked.connect(lambda state: self.saveSequence(SeqTo.text()))
        # plot sequence
        plotsbtn = QPushButton('Plot Sequence', self);
        plotsbtn.clicked.connect(lambda state: self.splotSequence())
        lay1.addWidget(loadebtn,0,0,1,1);
        lay1.addWidget(saveebtn,0,1,1,1);
        lay1.addWidget(plotebtn,0,2,1,1);
        lay1.addWidget(savesbtn,1,0,1,1);
        lay1.addWidget(loadsbtn,1,1,1,1);
        lay1.addWidget(plotsbtn,1,2,1,1);
        lay1.addWidget(SeqTo,2,0,1,1);
        lay1.addWidget(whichSeq,2,1,1,1);
        win1.move(10,0);
        win1.resize(win1.sizeHint());
        
        #AWG Panel stuff
        # Create channel voltage, divider and offset boxes and buttons
        #Divider linked to base GUI!!
        win5 = QWidget(self);
        lay5= QGridLayout(win5);
        awgframeh=QFrame(self);
        awgframeh.setFrameShape(QFrame.Shape(0x0004));
        awgframeh2=QFrame(self);
        awgframeh2.setFrameShape(QFrame.Shape(0x0004));
        awgframev=QFrame(self);
        awgframev.setFrameShape(QFrame.Shape(0x0005));
        lay5.addWidget(awgframeh,0,0,1,6);
        lay5.addWidget(awgframev,0,0,7,1);
        awglabel= QLabel(self);
        awglabel.setText('AWG Tools:');
        allonlabel= QLabel(self);allonlabel.setText('All on:');
        allonbox = QCheckBox(self);
        allonbox.stateChanged.connect(lambda state: self.runChan(allonbox, 0));
        achlabel1='Ch1';
        achlabel2='Ch2';
        achlabel3='Ch3';
        achlabel4='Ch4';
        achlabel=[achlabel1,achlabel2,achlabel3,achlabel4];
        for i in range(len(achlabel)):
            achlabel[i]= QLabel(self);achlabel[i].setText('Ch%d'%(i+1));
        avpp= QLabel(self);avpp.setText('Vpp');
        aoffset= QLabel(self);aoffset.setText('Offset');
        aoutput= QLabel(self);aoutput.setText('Output');
        achbox1 = QLineEdit(self);achbox2 = QLineEdit(self);achbox3 = QLineEdit(self);achbox4 = QLineEdit(self);
        achbox=[achbox1,achbox2,achbox3,achbox4];
        aoffbox1 = QLineEdit(self);aoffbox2 = QLineEdit(self);aoffbox3 = QLineEdit(self);aoffbox4 = QLineEdit(self);
        aoffbox=[aoffbox1,aoffbox2,aoffbox3,aoffbox4];
        aoutbox1 = QCheckBox(self);aoutbox2 = QCheckBox(self);aoutbox3 = QCheckBox(self);aoutbox4 = QCheckBox(self);
        aoutbox=[aoutbox1,aoutbox2,aoutbox3,aoutbox4];
        aoutbox1.stateChanged.connect(lambda state: self.runChan(aoutbox1, 1));
        aoutbox2.stateChanged.connect(lambda state: self.runChan(aoutbox2, 2));
        aoutbox3.stateChanged.connect(lambda state: self.runChan(aoutbox3, 3));
        aoutbox4.stateChanged.connect(lambda state: self.runChan(aoutbox4, 4));
        runAWGtn = QPushButton('Run AWG', self);
        runAWGtn.clicked.connect(lambda state: self.runAWG(Choose_awg))
        lay5.addWidget(awglabel,1,1,1,1);
        lay5.addWidget(runAWGtn,1,2,1,1);
        for i in range(len(achbox)):
            achbox[i].setText('4.5');aoffbox[i].setText('0');
            lay5.addWidget(achbox[i],i+3,2,1,1);lay5.addWidget(achlabel[i],i+3,1,1,1);
            lay5.addWidget(aoffbox[i],i+3,3,1,1);lay5.addWidget(aoutbox[i],i+3,4,1,1);
        lay5.addWidget(avpp,2,2,1,1);lay5.addWidget(aoffset,2,3,1,1);lay5.addWidget(aoutput,2,4,1,1);
        lay5.addWidget(allonlabel,1,3,1,1);lay5.addWidget(allonbox,1,4,1,1);
        win5.resize(win5.sizeHint())
        win5.move(450,270);

        
        #Filter Correction
        filtbtn = QPushButton('Filter correction', self)
        hfiltboxlabel= QLabel(self);hfiltboxlabel.setText('High pass (us):');hfiltboxlabel.resize(hfiltboxlabel.sizeHint());hfiltboxlabel.move(20,235);
        lfiltboxlabel= QLabel(self);lfiltboxlabel.setText('Low pass (us):');lfiltboxlabel.resize(lfiltboxlabel.sizeHint());lfiltboxlabel.move(170,235);
        hfiltbox = QLineEdit(self);hfiltbox.setText('80');hfiltbox.resize(hfiltbox.sizeHint());hfiltbox.move(20,250);
        lfiltbox = QLineEdit(self);lfiltbox.setText('-');lfiltbox.resize(lfiltbox.sizeHint());lfiltbox.move(170,250);
        filtbtn.clicked.connect(lambda state: self.filterCorrection(hfiltbox,lfiltbox))
        filtbtn.resize(filtbtn.sizeHint())
        filtbtn.move(320, 250)
        
        
        self.show()
        win2.hide()

    def splotElement(self):
        plotter(self.gelem);
    
    def splotSequence(self):
        plotter(gseq);
        
    def loadSequence(self,pathseq):
        global gseq;
        gseq = bb.Sequence.init_from_json(pathseq)
        #table.setItem(0,2, QTableWidgetItem("-12.8")
        #return
    
    def saveSequence(self,pathseq):
        gseq.write_to_json(pathseq)
   
    def seqchangeWidget(self,changeseqbox,win2,seqtable,seqpts):
        if changeseqbox.isChecked():
            self.updateSeqTable(seqtable,int(seqpts.text()));
            win2.show();
        else:
            win2.hide();
    
    def updateSeqTable(self,seqtable,seqpts):
        if gseq.points==0:
            return
        elif seqpts==0:
            seqtable.setRowCount(1);
            seqtable.setItem(0,0,QTableWidgetItem("0"));
            seqtable.setItem(0,1,QTableWidgetItem("1"));
            seqtable.setItem(0,2,QTableWidgetItem("0"));
            seqtable.setItem(0,3,QTableWidgetItem("0"));
        else:
            seqtable.setRowCount(seqpts);
            for i in range(seqpts):
                seqtable.setItem(i,0,QTableWidgetItem("0"));
                seqtable.setItem(i,1,QTableWidgetItem("1"));
                seqtable.setItem(i,2,QTableWidgetItem("0"));
                seqtable.setItem(i,3,QTableWidgetItem("0"));
            seqtable.setItem(i,3,QTableWidgetItem("1"));
    
    def changedSeqTable(self,seqtable):
        if gseq.points==0:
            return 
        seqlist=[];
        deflist=[0,1,0,0];
        for i in range(seqtable.rowCount()):
            seqlist=[];
            for j in range(4):
                seqlist.append(int(seqtable.item(i,j).text()));
            self.updategseq(i,seqlist);    
            
    def updategseq(self,row,seqlist):
        #gseq.setSequenceSettings(row+1,seqlist[0],seqlist[1],seqlist[2],seqlist[3]);
        gseq.setSequencingTriggerWait(row+1,seqlist[0])
        gseq.setSequencingNumberOfRepetitions(row+1,seqlist[1])
        gseq.setSequencingEventJumpTarget(row+1,seqlist[2])
        gseq.setSequencingGoto(row+1,seqlist[3])
    
    def buildSequenceWrap(self,chbox,offbox,contseqbox,timevoltbox,whichpulse,sparambox,seqstart,seqstop,seqpts):
        global gseq;
        gseq= bb.Sequence();
        timevolt=str(timevoltbox.currentText());
        whichp=str(whichpulse.text());
        sparam=str(sparambox.currentText());
        sstart=float(seqstart.text());
        sstop=float(seqstop.text());
        spts=int(seqpts.text());
        if timevolt=="Time":
            newparam="N-"+timevolt+"-0-"+whichp;
        else:
            newparam="N-"+"Volt"+"-"+timevolt[2]+"-"+whichp;
        gseq.setSR(self.gelem.SR);

        if contseqbox.isChecked():
            gseq.addElement(1,self.gelem);
            gseq.setSequencingTriggerWait(1,0)
            gseq.setSequencingNumberOfRepetitions(1,0)
            gseq.setSequencingEventJumpTarget(1,0)
            gseq.setSequenceSettings(1,0,0,0,0);
            for chan in gseq.channels:
                gseq.setChannelAmplitude(chan,(float(chbox[chan-1].text())));
                gseq.setChannelOffset(chan,(float(offbox[chan-1].text())));  
            return;
        elif sparam!="-Special-":
            buildsequencetable(self.gelem,sparam,sstart,sstop,spts);
        else:
            buildsequencetable(self.gelem,newparam,sstart,sstop,spts);
          
        for chan in gseq.channels:
            gseq.setChannelAmplitude(chan,(float(chbox[chan-1].text())));
            gseq.setChannelOffset(chan,(float(offbox[chan-1].text())));  
               
#############################################################################################
# AWG functions (uploading, running AWG, turning on outputs. Note that in this section 
# the AWG name is hardcoded. Probably first thing that needs to be changed.
#############################################################################################
    def uploadToAWG(self,Choose_awg,chbox):
        if Choose_awg.currentText() == 'AWG5014':
            #for i,  chan in enumerate(gseq.channels):
            #    self.AWG.channels[chan].AMP(float(chbox[chan-1].text()))
            self.AWG.ch1_amp(float(chbox[0].text()))
            self.AWG.ch2_amp(float(chbox[1].text()))
            self.AWG.ch3_amp(float(chbox[2].text()))
            self.AWG.ch4_amp(float(chbox[3].text()))
            package = gseq.outputForAWGFile()
            start_time=time.time();
            self.AWG.make_send_and_load_awg_file(*package[:])
            print("Sequence uploaded in %s seconds" %(time.time()-start_time));
        if Choose_awg.currentText() == 'AWG5208':
            gseq.name = 'sequence_from_gui'
            self.AWG.mode('AWG')
            for chan in gseq.channels:
                self.AWG.channels[chan-1].resolution(12)
                self.AWG.channels[chan-1].awg_amplitude(0.5)
                gseq.setChannelAmplitude(chan, self.AWG.channels[chan-1].awg_amplitude())
            self.AWG.clearSequenceList()
            self.AWG.clearWaveformList()
            self.AWG.sample_rate(gseq.SR)
            self.AWG.sample_rate(gseq.SR)
            print(Choose_awg.currentText() )
            
            seqx_input = gseq.outputForSEQXFile()
            start_time=time.time();
            seqx_output = self.AWG.makeSEQXFile(*seqx_input)
            # transfer it to the awg harddrive
            self.AWG.sendSEQXFile(seqx_output, 'sequence_from_gui.seqx')
            self.AWG.loadSEQXFile('sequence_from_gui.seqx')
            #time.sleep(1.300)
            for i,  chan in enumerate(gseq.channels):       
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
    
    def filterCorrection(self,hfiltbox,lfiltbox):
        if gseq.points==0:
            print("No sequence defined");
            return
        hptau=(float(hfiltbox.text()))*1e-6;
        for i in range(4):
            gseq.setChannelFilterCompensation(i+1,'HP',order=1,tau=hptau);

    def buildsequencetable(elem,param,start,stop,points):
        gseq.setSR(elem.SR);
        value=np.linspace(start,stop,points);
        #if first letter is "N"
        #if second word is time
        #setpulseduration
        #if second word is volt
        #setpulselevel
        for n in range(points):
            setpulseparameter(elem,param,value[n]);
            correctionDelem(elem);
            gseq.addElement(n+1, elem);
            gseq.setSequenceSettings(n+1,0,1,0,0);
            # Arguments are position, wait for trigger (0 means OFF), number of repetitions 
            #(0 is infinite, 1 is one), jump target (0 is off), goto (0 means next)
        gseq.setSequenceSettings(n+1,0,1,0,1);            