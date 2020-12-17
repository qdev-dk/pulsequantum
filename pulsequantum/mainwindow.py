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
from pulsequantum.annotateshape import annotateshape
matplotlib.use('QT5Agg')
from PyQt5.QtWidgets import QMainWindow, QAction, QMenu, QApplication



class pulsetable(QWidget, Gelem):
    """
    This is the GUI setup for the main window

    AWG=None AWG instance
    corrDflag=0 Global flag: Is correction D pulse already defined in the pulse table?

    """

    def __init__(self, AWG=None, corrDflag=0):
        super().__init__()
        self.setGeometry(50, 50, 1200, 700)
        self.setWindowTitle('Pulse Table Panel')
        self.mainwindow = pulsetable
        self._sequencebox = None
        self.AWG = AWG
        self.corrDflag = corrDflag    
        self.setStyleSheet("QLineEdit, QLabel, QPushButton,QComboBox {font: 10pt Arial}")
        self.home()
        self.layout

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

        self.divch = list(init_list['dividers']['channels'].values())
        self.awgcloc_init = init_list['awgcloc']
       

        # Set up initial pulse table
        table = QTableWidgetDF(self)
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
            chbox[i].setText('{}'.format(self.divch[i]))
            lay_divider.addWidget(chlabel[i], 0, i, 1, 1)
            lay_divider.addWidget(chbox[i], 1, i, 1, 1)

        # Set dividers
        divbtn = QPushButton('Set Dividers', self)
        divbtn.clicked.connect(lambda state: self.setDividers(chbox))
        lay_divider.addWidget(divbtn, 2, 0, 1, 4)

        
        

        # AWG clock ("sample rate")
        win_AWGclock = QWidget(self)
        lay_AWGclock = QGridLayout(win_AWGclock)
        setawgclockbox = QLineEdit(self)
        setawgclockbox.setText(self.awgcloc_init)
        setawgclocklabel = QLabel(self)
        setawgclocklabel.setText('AWG Clock (GS/s)')
        setawgclocklabel.resize(setawgclocklabel.sizeHint())
        setawgclockbtn = QPushButton('Set AWG Clock', self)
        setawgclockbtn.clicked.connect(lambda state: self.setAWGClock(setawgclockbox))
        setawgclockbtn.resize(setawgclockbtn.sizeHint())
        lay_AWGclock.addWidget(setawgclocklabel, 0, 0, 2, 1)
        lay_AWGclock.addWidget(setawgclockbox, 1, 0, 1, 1)
        lay_AWGclock.addWidget(setawgclockbtn, 1, 1, 1, 1)
        
        # Absolute Marker        
        absmarkerch=QComboBox(self);
        for i in range(len(chbox)): 
            absmarkerch.addItem('CH%dM1'%(i+1))
            absmarkerch.addItem('CH%dM2'%(i+1))
        absstart=QLineEdit(self);
        absstart.setText('0');
        
        absstop=QLineEdit(self);
        absstop.setText('0');
        abssetbtn = QPushButton('Set (us)', self);
        absrembtn = QPushButton('Remove All', self);
        abssetbtn.clicked.connect(lambda state: self.absMarkerSet(absmarkerch,absstart,absstop));
        absrembtn.clicked.connect(lambda state: self.absMarkerRemove(absmarkerch))      
        
        win_absmarker = QWidget(self);      
        lay_absmarker= QGridLayout(win_absmarker)
        lay_absmarker.addWidget(absmarkerch, 0, 0)
        lay_absmarker.addWidget(absstart, 1, 0)
        lay_absmarker.addWidget(absstop, 1, 1)
        lay_absmarker.addWidget(abssetbtn, 3, 0)
        lay_absmarker.addWidget(absrembtn, 3, 1)

        win_absmarkerbox = QWidget(self)
        lay_absmarkerbox = QGridLayout(win_absmarkerbox)
        absmarkerbox = QCheckBox(self);
        absmarkerbox.stateChanged.connect(lambda state: self.absMarkerWidget(absmarkerbox,win_absmarker))
        absmarkerboxlabel= QLabel(self);
        absmarkerboxlabel.setText('Absolute Marker');
        lay_absmarkerbox.addWidget(absmarkerboxlabel, 0, 0)
        lay_absmarkerbox.addWidget(absmarkerbox, 0, 1)
         


        # lib box
        libbox = QComboBox(self)
        libbox.addItem(" -Load From Lib- ")
        for i in range(len(self.seq_files)):
            libbox.addItem(self.seq_files[i])
        save_to = QLineEdit(self)
        save_to.setText('enter file name')
        
        # This is the start of top left buttons
        win_puls = QWidget(self)
        lay_puls = QGridLayout(win_puls)       

        #Plot Element
        plotbtn = QPushButton('Plot Element', self)
        #plotbtn.resize(plotbtn.sizeHint());plotbtn.move(185, 10)
        plotbtn.clicked.connect(lambda state:self.plotElement(table,
                                                             int(plotid_box.text()),
                                                             float(gate_box[0].text())*1e-3,
                                                             float(gate_box[1].text())*1e-3,
                                                             int(channel_mapping_box[0].text()),
                                                             int(channel_mapping_box[1].text()),
                                                             float(chbox[int(channel_mapping_box[0].text())].text()),
                                                             float(chbox[int(channel_mapping_box[0].text())].text())
                                                             ))
        # Generate Element
        runbtn = QPushButton('Generate Element', self)
        # runbtn.resize(runbtn.sizeHint());runbtn.move(40, 10);
        runbtn.clicked.connect(lambda state: self.generateElement(table))
        
        # Save Element
        savebtn = QPushButton('Save Element', self)
        savebtn.clicked.connect(lambda state:self.saveElement(join(self.libpath,save_to.text())))
        
        # Load Element
        loadbtn = QPushButton('Load Element', self)
        loadbtn.clicked.connect(lambda state: self.loadElement(table, path=join(self.libpath,libbox.currentText())))
 
        lay_puls.addWidget(runbtn, 0, 0, 1, 1)
        lay_puls.addWidget(plotbtn, 0, 1, 1, 1)
        lay_puls.addWidget(savebtn, 2, 0, 1, 1)
        lay_puls.addWidget(save_to, 2, 1, 1, 1)
        lay_puls.addWidget(loadbtn, 1, 0, 1, 1)
        lay_puls.addWidget(libbox, 1, 1, 1, 1)

