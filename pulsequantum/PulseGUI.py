# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 17:43:03 2019

@author: Triton4acq_2
"""
#todo: 
#- fix sampling rate to match clock speed when changed

# import and initialise the driver and ensure that the sample
# rate and channel voltage is correct



import sys,math,time
from PyQt5.QtCore import QCoreApplication,Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication, QWidget, QFrame,QMainWindow, QPushButton, QAction, QMessageBox, QLineEdit, QLabel, QSizePolicy
from PyQt5.QtWidgets import QCheckBox,QDialog,QTableWidget,QTableWidgetItem,QVBoxLayout,QHBoxLayout,QComboBox,QGridLayout

import pickle 
import broadbean as bb
from broadbean.plotting import plotter

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
matplotlib.use('QT5Agg')
import numpy as np
import time

#############################################################################################
#Hardcoded stuff, should incorporate into main code
#############################################################################################

nlines=3;
nchans=2;

ramp = bb.PulseAtoms.ramp; #Globally defined ramp, element, and sequence
gelem = bb.Element();
gseq = bb.Sequence();

divch1=11.5;divch2=11.75;divch3=11.7;divch4=1; #Hardcoded channel dividers
divch=[divch1,divch2,divch3,divch4];

awgclock=1.2e9;
corrDflag=0; #Global flag: Is correction D pulse already defined in the pulse table?

#Any new parameter defined for the "Special" sequencing tab needs to go here in order to appear in the dropdown menu
params=["det","psm_load","psm_unload","psm_load_sym","psm_unload_sym","dephasing_corrD"]
 


#############################################################################################
#Class for sequencing (secondary) window
#############################################################################################

class sequencing(QDialog,):
    """
    Should have a docstring
    """

    def __init__(self,AWG):
        #super(sequencing, self).__init__()
        super().__init__()
        self.setGeometry(200, 200, 900, 500)
        self.setWindowTitle("Sequencing")
        self.setMinimumWidth(350)
        self.home()
        self.AWG = AWG

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
        runself.AWGtn = QPushButton('Run AWG', self);
        runself.AWGtn.clicked.connect(lambda state: self.runAWG(Choose_awg))
        lay5.addWidget(awglabel,1,1,1,1);lay5.addWidget(runself.AWGtn,1,2,1,1);
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
        plotter(gelem);
    
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
        gseq.setSR(gelem.SR);
        #for chan in gseq.channels:
         #   gseq.setChannelAmplitude(chan,(float(chbox[chan-1].text())));
          #  gseq.setChannelOffset(chan,(float(offbox[chan-1].text())));
        if contseqbox.isChecked():
            gseq.addElement(1,gelem);
            gseq.setSequencingTriggerWait(1,0)
            gseq.setSequencingNumberOfRepetitions(1,0)
            gseq.setSequencingEventJumpTarget(1,0)
            gseq.setSequenceSettings(1,0,0,0,0);
            for chan in gseq.channels:
                gseq.setChannelAmplitude(chan,(float(chbox[chan-1].text())));
                gseq.setChannelOffset(chan,(float(offbox[chan-1].text())));  
            return;
        elif sparam!="-Special-":
            buildsequencetable(gelem,sparam,sstart,sstop,spts);
        else:
            buildsequencetable(gelem,newparam,sstart,sstop,spts);
          
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
    
    
#############################################################################################
# Main pulse building class and main window
#############################################################################################

class pulsetable(QMainWindow):
    """
    Should have a docstring
    """

    def __init__(self,AWG):
        #super(pulseGUI, self).__init__()
        super().__init__()
        self.setGeometry(50, 50, 1100, 900)
        self.setWindowTitle('Pulse Table Panel')
        self.mainwindow=pulsetable
        self.statusBar()
        self._sequencebox=None
        self.AWG = AWG
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        
        self.home()

    def home(self):

        
        #Set up initial pulse table
        table=QTableWidget(4,4,self)
        table.setGeometry(50, 100, 1000, 400)
        table.setColumnCount((nchans*3)+2)
        table.setRowCount(nlines)
        
        #Set horizontal headers
        h=nchans+1;
        table.setHorizontalHeaderItem(0, QTableWidgetItem("Time (us)"));
        table.setHorizontalHeaderItem(1, QTableWidgetItem("Ramp? 1=Yes"));
        for i in range(nchans):
            table.setHorizontalHeaderItem(i+2, QTableWidgetItem("CH%d"%(i+1)));
            table.setHorizontalHeaderItem(h+1, QTableWidgetItem("CH%dM1"%(i+1)));
            table.setHorizontalHeaderItem(h+2, QTableWidgetItem("CH%dM2"%(i+1)));
            h=h+2;
        
        
        
        #Set vertical headers
        nlist=["load", "unload", "measure"];
        for i in range(nlines):
            table.setVerticalHeaderItem(i, QTableWidgetItem(nlist[i]));
            
        #Set table items to zero initially    
        for column in range(table.columnCount()):
            for row in range(table.rowCount()):
                if column==0:
                    table.setItem(row,column, QTableWidgetItem("1"));
                else:
                    table.setItem(row,column, QTableWidgetItem("0"));

        # Create channel divider boxes and buttons
        chlabel1='Ch1';chlabel2='Ch2';chlabel3='Ch3';chlabel4='Ch4';
        chlabel=[chlabel1,chlabel2,chlabel3,chlabel4];
        for i in range(len(chlabel)):
            chlabel[i]= QLabel(self);chlabel[i].setText('Ch%d'%(i+1));chlabel[i].move(100+(50*i), 520)

        chbox1 = QLineEdit(self);chbox2 = QLineEdit(self);chbox3 = QLineEdit(self);chbox4 = QLineEdit(self);
        chbox=[chbox1,chbox2,chbox3,chbox4];
        for i in range(len(chbox)):
            chbox[i].setText('{}'.format(divch[i]));
            chbox[i].setGeometry(100+(50*i),550,40,40)
        
        #Set dividers
        divbtn = QPushButton('Set Dividers', self)
        divbtn.clicked.connect(lambda state: self.setDividers(chbox))
        divbtn.resize(divbtn.sizeHint())
        divbtn.move(300,550)

        # AWG clock ("sample rate")
        setawgclockbox = QLineEdit(self);setawgclockbox.setText('1.2');setawgclockbox.setGeometry(500,550,40,40);
        setawgclocklabel= QLabel(self);setawgclocklabel.setText('AWG Clock (GS/s)');setawgclocklabel.move(500, 520);setawgclocklabel.resize(setawgclocklabel.sizeHint())
        setawgclockbtn = QPushButton('Set AWG Clock', self);setawgclockbtn.clicked.connect(lambda state: self.setAWGClock(setawgclockbox));setawgclockbtn.move(550,550);setawgclockbtn.resize(setawgclockbtn.sizeHint())
        
        #Absolute Marker
        win = QWidget(self);
        lay= QVBoxLayout(win);lay.addStretch();lay1= QHBoxLayout();lay1.addStretch();lay2= QHBoxLayout();lay2.addStretch();
        absmarkerch=QComboBox(self);
        for i in range(len(chbox)): 
            absmarkerch.addItem('CH%dM1'%(i+1));absmarkerch.addItem('CH%dM2'%(i+1));
        absstart=QLineEdit(self);absstart.setText('0');absstart.resize(absstart.sizeHint());absstop=QLineEdit(self);absstop.setText('0');absstop.resize(absstop.sizeHint());
        abssetbtn = QPushButton('Set (us)', self);absrembtn = QPushButton('Remove All', self);abssetbtn.clicked.connect(lambda state: self.absMarkerSet(absmarkerch,absstart,absstop));absrembtn.clicked.connect(lambda state: self.absMarkerRemove(absmarkerch))
        lay.addWidget(absmarkerch);lay1.addWidget(absstart);lay1.addWidget(absstop);
        lay2.addWidget(abssetbtn);lay2.addWidget(absrembtn);lay.addLayout(lay1);lay.addLayout(lay2);
        win.move(700,530);
        win.resize(win.sizeHint());
        absmarkerbox = QCheckBox(self);absmarkerbox.move(830, 515);absmarkerbox.stateChanged.connect(lambda state: self.absMarkerWidget(absmarkerbox,win))
        absmarkerboxlabel= QLabel(self);absmarkerboxlabel.setText('Absolute Marker');absmarkerboxlabel.move(720, 520);absmarkerboxlabel.resize(absmarkerboxlabel.sizeHint())
        
        # This is the start of top left buttons
        win_puls = QWidget(self);
        lay_puls= QGridLayout(win_puls);        
        #Square Pulse
        sqpbtn = QPushButton('Square Pulse', self);
        sqpbtn.clicked.connect(lambda state:self.squarePulse(table))       
        
        #Pulse Triangle
        ptpbtn = QPushButton('Pulse Triangle', self);
        ptpbtn.clicked.connect(lambda state:self.pulseTriangle(table)) 
        
        #Spin Funnel
        sfpbtn = QPushButton('Spin Funnel', self);
        sfpbtn.clicked.connect(lambda state:self.spinFunnel(table))

        #Dephasing
        sfpbtn = QPushButton('Dephasing', self);sfpbtn.resize(sfpbtn.sizeHint());sfpbtn.move(290, 70)
        sfpbtn.clicked.connect(lambda state:self.Dephasing(table))



        
        #Plot Element
        plotbtn = QPushButton('Plot Element', self)
        #plotbtn.resize(plotbtn.sizeHint());plotbtn.move(185, 10)
        plotbtn.clicked.connect(lambda state:self.plotElement())
        
        #Generate Element
        runbtn = QPushButton('Generate Element', self);
        #runbtn.resize(runbtn.sizeHint());runbtn.move(40, 10);
        runbtn.clicked.connect(lambda state: self.generateElement(table))
        
        #Save Element
        savebtn = QPushButton('Save Element', self)
        savebtn.clicked.connect(lambda state:self.saveElement())
        
        #Load Element
        loadbtn = QPushButton('Load Element', self)
        loadbtn.clicked.connect(lambda state: self.loadElement(table))
        
        #Populate table from Sequence
        table_from_seq = QPushButton('Element from Sequence', self);
        table_from_seq.clicked.connect(lambda state: self.from_sequence(table))
        
        lay_puls.addWidget(runbtn,0,0,1,1);
        lay_puls.addWidget(plotbtn,0,1,1,1);
        lay_puls.addWidget(savebtn,1,0,1,1);
        lay_puls.addWidget(loadbtn,1,1,1,1);
        lay_puls.addWidget(sqpbtn,2,0,1,1);        
        lay_puls.addWidget(ptpbtn,2,1,1,1);
        lay_puls.addWidget(sfpbtn,2,2,1,1);
        lay_puls.addWidget(table_from_seq ,2,3,1,1);
        win_puls.move(20,5);
        win_puls.resize(win_puls.sizeHint());
        
        # This is the end of top left buttons

        #Add a channel
        whichch=QComboBox(self);whichch.move(420,10);
        for i in range(len(chbox)): 
            whichch.addItem('CH%d'%(i+1));
        addchbtn = QPushButton('Add Channel', self)
        addchbtn.clicked.connect(lambda state: self.addChannel(table,whichch))
        addchbtn.resize(addchbtn.sizeHint())
        addchbtn.move(350, 40)
        
        #Remove a channel
        remchbtn = QPushButton('Remove Channel', self)
        remchbtn.clicked.connect(lambda state: self.remChannel(table,whichch))
        remchbtn.resize(remchbtn.sizeHint())
        remchbtn.move(470, 40)
        
        #Add a pulse
        addpbtn = QPushButton('Add Pulse', self)
        whichp = QLineEdit(self);whichp.setText('Set name');whichp.setGeometry(720,15,70,20);
        addpbtn.clicked.connect(lambda state: self.addPulse(table,whichp))
        addpbtn.resize(addpbtn.sizeHint())
        addpbtn.move(660, 40)
        
        #Remove a pulse
        rempbtn = QPushButton('Remove Pulse', self)
        rempbtn.clicked.connect(lambda state: self.remPulse(table,whichp))
        rempbtn.resize(rempbtn.sizeHint())
        rempbtn.move(760, 40)
        
        #Rename a pulse
        renamepbtn = QPushButton('Rename Pulse', self);renamepbtn.resize(renamepbtn.sizeHint());renamepbtn.move(910, 40)
        oldpname = QLineEdit(self);oldpname.setText('Old name');oldpname.setGeometry(890,15,70,20);
        newpname = QLineEdit(self);newpname.setText('New name');newpname.setGeometry(965,15,70,20);
        renamepbtn.clicked.connect(lambda state: self.renamePulse(table,oldpname,newpname))
        
        #Remove a pulse
        rempbtn = QPushButton('Remove Pulse', self)
        rempbtn.clicked.connect(lambda state: self.remPulse(table,whichp))
        rempbtn.resize(rempbtn.sizeHint())
        rempbtn.move(760, 40)
        
        
        #Correction D
        corrbtn = QPushButton('Correction D', self)
        corrbtn.clicked.connect(lambda state: self.correctionD(table))
        corrbtn.resize(corrbtn.sizeHint())
        corrbtn.move(100, 600)

         

        #Sequence and upload
        seqbtn = QPushButton('Upload Sequence', self)
        seqbtn.clicked.connect(lambda state:self.sequence(self.AWG))
        seqbtn.resize(seqbtn.sizeHint())
        seqbtn.move(400, 600)

        
        
        
        
        
        self.show()
        win.hide()
        
        
    def generateElement(self,table):
        #Make element from pulse table
        global gelem;
        gelem= bb.Element();
        h=int((table.columnCount()-2)/3);
        prevlvl=0;
        global awgclock;
        v=table.rowCount();
        for col in range(2,h+2):
            chno=int(table.horizontalHeaderItem(col).text()[2]);
            gp = bb.BluePrint()
            gp.setSR(awgclock);
            for row in range(v):
                nm=table.verticalHeaderItem(row).text();
                dr=(float(table.item(row,0).text()))*1e-6;
                rmp=int(table.item(row,1).text());
                lvl=(float(table.item(row,col).text()))*divch[col-2]*1e-3;
                mkr1=int(table.item(row,h+2).text());
                mkr2=int(table.item(row,h+3).text());
                if rmp==0:
                    gp.insertSegment(row, ramp, (lvl, lvl), name=nm, dur=dr);
                if rmp==1:
                    if row==0:
                        gp.insertSegment(row, ramp, (0, lvl), name=nm, dur=dr);
                    else:
                        gp.insertSegment(row, ramp, (prevlvl, lvl), name=nm, dur=dr);
                if mkr1==1:
                    gp.setSegmentMarker(nm, (0,dr), 1);
                if mkr2==1:
                    gp.setSegmentMarker(nm, (0,dr), 2);
                prevlvl=lvl;
            gelem.addBluePrint(chno, gp);
            h=h+2;
        gelem.validateDurations();
        
    def plotElement(self):
        plotter(gelem);
    

#############################################################################################
# Saving and loading of element does not work yet. Using it may crash the GUI. I tried to use
# pickle for saving an element object, however this created tons of problems I wasn't able to
# solve. If I had to do it again, I would drill down into the dictionaries to save and load.
#############################################################################################
    def saveElement(self):
        savedict=gelem.getArrays(includetime=True);
        dlg=QFileDialog(self);
        fileName, _ =  dlg.getSaveFileName(self,"Save Element",r"A:\Users\fabio\QCoDeSLocal\SpinQubit\Pulse_wrappers\Pulsinglibrary");
        with open(fileName, 'wb') as f:
            pickle.dump(savedict,f,protocol=pickle.HIGHEST_PROTOCOL)
    
    def addChannel(self,table,whichch):
        global nchans;
        nchans=nchans+1;
        index=whichch.currentIndex();
        ch=[1,2,3,4];chno=ch[index];
        n=table.columnCount();nchan=int((table.columnCount()-2)/3);
        table.insertColumn(nchan+2);table.insertColumn(n+1);table.insertColumn(n+2);
        table.setHorizontalHeaderItem(nchan+2, QTableWidgetItem("CH%d"%chno));
        table.setHorizontalHeaderItem(n+1, QTableWidgetItem("CH%dM1"%chno));
        table.setHorizontalHeaderItem(n+2, QTableWidgetItem("CH%dM2"%chno));
        for row in range(table.rowCount()):
            table.setItem(row,nchan+2, QTableWidgetItem("0"));
            table.setItem(row,n+1, QTableWidgetItem("0"));
            table.setItem(row,n+2, QTableWidgetItem("0"));
    
    def remChannel(self,table,whichch):
        global nchans;
        nchans=nchans-1;
        n=table.columnCount();
        n=n-1;
        for i in range(n):
            temp=str(whichch.currentText());
            if str(table.horizontalHeaderItem(i).text())==temp:
                table.removeColumn(i);
            if str(table.horizontalHeaderItem(i).text())==temp+"M1":    
                table.removeColumn(i);
            if str(table.horizontalHeaderItem(i).text())==temp+"M2":
                table.removeColumn(i);
    
    def addPulse(self,table,whichp,i=-1):
        global nlines;
        nlines=nlines+1;
        if i==-1:
            n=table.rowCount();
        else:
            n=i;
        table.insertRow(n);
        table.setVerticalHeaderItem(n,QTableWidgetItem(whichp.text()));
        for column in range(table.columnCount()):
            if column==0:
                table.setItem(n,column, QTableWidgetItem("1"));
            else:
                table.setItem(n,column, QTableWidgetItem("0"));
    
    def remPulse(self,table,whichp):
        global nlines;
        global corrDflag;
        nlines=nlines-1;
        for n in range(table.rowCount()):
            if table.verticalHeaderItem(n).text()==whichp.text():
                if whichp.text()=='corrD':
                    corrDflag=0;
                table.removeRow(n);
    
    def renamePulse(self,table,oldpname,newpname):
        for n in range(table.rowCount()):
            if table.verticalHeaderItem(n).text()==oldpname.text():
                table.setVerticalHeaderItem(n,QTableWidgetItem(newpname.text()));
    
    
        
    def setDividers(self,chbox):
        for i in range(len(divch)):
            divch[i]=(float(chbox[i].text()));
        
    def setAWGClock(self,setawgclockbox):
        global awgclock;
        awgclock=(float(setawgclockbox.text()))*1e9;
        
    def absMarkerWidget(self,absmarkerbox,win):
        if absmarkerbox.isChecked():
            win.show()
        else:
            win.hide()
    
    def absMarkerSet(self,absmarkerch,absstart,absstop):
        tempbp=bb.BluePrint();
        mstart=(float(absstart.text())*1e-6);
        mstop=(float(absstop.text())*1e-6);
        index=absmarkerch.currentIndex();
        ch=[1,1,2,2,3,3,4,4];chno=ch[index];
        mno=[1,2,1,2,1,2,1,2];m=mno[index];
        tempbp=gelem._data[chno]['blueprint'];
        if m==1:
            tempbp.marker1=[(mstart,mstop)];
        if m==2:
            tempbp.marker2=[(mstart,mstop)];
        gelem._data[chno]['blueprint']=tempbp;
    
    def absMarkerRemove(self,absmarkerch):
        tempbp=bb.BluePrint();
        index=absmarkerch.currentIndex();
        ch=[1,1,2,2,3,3,4,4];chno=ch[index];
        mno=[1,2,1,2,1,2,1,2];m=mno[index];
        tempbp=gelem._data[chno]['blueprint'];
        if m==1:
            tempbp.marker1=[];
        if m==2:
            tempbp.marker2=[];
        gelem._data[chno]['blueprint']=tempbp;
        
        
#############################################################################################
# The correction D pulse keeps the centre of gravity of the pulse at the DC value (voltage
# seen by the same when there is no pulsing. Not always used or needed.
#############################################################################################
    def correctionD(self,table):
        global awgclock;
        global corrDflag;
        if corrDflag==1:
            print("Correction D pulse already exists.")
            return;
        corrDflag=1;
        awgclockinus=awgclock/1e6;
        dpulse = QLineEdit(self);dpulse.setText('corrD');
        tottime=0;
        dpos=1;#position of correction D pulse, hardcoded for now
        self.addPulse(table,dpulse,dpos);
        #Set D pulse time to 60% of total pulse cycle time
        for row in range(table.rowCount()):
            nm=table.verticalHeaderItem(row).text();
            if nm!='corrD':
                tottime=tottime+(float(table.item(row,0).text()));
        timeD=round(tottime/1.65*(awgclockinus))/awgclockinus;
        table.setItem(dpos,0, QTableWidgetItem("%f"%timeD));
        
        #Correct all voltages in a loop
        for column in range(6):
            tottimevolt=0;
            colnm=table.horizontalHeaderItem(column).text();
            for row in range(table.rowCount()):
                rownm=table.verticalHeaderItem(row).text();
                rmp=int(table.item(row,1).text());
                if (rownm!='corrD') and (colnm=='CH1' or colnm=='CH2' or colnm=='CH3' or colnm=='CH4'):
                    if rmp==0:
                        tottimevolt=tottimevolt+((float(table.item(row,0).text()))*(float(table.item(row,column).text())));
                    if rmp==1:
                        if row==0:
                            tottimevolt=tottimevolt+((float(table.item(row,0).text()))*(float(table.item(row,column).text()))/2);
                        else:
                            tottimevolt=tottimevolt+((float(table.item(row,0).text()))*((float(table.item(row,column).text()))+(float(table.item(row-1,column).text())))/2);
                voltD=-tottimevolt/timeD;
            if (column!=0) and (column!=1) and (colnm=='CH1' or colnm=='CH2' or colnm=='CH3' or colnm=='CH4'):
                table.setItem(dpos,column, QTableWidgetItem("%f"%voltD));
            


#############################################################################################
# Saving and loading of element does not work yet. Using it may crash the GUI. I tried to use
# pickle for saving an element object, however this created tons of problems I wasn't able to
# solve. If I had to do it again, I would drill down into the dictionaries to save and load.
#############################################################################################    
    def loadElement(self,table):
        global awgclock;
        global gelem;
        #gelem=bb.Element();
        dlg=QFileDialog(self);
        fileName, _ =  dlg.getOpenFileName(self,"Load Element",r"A:\Users\fabio\QCoDeSLocal\SpinQubit\Pulse_wrappers\Pulsinglibrary");
        with open(fileName, 'rb') as f:
            loaddict=pickle.load(f)
        table.setRowCount(0);
        table.setColumnCount(0);
        #Create the element
        chno=list(loaddict.keys());#List of channels
        for i in range(len(chno)):
            temp=loaddict[chno[i]];
            wfm=temp['wfm'];
            newdurations=temp['newdurations'];
            m1=temp['m1'];
            m2=temp['m2'];
            time=temp['time'];
#            print(len(newdurations));print(len(wfm));
            kwargs={'m1':m1,'m2':m2,'time':time};
            gelem.addArray(chno[i],wfm,awgclock,**kwargs);
       # Generate the pulse table

    
    def sequence(self):
        if self._sequencebox is None:
            self._sequencebox=sequencing();
            self._sequencebox.exec_();
        else:
#            global_point = callWidget.mapToGlobal(point)
#            self._sequencebox.move(global_point - QtCore.QPoint(self.width(), 0))
             self.SetForegroundWindow(self._sequencebox)
    
    def close_application(self):

        choice = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if choice == QMessageBox.Yes:
            print('quit application')
            app.exec_()
        else:
            pass




#############################################################################################
# A few hardcoded pulses that we use over and over, and some placeholder buttons.
#############################################################################################

    def squarePulse(self,table):
        table.setColumnCount((2*3)+2);
        table.setRowCount(2);
        #Set horizontal headers
        h=nchans+1;
        table.setHorizontalHeaderItem(0, QTableWidgetItem("Time (us)"));
        table.setHorizontalHeaderItem(1, QTableWidgetItem("Ramp? 1=Yes"));
        for i in range(2):
            table.setHorizontalHeaderItem(i+2, QTableWidgetItem("CH%d"%(i+1)));
            table.setHorizontalHeaderItem(h+1, QTableWidgetItem("CH%dM1"%(i+1)));
            table.setHorizontalHeaderItem(h+2, QTableWidgetItem("CH%dM2"%(i+1)));
            h=h+2;
        
        #Set vertical headers
        nlist=["up", "down"];
        for i in range(2):
            table.setVerticalHeaderItem(i, QTableWidgetItem(nlist[i]));
            
        #Set table items to zero initially    
        for column in range(table.columnCount()):
            for row in range(table.rowCount()):
                if column==0:
                    table.setItem(row,column, QTableWidgetItem("1"));
                else:
                    table.setItem(row,column, QTableWidgetItem("0"));
        table.setItem(1,4, QTableWidgetItem("1"));
        table.setItem(1,5, QTableWidgetItem("1"));


    def pulseTriangle(self,table):
        table.setColumnCount((2*3)+2)
        table.setRowCount(4)
        
        #Set horizontal headers
        h=nchans+1;
        table.setHorizontalHeaderItem(0, QTableWidgetItem("Time (us)"));
        table.setHorizontalHeaderItem(1, QTableWidgetItem("Ramp? 1=Yes"));
        for i in range(nchans):
            table.setHorizontalHeaderItem(i+2, QTableWidgetItem("CH%d"%(i+1)));
            table.setHorizontalHeaderItem(h+1, QTableWidgetItem("CH%dM1"%(i+1)));
            table.setHorizontalHeaderItem(h+2, QTableWidgetItem("CH%dM2"%(i+1)));
            h=h+2;
        
        #Set vertical headers
        nlist=["unload", "load","separate", "measure"];
        #nlist=["detuning_up", "detuning_up_b","down", "down_b"];
        for i in range(4):
            table.setVerticalHeaderItem(i, QTableWidgetItem(nlist[i]));
            
        #Set table items to zero initially    
        for column in range(table.columnCount()):
            for row in range(table.rowCount()):
                if column==0:
                    table.setItem(row,column, QTableWidgetItem("20"));
                else:
                    table.setItem(row,column, QTableWidgetItem("0"));
        for column in range(table.columnCount()):
            table.setItem(3,4, QTableWidgetItem("1"));
        table.setItem(0,2, QTableWidgetItem("-8.8"));
        table.setItem(0,3, QTableWidgetItem("-6"));
        table.setItem(1,2, QTableWidgetItem("-6.8"));
        table.setItem(1,3, QTableWidgetItem("2"));
        table.setItem(2,2, QTableWidgetItem("10.2"));
        table.setItem(2,3, QTableWidgetItem("-4"));
        table.setItem(3,2, QTableWidgetItem("0"));
        table.setItem(3,3, QTableWidgetItem("0"));
        
        # From Sequence
    def from_sequence(self,table):
         
        seq_description = gseq.description['1']['channels']
        seg_name = []
        seg_durations = []
        seg_ramp = []
        values = []
        marker1 = []
        marker2 = []
        for chan in seq_description.keys():
            ch_values = []
            channels_marker1 = []
            channels_marker2 = []
            print(chan)
            marker1_rel = seq_description[chan]['marker1_rel']
            marker2_rel = seq_description[chan]['marker2_rel']
            seg_mar_list = list(seq_description[chan].keys())
            seg_list = [s for s in seg_mar_list if 'segment' in s]
            for i, seg in enumerate(seg_list):
                seg_digt = seq_description[chan][seg]
                tmp_name = seg_digt['name']
                tmp_durations = seg_digt["durations"]
                if tmp_name not in seg_name:
                    seg_name.append(tmp_name)
                    seg_durations.append(tmp_durations)
                    if seg_digt['arguments']['start'] != seg_digt['arguments']['stop']:
                        seg_ramp.append(1)
                    else:
                        seg_ramp.append(0)
                ch_values.append(seg_digt['arguments']['stop'])
                if marker1_rel[i] == (0,0):
                    channels_marker1.append(0)
                else:
                    channels_marker1.append(1)
                    
                if marker2_rel[i] == (0,0):
                    channels_marker2.append(0)
                else:
                    channels_marker2.append(1)             
            values.append(ch_values)
            marker1.append(channels_marker1)
            marker2.append(channels_marker2)
         
        nchans = len(values)
        nsegs = len(values[0])


        table.setColumnCount((nchans*3)+2)
        table.setRowCount(nsegs)
        
        #Set horizontal headers
        h=nchans+1;
        table.setHorizontalHeaderItem(0, QTableWidgetItem("Time (us)"));
        table.setHorizontalHeaderItem(1, QTableWidgetItem("Ramp? 1=Yes"));
        for i in range(nchans):
            table.setHorizontalHeaderItem(i+2, QTableWidgetItem("CH%d"%(i+1)));
            table.setHorizontalHeaderItem(h+1, QTableWidgetItem("CH%dM1"%(i+1)));
            table.setHorizontalHeaderItem(h+2, QTableWidgetItem("CH%dM2"%(i+1)));
            h=h+2;
        
        #Set vertical headers
        #nlist= seg_name
        for i, name in enumerate(seg_name):
            table.setVerticalHeaderItem(i, QTableWidgetItem(name));
            
        
        for seg in range(nsegs):
            duration = str(seg_durations[seg]/1e-6)
            table.setItem(seg,0, QTableWidgetItem(duration))
            ramp_yes = str(seg_ramp[seg])
            table.setItem(seg,0, QTableWidgetItem(duration))
            table.setItem(seg,1, QTableWidgetItem(ramp_yes))
            for ch in range(nchans):
               val = str(values[ch][seg]/(divch[ch]*1e-3))
               mark1 = str(marker1[ch][seg])
               mark2 = str(marker2[ch][seg])
               table.setItem(seg,ch+2, QTableWidgetItem(val))
               table.setItem(seg,ch*2+4, QTableWidgetItem(mark1))
               table.setItem(seg,ch*2+5, QTableWidgetItem(mark2))

        
        
    def spinFunnel(self,table):
        table.setColumnCount((2*3)+2)
        table.setRowCount(8)
        
        #Set horizontal headers
        h=nchans+1;
        table.setHorizontalHeaderItem(0, QTableWidgetItem("Time (us)"));
        table.setHorizontalHeaderItem(1, QTableWidgetItem("Ramp? 1=Yes"));
        for i in range(nchans):
            table.setHorizontalHeaderItem(i+2, QTableWidgetItem("CH%d"%(i+1)));
            table.setHorizontalHeaderItem(h+1, QTableWidgetItem("CH%dM1"%(i+1)));
            table.setHorizontalHeaderItem(h+2, QTableWidgetItem("CH%dM2"%(i+1)));
            h=h+2;
        
        #Set vertical headers
        nlist=["start","unload", "load","reference","wait","separate", "measure","stop"];
        for i in range(8):
            table.setVerticalHeaderItem(i, QTableWidgetItem(nlist[i]));
            
        #Set table items to zero initially    
        for column in range(table.columnCount()):
            for row in range(table.rowCount()):
                table.setItem(row,column, QTableWidgetItem("0"));
        
        #Times
        table.setItem(0,0, QTableWidgetItem("0.01"));
        table.setItem(1,0, QTableWidgetItem("20"));
        table.setItem(2,0, QTableWidgetItem("20"));
        table.setItem(3,0, QTableWidgetItem("10"));
        table.setItem(4,0, QTableWidgetItem("1"));
        table.setItem(5,0, QTableWidgetItem("0.5"));
        table.setItem(6,0, QTableWidgetItem("10"));
        table.setItem(7,0, QTableWidgetItem("0.01"));
        
        #Markers
        table.setItem(6,4, QTableWidgetItem("1"));
        table.setItem(3,4, QTableWidgetItem("1"));
        
        #Pulses
        table.setItem(1,2, QTableWidgetItem("-8.8"));
        table.setItem(1,3, QTableWidgetItem("-6"));
        table.setItem(2,2, QTableWidgetItem("-6.8"));
        table.setItem(2,3, QTableWidgetItem("2"));
        table.setItem(5,2, QTableWidgetItem("9.8"));
        table.setItem(5,3, QTableWidgetItem("-2"));





#if __name__ == "__main__":  # had to add this otherwise app crashed

def run(AWG = None):
    global self.AWG 
    self.AWG = AWG
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    #app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    Gui = pulseGUI()
    app.exec_()

#run()


#############################################################################################
###################           BUILD SEQUENCE TABLE          #################################
#############################################################################################


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


#############################################################################################
###################            SET PULSE PARAMETER          #################################
#############################################################################################

def setpulseparameter(elem,param,value):
    #Define your own parameters here! For setting a segment name use setpulse()
    ch=0;
    if param[0]=='N':
        ch=int(param[7]);
        seg=param[9:len(param)];
        if param[2:6]=="Time":
            setpulseduration(elem,ch,seg,value);
        else:
            setpulselevel(elem,ch,seg,value);
    if param=='det':
        setpulselevel(elem,1,'separate',value*0.8552);#For 20-11
        setpulselevel(elem,2,'separate',-value*0.5183);#For 20-11
        #setpulselevel(elem,1,'separate',value*0.9558);#For 40-31
        #setpulselevel(elem,2,'separate',-value*0.2940);#For 40-31
        
    if param=='psm':
        setpulselevel(elem,1,'detuning',value*0.8);
        setpulselevel(elem,2,'detuning',-value*0.5);



#############################################################################################
###################    CHANGE PULSE LEVEL OR DURATION       #################################
#############################################################################################
def setpulselevel(elem,ch,seg,lvl,div=11.7):
    #Change a pulse within an element
    lvl=lvl*divch[ch-1]*1e-3;
#    print(lvl);
    elem.changeArg(ch,seg,0,lvl,False);
    elem.changeArg(ch,seg,1,lvl,False);

def setpulseduration(elem,ch,seg,dur):
    dur=dur*1e-6;
    ch=gelem.channels;
    for i in range(len(ch)):
        elem.changeDuration(ch[i],seg,dur,False);

#############################################################################################
###################            correctionD Pulse            #################################
#############################################################################################
def correctionDelem(elem):
    global awgclock;
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
    num=len(elem.description['{}'.format(elem.channels[0])])-4
    chs=len(elem.channels)
    #Get all pulses in element
    for j in range(chs):
        #Reinitialise pulses and total time
        start=[];stop=[];ramp=[];name=[];seg_dur=[];
        tottime=0;
        tottimevolt=0;
        timeD=0;voltD=0;
        #Get all pulses for that channel
        for i in range(num):
            pulsestart=1e3*(elem.description['{}'.format(j+1)]['segment_%02d'%(i+1)]['arguments']['start'])/divch[j+1]
            pulsestop=1e3*(elem.description['{}'.format(j+1)]['segment_%02d'%(i+1)]['arguments']['stop'])/divch[j+1] #Need correct channel dividers!
            start.append(pulsestart)
            stop.append(pulsestop)
            if(pulsestart==pulsestop):
                ramp.append(0);
            else:
                ramp.append(1);
            pulsedur=1e6*elem.description['{}'.format(j+1)]['segment_%02d'%(i+1)]['durations']
            seg_dur.append(pulsedur)
            pulsename=elem.description['{}'.format(j+1)]['segment_%02d'%(i+1)]['name']
            name.append(pulsename)
            #Add duration to total time
            if pulsename!='corrD':
             tottime=tottime+pulsedur; #In us  
        #Calculate correctionD time, 65% of the total pulse cycle time
        timeD=round(tottime/1.65*(awgclockinus))/awgclockinus;
        setpulseduration(elem,j+1,'corrD',timeD);
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
        setpulselevel(elem,j+1,'corrD',voltD)