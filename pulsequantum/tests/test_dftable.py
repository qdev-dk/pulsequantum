import pandas as pd
from pulsequantum.dftable import QTableWidgetDF
import sys
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from numpy import random


nchans=2
nlines=3
test_data = random.randint(10, size=(nchans, nlines))
app = QApplication(sys.argv)
table = QTableWidgetDF()
table.setGeometry(50, 100, 1000, 400)
table.setColumnCount((nchans*3)+2)
table.setRowCount(nlines)

        # Set horizontal headers
h = nchans+1

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



trial_df = pd.DataFrame( 
                columns=test_headers,  # Fill columnets
                index=nlist  # Fill rows
                ) 

for i, row in enumerate(nlist):
    for j, col in enumerate(test_headers):
        trial_df.loc[row, col] = str(test_data[j, i])

tmp_df = table.table_to_df()
print(tmp_df.equals(trial_df))

tmp_table = QTableWidgetItem.df_to_table(tmp_df)

tmp2_df = tmp_table.table_to_df()

print(table == table.update_table_from_df(tmp2_df))
print(tmp_df.equals(tmp2_df))