import pandas as pd
from pulsequantum.dftable import QTableWidgetDF
import sys
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from numpy import random

def test_dftable():
    """
    Test for the class dftable
    """

    # setting uo the table

    app = QApplication(sys.argv)
    table = QTableWidgetDF()
    table.setGeometry(50, 100, 1000, 400)
    # Set horizontal headers
    test_headers = ['a', 'b', 'c', 'd']
    nlist = ["load", "unload", "measure"]
    colnr = len(test_headers)
    rownr = len(nlist)
    test_data = random.randint(10, size=(colnr, rownr))
    table.setColumnCount(colnr)
    table.setRowCount(rownr)
    # Set horizontal headers
    for i, col in enumerate(test_headers):
        table.setHorizontalHeaderItem(i, QTableWidgetItem(col))
    # Set vertical headers
    for i, row in enumerate(nlist):
        table.setVerticalHeaderItem(i, QTableWidgetItem(nlist[i]))

    # Set table items to zero initially
    for col in range(colnr):
        for row in range(rownr):
            table.setItem(row, col, QTableWidgetItem(str(test_data[col, row])))


    # setting up the dataframe 
    trial_df = pd.DataFrame( 
                    columns=test_headers,  # Fill columnets
                    index=nlist  # Fill rows
                    ) 

    for i, row in enumerate(nlist):
        for j, col in enumerate(test_headers):
            trial_df.loc[row, col] = str(test_data[j, i])


    tmp_df = table.table_to_df()
    assert tmp_df.equals(trial_df)

    tmp_table = QTableWidgetDF.df_to_table(tmp_df)
    tmp2_df = tmp_table.table_to_df()
    assert tmp2_df.equals(trial_df)

    trial2_df = trial_df*2
    table.update_table_from_df(trial2_df)
    assert trial2_df.equals(table.table_to_df())




test_dftable()