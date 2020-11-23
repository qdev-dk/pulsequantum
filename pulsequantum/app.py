import sys
from PyQt5.QtWidgets import QApplication
from  mainwindow import pulsetable





def run():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    
    app.aboutToQuit.connect(app.deleteLater)
    pulsetable(AWG = None)
    app.exec_()    
if __name__ == "__main__": 
    run()