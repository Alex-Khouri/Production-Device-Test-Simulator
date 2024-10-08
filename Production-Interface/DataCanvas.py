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
	import AppGUI
	import DataCanvas
	import RunTestWorker
########################################

class DataCanvas(FigureCanvas):
	def __init__(self, parent=None, width=6, height=6, dpi=100):
		figure = Figure(figsize=(width, height), dpi=dpi)
		self.axes = figure.add_subplot(111)
		self.axes.set_xlabel("Time (milliseconds)")
		self.axes.set_ylabel("Level (mA/mV)")
		super(DataCanvas, self).__init__(figure)