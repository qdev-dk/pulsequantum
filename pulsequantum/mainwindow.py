

import time
from PyQt5.QtCore import QCoreApplication,Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication, QWidget, QFrame,QMainWindow, QPushButton, QAction, QMessageBox, QLineEdit, QLabel, QSizePolicy
from PyQt5.QtWidgets import QCheckBox,QDialog,QTableWidget,QTableWidgetItem,QVBoxLayout,QHBoxLayout,QComboBox,QGridLayout
import pickle 
import broadbean as bb
from broadbean.plotting import plotter
from awgsequencing import Sequencing
from pulsebuilding import Gelem

import matplotlib
matplotlib.use('QT5Agg')



#############################################################################################
#Hardcoded stuff, should incorporate into main code
#############################################################################################

divch1=11.5;divch2=11.75;divch3=11.7;divch4=1; #Hardcoded channel dividers
divch=[divch1,divch2,divch3,divch4];

class pulsetable(QMainWindow,Gelem):
    """
    This is the GUI setup for the main window

    AWG=None AWG instance
    nchans=2 number of channels,
    nlines=3 number of elements
    corrDflag=0 Global flag: Is correction D pulse already defined in the pulse table?

    """

    def __init__(self, AWG=None, nchans=2, nlines=3, corrDflag=0):
        super().__init__()
        self.setGeometry(50, 50, 1100, 900)
        self.setWindowTitle('Pulse Table Panel')
        self.mainwindow = pulsetable
        self.statusBar()
        self._sequencebox = None
        self.AWG = AWG
        self.nchans = nchans
        self.nlines = nlines
        self.corrDflag = corrDflag
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        
        self.home()

    def home(self):

        
        # Set up initial pulse table
        table = QTableWidget(4, 4, self)
        table.setGeometry(50, 100, 1000, 400)
        table.setColumnCount((self.nchans*3)+2)
        table.setRowCount(self.nlines)
        
        # Set horizontal headers
        h = self.nchans+1
        table.setHorizontalHeaderItem(0, QTableWidgetItem("Time (us)"))
        table.setHorizontalHeaderItem(1, QTableWidgetItem("Ramp? 1=Yes"))
        for i in range(self.nchans):
            table.setHorizontalHeaderItem(i+2, QTableWidgetItem("CH%d"%(i+1)))
            table.setHorizontalHeaderItem(h+1, QTableWidgetItem("CH%dM1"%(i+1)))
            table.setHorizontalHeaderItem(h+2, QTableWidgetItem("CH%dM2"%(i+1)))
            h = h+2
                        
        # Set vertical headers
        nlist = ["load", "unload", "measure"]
        for i in range(self.nlines):
            table.setVerticalHeaderItem(i, QTableWidgetItem(nlist[i]))
            
        # Set table items to zero initially
        for column in range(table.columnCount()):
            for row in range(table.rowCount()):
                if column == 0:
                    table.setItem(row, column, QTableWidgetItem("1"))
                else:
                    table.setItem(row, column, QTableWidgetItem("0"))


        # Divider wiget
        win_divider = QWidget(self)
        lay_divider = QGridLayout(win_divider)
        chlabel = []
        chbox = []
        for i in range(4):  # todo make dynamic with number of channels
            chlabel.append(QLabel(self))
            chlabel[i].setText('Ch%d'%(i+1))
            chbox.append(QLineEdit(self))
            chbox[i].setText('{}'.format(divch[i]))
            lay_divider.addWidget(chlabel[i], 0, i, 1, 1)
            lay_divider.addWidget(chbox[i], 1, i, 1, 1)
 
        # Set dividers
        divbtn = QPushButton('Set Dividers', self)
        divbtn.clicked.connect(lambda state: self.setDividers(chbox))
        lay_divider.addWidget(divbtn, 2, 0, 1, 4)
        win_divider.move(100, 520)
        win_divider.resize(200, 100) 

        # AWG clock ("sample rate")
        win_AWGclock = QWidget(self)
        lay_AWGclock = QGridLayout(win_AWGclock)
        setawgclockbox = QLineEdit(self);
        setawgclockbox.setText('1.2');
        #setawgclockbox.setGeometry(500,550,40,40);
        setawgclocklabel = QLabel(self);
        setawgclocklabel.setText('AWG Clock (GS/s)');
        #setawgclocklabel.move(500, 520);
        setawgclocklabel.resize(setawgclocklabel.sizeHint())
        setawgclockbtn = QPushButton('Set AWG Clock', self);
        setawgclockbtn.clicked.connect(lambda state: self.setAWGClock(setawgclockbox));
        #setawgclockbtn.move(550,550);
        setawgclockbtn.resize(setawgclockbtn.sizeHint())
        lay_AWGclock.addWidget(setawgclocklabel, 0, 0, 2, 1)
        lay_AWGclock.addWidget(setawgclockbox, 1, 0, 1, 1)
        lay_AWGclock.addWidget(setawgclockbtn, 1, 1, 1, 1)
        win_AWGclock.move(500, 520)
        win_AWGclock.resize(200, 100) 
        
        # Absolute Marker
        win = QWidget(self);
        lay= QVBoxLayout(win);
        lay.addStretch();
        lay1= QHBoxLayout();
        lay1.addStretch();
        lay2= QHBoxLayout();
        lay2.addStretch();
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
        sqpbtn = QPushButton('Square Pulse', self)
        sqpbtn.clicked.connect(lambda state:self.squarePulse(table))       
        
        #Pulse Triangle
        ptpbtn = QPushButton('Pulse Triangle', self)
        ptpbtn.clicked.connect(lambda state:self.pulseTriangle(table)) 
        
        #Spin Funnel
        sfpbtn = QPushButton('Spin Funnel', self)
        sfpbtn.clicked.connect(lambda state:self.spinFunnel(table))

        #Dephasing
        dppbtn = QPushButton('Dephasing', self)
        dppbtn.clicked.connect(lambda state:self.Dephasing(table))



        
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
        table_from_seq.clicked.connect(lambda state: self.from_sequence(table, seq = self._sequencebox.gseq))
        
        lay_puls.addWidget(runbtn,0,0,1,1)
        lay_puls.addWidget(plotbtn,0,1,1,1)
        lay_puls.addWidget(savebtn,1,0,1,1)
        lay_puls.addWidget(loadbtn,1,1,1,1)
        lay_puls.addWidget(sqpbtn,2,0,1,1)        
        lay_puls.addWidget(ptpbtn,2,1,1,1)
        lay_puls.addWidget(sfpbtn,2,2,1,1)
        lay_puls.addWidget(dppbtn,1,2,1,1)
        lay_puls.addWidget(table_from_seq ,2,3,1,1)
        win_puls.move(20,5)
        win_puls.resize(win_puls.sizeHint())
        
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
        corrbtn.move(100, 700)

         

        #Sequence and upload
        seqbtn = QPushButton('Upload Sequence', self)
        seqbtn.clicked.connect(lambda state:self.sequence())
        seqbtn.resize(seqbtn.sizeHint())
        seqbtn.move(400, 700)

        
        
        
        
        
        self.show()
        win.hide()
        
        
    def addChannel(self,table,whichch):
        self.nchans=self.nchans+1;
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
        self.nchans=self.nchans-1;
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
        self.nlines=self.nlines+1;
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
        self.nlines=self.nlines-1;
        for n in range(table.rowCount()):
            if table.verticalHeaderItem(n).text()==whichp.text():
                if whichp.text()=='corrD':
                    self.corrDflag=0;
                table.removeRow(n);
    
    def renamePulse(self,table,oldpname,newpname):
        for n in range(table.rowCount()):
            if table.verticalHeaderItem(n).text()==oldpname.text():
                table.setVerticalHeaderItem(n,QTableWidgetItem(newpname.text()));
    
    
        
    def setDividers(self,chbox):
        for i in range(len(divch)):
            divch[i]=(float(chbox[i].text()));
        
    def setAWGClock(self,setawgclockbox):
        self.awgclock=(float(setawgclockbox.text()))*1e9;
        
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
        tempbp=self.gelem._data[chno]['blueprint'];
        if m==1:
            tempbp.marker1=[(mstart,mstop)];
        if m==2:
            tempbp.marker2=[(mstart,mstop)];
        self.gelem._data[chno]['blueprint']=tempbp;
    
    def absMarkerRemove(self,absmarkerch):
        tempbp=bb.BluePrint();
        index=absmarkerch.currentIndex();
        ch=[1,1,2,2,3,3,4,4];chno=ch[index];
        mno=[1,2,1,2,1,2,1,2];m=mno[index];
        tempbp=self.gelem._data[chno]['blueprint'];
        if m==1:
            tempbp.marker1=[];
        if m==2:
            tempbp.marker2=[];
        self.gelem._data[chno]['blueprint']=tempbp;
        
        


    
    def sequence(self):
        if self._sequencebox is None:
            self._sequencebox = Sequencing(AWG = self.AWG, gelem = self.gelem)
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
    
    # From Sequence
    def from_sequence(self, table, seq):
         
        seq_description = seq.description['1']['channels']
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
         
        self.nchans = len(values)
        nsegs = len(values[0])


        table.setColumnCount((self.nchans*3)+2)
        table.setRowCount(nsegs)
        
        #Set horizontal headers
        h=self.nchans+1;
        table.setHorizontalHeaderItem(0, QTableWidgetItem("Time (us)"));
        table.setHorizontalHeaderItem(1, QTableWidgetItem("Ramp? 1=Yes"));
        for i in range(self.nchans):
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
            for ch in range(self.nchans):
               val = str(values[ch][seg]/(divch[ch]*1e-3))
               mark1 = str(marker1[ch][seg])
               mark2 = str(marker2[ch][seg])
               table.setItem(seg,ch+2, QTableWidgetItem(val))
               table.setItem(seg,ch*2+4, QTableWidgetItem(mark1))
               table.setItem(seg,ch*2+5, QTableWidgetItem(mark2))

        
        

        
