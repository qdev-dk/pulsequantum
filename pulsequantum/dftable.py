import pandas as pd
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem


class QTableWidgetDF(QTableWidget):
    """
    Extent the QTableWidget interact with Pandas
    """
    def __init__(self,parent=None):
        super(QTableWidgetDF, self).__init__(parent)
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
 