###################################################################
        # gate plot options
        win_gateplot = QWidget(self)
        lay_gateplot = QGridLayout(win_gateplot)
        gate_label = []
        gate_box = []
        channel_mapping_label = []
        channel_mapping_box = []
        gate_names = ['x','y']
        for i, gate_name in enumerate(gate_names):  # todo make dynamic with number of channels
            gate_label.append(QLabel(self))
            gate_label[i].setText('Gate_'+gate_name)
            gate_box.append(QLineEdit(self))
            gate_box[i].setText(str(0))
            channel_mapping_label.append(QLabel(self))
            channel_mapping_label[i].setText('Channel_'+gate_name)
            channel_mapping_box.append(QLineEdit(self))
            channel_mapping_box[i].setText(str(1+i))
            lay_gateplot.addWidget(gate_label[i], 0, i, 1, 1)
            lay_gateplot.addWidget(gate_box[i], 1, i, 1, 1)
            lay_gateplot.addWidget(channel_mapping_label[i], 0, i+2, 1, 1)
            lay_gateplot.addWidget(channel_mapping_box[i], 1, i+2, 1, 1)

        plotid_label = QLabel(self)
        plotid_label.setText('plot_id')
        plotid_box = QLineEdit(self)
        plotid_box.setText('0')
        lay_gateplot.addWidget(plotid_label, 2, 0, 1, 1)
        lay_gateplot.addWidget(plotid_box, 2, 1, 1, 1)


        #lay_puls.addWidget(win_gateplot, 1, 2, 1, 1)
