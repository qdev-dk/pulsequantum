#todo: 
#- fix sampling rate to match clock speed when changed

# import and initialise the driver and ensure that the sample
# rate and channel voltage is correct

import matplotlib
from PyQt5.QtWidgets import QWidget, QFrame,  QPushButton, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox, QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QComboBox, QGridLayout
from broadbean.plotting import plotter
from sequencebuilding import Gseq
matplotlib.use('QT5Agg')



#Any new parameter defined for the "Special" sequencing tab needs to go here in order to appear in the dropdown menu
params = ["det", "psm_load", "psm_unload", "psm_load_sym", "psm_unload_sym", "dephasing_corrD"]


class Sequencing(QDialog, Gseq):
    """
    Class for sequencing (secondary) window
    """

    def __init__(self, AWG=None, gelem=None):
        super().__init__(AWG=AWG, gelem=gelem)
        self.setGeometry(200, 200, 900, 500)
        self.setWindowTitle("Sequencing")
        self.setMinimumWidth(350)
        self.home()

    def home(self):
        
        # Create channel voltage, divider and offset boxes and buttons
        win4 = QWidget(self)
        lay4 = QGridLayout(win4)
        vpp = QLabel(self)
        vpp.setText('Vpp')
        offset = QLabel(self)
        offset.setText('Offset')
        lay4.addWidget(vpp, 0, 1, 1, 1)
        lay4.addWidget(offset, 0, 2, 1, 1)
        number_channels = 4
        chlabel = list(range(number_channels))
        chbox = list(range(number_channels))
        offbox = list(range(number_channels))
        for i in range(number_channels):
            chlabel[i] = QLabel(self)
            chlabel[i].setText('Ch%d'%(i+1))
            chbox[i] = QLineEdit(self)
            chbox[i].setText('4.5')
            offbox[i] = QLineEdit(self)
            offbox[i].setText('0')
            lay4.addWidget(chlabel[i], i+1, 0, 1, 1)
            lay4.addWidget(chbox[i], i+1, 1, 1, 1)
            lay4.addWidget(offbox[i], i+1, 2, 1, 1)
        win4.move(10, 100)

        # Continuous sequence?
        contseq = QWidget(self)
        lay_contseq = QGridLayout(contseq)
        contseqboxlabel = QLabel(self)
        contseqboxlabel.setText('Simple continuous element?')
        contseqboxlabel.resize(contseqboxlabel.sizeHint())
        contseqbox = QCheckBox(self)
        lay_contseq.addWidget(contseqboxlabel, 0, 0, 1, 1)
        lay_contseq.addWidget(contseqbox, 0, 1, 1, 1)
        contseq.move(20, 280)

        # Upload to AWG
        # Function
        uploadbtn = QPushButton('Upload To AWG', self)
        uploadbtn.clicked.connect(lambda state: self.uploadToAWG(Choose_awg, chbox))
        
        # Choose awg
        Choose_awg = QComboBox(self)
        Choose_awg.addItem('AWG5014')
        Choose_awg.addItem('AWG5208')

        # Update sequencing parameters: table and update button
        win2 = QWidget(self)
        lay2 = QVBoxLayout(win2)
        seqtable = QTableWidget(4, 4, self)
        seqtable.setColumnCount(4)
        # Set top headers
        hlist = ["TrigWait", "NumReps", "JumpTarget", "Goto"]
        for i in range(len(hlist)):
            seqtable.setColumnWidth(i, 70)
            seqtable.setHorizontalHeaderItem(i, QTableWidgetItem(hlist[i]))
        seqtable.setRowCount(0)
        updateseqbtn = QPushButton('Update sequence', self)
        updateseqbtn.clicked.connect(lambda state: self.changedSeqTable(seqtable))
        updateseqbtn.resize(updateseqbtn.sizeHint())
        lay2.addWidget(seqtable)
        lay2.addWidget(updateseqbtn)
        win2.move(450, 30)
        win2.resize(win2.sizeHint())
        
        # Update sequencing parameters: do this?
        changeseqbox = QCheckBox(self)
        changeseqbox.move(630, 10)
        changeseqbox.stateChanged.connect(lambda state: self.seqchangeWidget(changeseqbox, win2, seqtable, seqpts))
        changeseqboxlabel = QLabel(self)
        changeseqboxlabel.setText('Change sequencing options?')
        changeseqboxlabel.move(450, 10)
        changeseqboxlabel.resize(changeseqboxlabel.sizeHint())
        
        # Build Sequence and take parameters
        win3 = QWidget(self)
        lay3 = QGridLayout(win3)
        buildseqlabel = QLabel(self)
        buildseqlabel.setText('Select a parameter to build the sequence:')
        buildseqlabel.resize(buildseqlabel.sizeHint())
        buildseqbtn = QPushButton('Build sequence', self)
        buildseqbtn.clicked.connect(lambda state: self.buildSequenceWrap(chbox, offbox, contseqbox, timevoltbox, whichpulse, sparambox, seqstart, seqstop, seqpts))
        buildseqbtn.resize(buildseqbtn.sizeHint())
        buildseqbtn.move(350, 100)
        
        # Native and special parameters
        timevoltbox = QComboBox(self)
        timevoltbox.addItem("Time")
        for i in range(number_channels):
            timevoltbox.addItem("Ch%{} Voltage".format(i))
        whichpulse = QLineEdit(self)
        whichpulse.setText('Which pulse?')
        whichpulse.resize(whichpulse.sizeHint())
        sparambox = QComboBox(self)
        sparambox.addItem("-Special-")
        for i in range(len(params)):
            sparambox.addItem(params[i])
        # Start/stop and build
        lay32 = QHBoxLayout()
        lay32.addStretch()
        startslabel = QLabel(self)
        startslabel.setText('Start:')
        stopslabel = QLabel(self)
        stopslabel.setText('Stop:')
        pointsslabel = QLabel(self)
        pointsslabel.setText('Points:')
        seqstart = QLineEdit(self)
        seqstart.setText('0')
        seqstart.resize(seqstart.sizeHint())
        seqstop = QLineEdit(self)
        seqstop.setText('0')
        seqstop.resize(seqstop.sizeHint())
        seqpts = QLineEdit(self)
        seqpts.setText('0')
        seqpts.resize(seqpts.sizeHint())
        
        lay3.addWidget(buildseqlabel, 0, 0, 1, 3)
        lay3.addWidget(timevoltbox, 1, 0, 1, 1)
        lay3.addWidget(whichpulse, 1, 1, 1, 1)
        lay3.addWidget(sparambox, 1, 2, 1, 1)
        lay3.addWidget(startslabel, 2, 0, 1, 1)
        lay3.addWidget(stopslabel, 2, 1, 1, 1)
        lay3.addWidget(pointsslabel, 2, 2, 1, 1)
        lay3.addWidget(seqstart, 3, 0, 1, 1)
        lay3.addWidget(seqstop, 3, 1, 1, 1)
        lay3.addWidget(seqpts, 3, 2, 1, 1)
        lay3.addWidget(buildseqbtn, 4, 0, 1, 3)
        lay3.addWidget(uploadbtn, 5, 0, 1, 3)
        lay3.addWidget(Choose_awg, 6, 0, 1, 2)
        win3.move(10, 300)
        win3.resize(win3.sizeHint())
        
        
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
        savesbtn.clicked.connect(lambda state: self.gseq.write_to_json(SeqTo.text()))
        # plot sequence
        plotsbtn = QPushButton('Plot Sequence', self);
        plotsbtn.clicked.connect(lambda state: plotter(self.gseq))
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
############################################################################################################################################################################################################


   
    def seqchangeWidget(self,changeseqbox,win2,seqtable,seqpts):
        if changeseqbox.isChecked():
            self.updateSeqTable(seqtable,int(seqpts.text()));
            win2.show();
        else:
            win2.hide();
    
    def updateSeqTable(self,seqtable,seqpts):
        if self.gseq.points==0:
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
    
    