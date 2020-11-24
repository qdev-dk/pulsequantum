import broadbean as bb
from PyQt5.QtCore import QCoreApplication,Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication, QWidget, QFrame,QMainWindow, QPushButton, QAction, QMessageBox, QLineEdit, QLabel, QSizePolicy
from PyQt5.QtWidgets import QCheckBox,QDialog,QTableWidget,QTableWidgetItem,QVBoxLayout,QHBoxLayout,QComboBox,QGridLayout
from broadbean.plotting import plotter

nlines=3;
nchans=2;

ramp = bb.PulseAtoms.ramp; #Globally defined ramp, element, and sequence
gelem = bb.Element();
gseq = bb.Sequence();

divch1=11.5;divch2=11.75;divch3=11.7;divch4=1; #Hardcoded channel dividers
divch=[divch1,divch2,divch3,divch4];

corrDflag=0; #Global flag: Is correction D pulse already defined in the pulse table?

class Gelem():
    def __init__(self, AWG=None, gelem=None):
        self.gelem = bb.Element()
        self.awgclock=1.2e9


    def generateElement(self,table):
        #Make element from pulse table
        self.gelem= bb.Element();
        h=int((table.columnCount()-2)/3);
        prevlvl=0;
        v=table.rowCount();
        for col in range(2,h+2):
            chno=int(table.horizontalHeaderItem(col).text()[2]);
            gp = bb.BluePrint()
            gp.setSR(self.awgclock);
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
            self.gelem.addBluePrint(chno, gp);
            h=h+2;
        self.gelem.validateDurations();


    #############################################################################################
# The correction D pulse keeps the centre of gravity of the pulse at the DC value (voltage
# seen by the same when there is no pulsing. Not always used or needed.
#############################################################################################
    def correctionD(self,table):
        global corrDflag;
        if corrDflag==1:
            print("Correction D pulse already exists.")
            return;
        corrDflag=1;
        awgclockinus=self.awgclock/1e6;
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
            gelem.addArray(chno[i],wfm,self.awgclock,**kwargs);
       # Generate the pulse table    
        
    def plotElement(self):
        plotter(self.gelem);
    

#############################################################################################

    def saveElement(self):
        return None




 #############################################################################################
# A few hardcoded pulses that we use over and over, and some placeholder buttons. should be replaced by json libery
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
        
    def Dephasing(self,table):
        table.setColumnCount((2*3)+2)
        table.setRowCount(5)
        
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
        nlist=["dummy","Prepare","Prepare*","Separate","Measure"];
        for i in range(5):
            table.setVerticalHeaderItem(i, QTableWidgetItem(nlist[i]));
            
        #Set table items to zero initially    
        for column in range(table.columnCount()):
            for row in range(table.rowCount()):
                table.setItem(row,column, QTableWidgetItem("0"));
        
        #Times
        table.setItem(0,0, QTableWidgetItem("5000"));
        table.setItem(1,0, QTableWidgetItem("200"));
        table.setItem(2,0, QTableWidgetItem("25"));
        table.setItem(3,0, QTableWidgetItem("2000"));
        table.setItem(4,0, QTableWidgetItem("10"));
        # table.setItem(5,0, QTableWidgetItem("0.5"));
        # table.setItem(6,0, QTableWidgetItem("10"));
        # table.setItem(7,0, QTableWidgetItem("0.01"));
        
        #Markers
        table.setItem(4,4, QTableWidgetItem("1"));
        # table.setItem(3,4, QTableWidgetItem("1"));
        
        #Pulses: (n,m): n - row from 0, m - clmn from 0
        #Prepare 
        table.setItem(1,2, QTableWidgetItem("-4.077"));
        table.setItem(1,3, QTableWidgetItem("4.5322"));
        #Prepare* 
        table.setItem(2,2, QTableWidgetItem("0"));
        table.setItem(2,3, QTableWidgetItem("0"));
        #Separate 
        table.setItem(3,2, QTableWidgetItem("6.604"));
        table.setItem(3,3, QTableWidgetItem("-3.0405"));
        #Measure 
        table.setItem(4,2, QTableWidgetItem("0"));
        table.setItem(4,3, QTableWidgetItem("0"));        
    