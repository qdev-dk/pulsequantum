import broadbean as bb
import matplotlib
import pandas as pd
import pathlib
import yaml
from PyQt5.QtWidgets import QWidget, QMainWindow, QPushButton, QMessageBox, QLineEdit, QLabel
from PyQt5.QtWidgets import QCheckBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QComboBox, QGridLayout
from pulsequantum.awgsequencing import Sequencing
from pulsequantum.pulsebuilding import Gelem
from os import listdir, path
from os.path import isfile, join
from pulsequantum.dftable import QTableWidgetDF
from pathlib import Path
matplotlib.use('QT5Agg')



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
       
        #self.setStyleSheet("QLabel {font: 11pt Arial}")
        self.setStyleSheet("QLineEdit, QLabel, QPushButton,QComboBox {font: 10pt Arial}")
        #self.setStyleSheet(" {font: 8pt Arial}")

        
        
        #, "QLabel {font: 11pt Arial}")
        self.home()

    def home(self):

        # read in default values
        if path.exists(join(pathlib.Path(__file__).parents[0], 'initfiles/mydefault.yaml')):
            defalutfile = join(pathlib.Path(__file__).parents[0], 'initfiles/mydefault.yaml')
        else:
            defalutfile = join(pathlib.Path(__file__).parents[0], 'initfiles/setupdefault.yaml')
        with open(defalutfile) as file:
            # The FullLoader parameter handles the conversion from YAML
            # scalar values to Python the dictionary format
            init_list = yaml.load(file, Loader=yaml.FullLoader)

        divch = list(init_list['dividers']['channels'].values())
        awgcloc_init = init_list['awgcloc']

        # Set up initial pulse table
        table = QTableWidgetDF(self)
        table.setGeometry(50, 100, 1000, 400)
        self.loadElement(table, path=join(join(pathlib.Path(__file__).parents[0], 'initfiles/init.json')))

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
        win_divider.resize(win_divider.minimumSizeHint())
        #win_divider.resize(200, 100) 

        # AWG clock ("sample rate")
        win_AWGclock = QWidget(self)
        lay_AWGclock = QGridLayout(win_AWGclock)
        setawgclockbox = QLineEdit(self)
        setawgclockbox.setText(awgcloc_init)
        setawgclocklabel = QLabel(self)
        setawgclocklabel.setText('AWG Clock (GS/s)')
        setawgclocklabel.resize(setawgclocklabel.sizeHint())
        setawgclockbtn = QPushButton('Set AWG Clock', self)
        setawgclockbtn.clicked.connect(lambda state: self.setAWGClock(setawgclockbox))
        setawgclockbtn.resize(setawgclockbtn.sizeHint())
        lay_AWGclock.addWidget(setawgclocklabel, 0, 0, 2, 1)
        lay_AWGclock.addWidget(setawgclockbox, 1, 0, 1, 1)
        lay_AWGclock.addWidget(setawgclockbtn, 1, 1, 1, 1)
        win_AWGclock.move(500, 520)
        win_AWGclock.resize(win_AWGclock.minimumSizeHint()) 
        
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

        # lib box
        libbox = QComboBox(self)
        libbox.addItem("-Load From Lib-")
        for i in range(len(self.seq_files)):
            libbox.addItem(self.seq_files[i])
        save_to = QLineEdit(self)
        save_to.setText('enter file name')
        
        # This is the start of top left buttons
        win_puls = QWidget(self);
        lay_puls= QGridLayout(win_puls);        

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
        savebtn.clicked.connect(lambda state:self.saveElement(join(self.libpath,save_to.text())))
        
        #Load Element
        loadbtn = QPushButton('Load Element', self)
        loadbtn.clicked.connect(lambda state: self.loadElement(table,path=join(self.libpath,libbox.currentText()) ))
        
        #Populate table from Sequence
        table_from_seq = QPushButton('Element from Sequence', self)
        table_from_seq.clicked.connect(lambda state: self.from_sequence(table, seq = self._sequencebox.gseq))
        
        lay_puls.addWidget(runbtn,0,0,1,1)
        lay_puls.addWidget(plotbtn,0,1,1,1)
        lay_puls.addWidget(savebtn,2,0,1,1)
        lay_puls.addWidget(save_to,2,1,1,1)
        lay_puls.addWidget(loadbtn,1,0,1,1)
        lay_puls.addWidget(libbox,1,1,1,1)
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
                if str(whichp.text())=='corrD':
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
    

    

    