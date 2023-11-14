from PySide6.QtWidgets import QApplication

from fancyfolders.ui.screens.mainwindow import MainWindow

##############################
# START APPLICATION
##############################

app = QApplication()

window = MainWindow()
window.show()

app.exec()
