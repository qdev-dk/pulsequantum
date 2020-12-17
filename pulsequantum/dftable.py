import pandas as pd
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem


class QTableWidgetDF(QTableWidget):
    """
    Extent the QTableWidget interact with Pandas
    """
    def __init__(self,parent=None, nchans=2, nlines=3):
        super(QTableWidgetDF, self).__init__(parent)
        self.nchans = nchans
        self.nlines = nlines
    #def __init__(self):
    #    super().__init__()

    def table_to_df(self):
        """

        Returns the table as a Pandas df
        """
        number_of_rows = self.rowCount()
        number_of_columns = self.columnCount()
        columns_headers = []
        for i in range(number_of_columns):
            columns_headers.append(self.horizontalHeaderItem(i).text())
        row_headers = []
        for i in range(number_of_rows):
            row_headers.append(self.verticalHeaderItem(i).text())

        tmp_df = pd.DataFrame( 
                columns=columns_headers,  # Fill columnets
                index=row_headers  # Fill rows
                ) 

        for i, row in enumerate(row_headers):
            for j, col in enumerate(columns_headers):
                tmp_df.loc[row, col] = self.item(i, j).text()
        return tmp_df

    @classmethod    
    def df_to_table(cls, df: pd.DataFrame):
        """
        Init a QTableWidget from a pd.DataFrame
        """
        columns_headers = list(df.columns) 
        row_headers = list(df.index)
        table = cls()
        table.setGeometry(50, 100, 1000, 400)
        table.setColumnCount(len(columns_headers))
        table.setRowCount(len(row_headers))
        for i, row in enumerate(row_headers):
            table.setVerticalHeaderItem(i, QTableWidgetItem(row_headers[i]))
            for j, col in enumerate(columns_headers):
                if i == 0:
                    table.setHorizontalHeaderItem(j, QTableWidgetItem(columns_headers[j]))
                table.setItem(i, j, QTableWidgetItem(df.loc[row, col]))

        return table

    def update_table_from_df(self, df):
        """

        Update QTableWidget from a pd.DataFrame
        """
        columns_headers = list(df.columns)
        row_headers = list(df.index)
        self.setColumnCount(len(columns_headers))
        self.setRowCount(len(row_headers))
        for i, row in enumerate(row_headers):
            self.setVerticalHeaderItem(i, QTableWidgetItem(row_headers[i]))
            for j, col in enumerate(columns_headers):
                if i == 0:
                    self.setHorizontalHeaderItem(j, QTableWidgetItem(columns_headers[j]))
                self.setItem(i, j, QTableWidgetItem(df.loc[row, col]))

    def addChannel(self, index):
        self.nchans=self.nchans+1
        ch=[1,2,3,4]
        chno=ch[index]
        n=self.columnCount()
        nchan=int((self.columnCount()-2)/3)
        self.insertColumn(nchan+2);
        self.insertColumn(n+1);
        self.insertColumn(n+2);
        self.setHorizontalHeaderItem(nchan+2, QTableWidgetItem("CH%d"%chno));
        self.setHorizontalHeaderItem(n+1, QTableWidgetItem("CH%dM1"%chno));
        self.setHorizontalHeaderItem(n+2, QTableWidgetItem("CH%dM2"%chno));
        for row in range(self.rowCount()):
            self.setItem(row,nchan+2, QTableWidgetItem("0"));
            self.setItem(row,n+1, QTableWidgetItem("0"));
            self.setItem(row,n+2, QTableWidgetItem("0"));
    
    # TODO fix this function
    def remChannel(self, channel_name): 
        self.nchans=self.nchans-1;
        n=self.columnCount();
        n=n-1-2;
        for i in range(n):
            if str(self.horizontalHeaderItem(i).text())==channel_name:
               self.removeColumn(i);
            if str(self.horizontalHeaderItem(i).text())==channel_name+"M1":    
                self.removeColumn(i);
            if str(self.horizontalHeaderItem(i).text())==channel_name+"M2":
               self.removeColumn(i);
    
    def addPulse(self, pulse_name, i=-1):
        self.nlines=self.nlines+1;
        if i==-1:
            n=self.rowCount();
        else:
            n=i;
        self.insertRow(n);
        self.setVerticalHeaderItem(n,QTableWidgetItem(pulse_name));
        for column in range(self.columnCount()):
            if column==0:
                self.setItem(n,column, QTableWidgetItem("1"));
            else:
                self.setItem(n,column, QTableWidgetItem("0"));
    
    def remPulse(self, pulse_name):
        self.nlines=self.nlines-1;
        for n in range(self.rowCount()):
            if str(self.verticalHeaderItem(n).text())==pulse_name:
                if pulse_name=='corrD':
                    self.corrDflag=0;
                self.removeRow(n);
    
    def renamePulse(self, oldpname,newpname):
        for n in range(self.rowCount()):
            if self.verticalHeaderItem(n).text()==oldpname.text():
                self.setVerticalHeaderItem(n,QTableWidgetItem(newpname.text()));
 