##########################################################################

    
        #Add  or Remove a channel
        win_add_remove_channel = QWidget(self)
        lay_add_remove_channel = QGridLayout(win_add_remove_channel)
        whichch=QComboBox(self)
        for i in range(len(chbox)): 
            whichch.addItem('CH%d'%(i+1))
        addchbtn = QPushButton('Add Channel', self)
        addchbtn.clicked.connect(lambda state: table.addChannel(whichch.currentIndex()))

        remchbtn = QPushButton('Remove Channel', self)
        remchbtn.clicked.connect(lambda state: table.remChannel(str(whichch.currentText())))

        lay_add_remove_channel.addWidget(whichch, 0, 0, 0, 2)
        lay_add_remove_channel.addWidget(addchbtn, 1, 0)
        lay_add_remove_channel.addWidget(remchbtn, 1, 1)


        # Add or remove a pulse
        win_add_remove_pulse = QWidget(self)
        lay_add_remove_pulse = QGridLayout(win_add_remove_pulse)

        whichp = QLineEdit(self);whichp.setText('Set name')        
        addpbtn = QPushButton('Add Pulse', self)
        addpbtn.clicked.connect(lambda state: table.addPulse(whichp.text()))
        rempbtn = QPushButton('Remove Pulse', self)
        rempbtn.clicked.connect(lambda state: table.remPulse(str(whichp.text())))

        lay_add_remove_pulse.addWidget(whichp, 0, 0, 1, 2)
        lay_add_remove_pulse.addWidget(addpbtn, 1, 0)
        lay_add_remove_pulse.addWidget(rempbtn, 1, 1)

        # Rename a puls
        win_rename = QWidget(self)
        lay_rename = QGridLayout(win_rename)
        renamepbtn = QPushButton('Rename Pulse', self)
        oldpname = QLineEdit(self)
        oldpname.setText('Old name')
        newpname = QLineEdit(self)
        newpname.setText('New name')
        renamepbtn.clicked.connect(lambda state: table.renamePulse(oldpname,newpname))
        lay_rename.addWidget(renamepbtn, 0, 0, 1, 2)
        lay_rename.addWidget(oldpname, 1, 0)
        lay_rename.addWidget(newpname, 1, 1)

        
        #Correction D
        corrbtn = QPushButton('Correction D', self)
        corrbtn.clicked.connect(lambda state: self.correctionD(table))

        # Sequence and upload

        seqbtn = QPushButton('Upload Sequence', self)
        seqbtn.clicked.connect(lambda state:self.sequence())

        
        # setting up the layout of the main window
        #win_RT = QWidget(self)
        #lay_RT = QGridLayout(win_RT)
       # lay_RT.addWidget(win_puls,0,0)


        win_RM = QWidget(self)
        lay_RM = QVBoxLayout(win_RM)
        lay_RM.addWidget(win_add_remove_channel)
        lay_RM.addWidget(win_add_remove_pulse)
        lay_RM.addWidget(win_rename)
        lay_RM.addWidget(corrbtn)

        win_LB = QWidget(self)
        lay_LB = QGridLayout(win_LB)
        lay_LB.addWidget(win_divider,0,0)
        lay_LB.addWidget(win_AWGclock,1,0)

        win_MB = QWidget(self)
        lay_MB = QGridLayout(win_MB)
        lay_MB.addWidget(win_absmarkerbox, 0, 0)
        lay_MB.addWidget(win_absmarker, 1, 0)
        win_RB = QWidget(self)
        lay_RB = QGridLayout(win_RB)
        lay_RB.addWidget(seqbtn)

        mainlayout = QGridLayout()
        self.setLayout(mainlayout)

        mainlayout.setRowStretch(0, 1)
        mainlayout.setRowStretch(1, 10)
        mainlayout.setRowStretch(2, 1)
        
        mainlayout.setColumnStretch(0, 1)
        mainlayout.setColumnStretch(1, 10)
        mainlayout.setColumnStretch(2, 1)

        mainlayout.addWidget(win_puls,0,0)
        mainlayout.addWidget(win_gateplot,0,1)
        mainlayout.addWidget(table, 1, 0, 1, 2)
        mainlayout.addWidget(win_RM, 1, 2, 1, 1)
        mainlayout.addWidget(win_LB, 2, 0)
        mainlayout.addWidget(win_MB,2,1)
        mainlayout.addWidget(win_RB, 2, 2)


        self.show()
        win_absmarker.hide()
        
        

    
    
        
    def setDividers(self,chbox):
        for i in range(len(self.divch)):
            self.divch[i]=(float(chbox[i].text()));
        
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
            self._sequencebox.show() #exec_()
        else:
#            global_point = callWidget.mapToGlobal(point)
#            self._sequencebox.move(global_point - QtCore.QPoint(self.width(), 0))
             #self.SetForegroundWindow(self._sequencebox)
             self._sequencebox.show()
             #self._sequencebox.close()  # Close window.
             #self._sequencebox = None  # Discard reference.

    
    def close_application(self):

        choice = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if choice == QMessageBox.Yes:
            print('quit application')
            app.exec_()
        else:
            pass
    

    

    