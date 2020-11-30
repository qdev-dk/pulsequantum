import broadbean as bb
from PyQt5.QtCore import QCoreApplication,Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication, QWidget, QFrame,QMainWindow, QPushButton, QAction, QMessageBox, QLineEdit, QLabel, QSizePolicy
from PyQt5.QtWidgets import QCheckBox,QDialog,QTableWidget,QTableWidgetItem,QVBoxLayout,QHBoxLayout,QComboBox,QGridLayout
from broadbean.plotting import plotter

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
   
    #def loadElement(self,path):
     #   seq = bb.Sequence.init_from_json(path)
        
        
    def saveElement(self):
        return None

        
    def plotElement(self):
        plotter(self.gelem)
    

#############################################################################################





      
    