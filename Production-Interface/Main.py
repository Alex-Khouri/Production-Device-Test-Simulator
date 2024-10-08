########################################
if __name__ == "__main__":
	import warnings
	warnings.filterwarnings("ignore")

	import matplotlib
	from matplotlib import pyplot
	from matplotlib.backends.backend_pdf import PdfPages
	from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
	from matplotlib.figure import Figure
	matplotlib.use('Qt5Agg')

	from PyQt5 import QtCore, QtWidgets
	from PyQt5.QtCore import *
	from PyQt5.QtGui import *
	from PyQt5.QtWidgets import *

	import socket
	from datetime import datetime
	from sys import argv
	from sys import exit
	from time import sleep
	from threading import Thread

	from Config import *
	from AppGUI import AppGUI
	from DataCanvas import DataCanvas
	from RunTestWorker import RunTestWorker

# TODO: Fix imports
########################################

app = QtWidgets.QApplication(argv)
try:
	gui = AppGUI()
	widget = gui.getWidget()
	widget.show()
except SystemExit as error:
	gui.printOut(f"Program terminated with exit code: {error}")
except KeyboardInterrupt as error:
	gui.printOut(f"Program terminated by keyboard interrupt: {error}")
except Exception as error:
	gui.printOut(str(error))
except:
	gui.printOut("Error occurred during program execution")
finally:
	exit(app.exec())