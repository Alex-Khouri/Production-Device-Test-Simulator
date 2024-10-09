########################################
# ***** IMPORTS *****
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
from DataCanvas import DataCanvas
from TestExecutionWorker import TestExecutionWorker
########################################

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)
		# GENERAL
		self.__IPDeviceRegex = QRegExp("((2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[0-9]?[0-9])\.){3}(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[0-9]?[0-9])")
		self.__layout = QGridLayout()
		self.__widget = QWidget()
		self.__widget.setLayout(self.__layout)
		self.__widget.setWindowTitle("Production Automation Interface")
		self.__widget.setMinimumSize(1300, 600)
		
		# DATA
		self.__timestamps = []
		self.__mvData = []
		self.__maData = []
		
		# COMPONENTS
		self.__buttonStartTest = QPushButton(text="Start")
		self.__buttonCancelTest = QPushButton(text="Cancel")
		self.__checkGenerateFile = QCheckBox("Generate File")
		self.__labelIPDevice = QLabel(text="IP Address (Device):")
		self.__labelPortDevice = QLabel(text="Port Number (Device):")
		self.__labelPortInterface = QLabel(text="Port Number (Interface):")
		self.__labelDuration = QLabel(text="Test Duration (secs):")
		self.__labelInterval = QLabel(text="Test Interval (millisecs):")
		self.__labelFormat = QLabel(text="Output File Format:")
		self.__labelDisplayCount = QLabel(text="Live Display Scale:")
		self.__lineIPDevice = QLineEdit()
		self.__lineIPDevice.setValidator(QRegExpValidator(self.__IPDeviceRegex))
		self.__linePortDevice = QLineEdit()
		self.__linePortDevice.setValidator(QIntValidator(MIN_PORT, MAX_PORT))
		self.__linePortDevice.setPlaceholderText(f"{MIN_PORT} - {MAX_PORT}")
		self.__linePortInterface = QLineEdit()
		self.__linePortInterface.setValidator(QIntValidator(MIN_PORT, MAX_PORT))
		self.__linePortInterface.setPlaceholderText(f"{MIN_PORT} - {MAX_PORT}")
		self.__lineDuration = QLineEdit()
		self.__lineDuration.setValidator(QIntValidator(bottom=1))
		self.__lineInterval = QLineEdit()
		self.__lineInterval.setValidator(QIntValidator(bottom=MIN_INTERVAL, top=MAX_INTERVAL))
		self.__lineInterval.setPlaceholderText(f"{MIN_INTERVAL} - {MAX_INTERVAL}")
		self.__boxFormat = QComboBox()
		self.__boxFormat.addItems(OUTPUT_FORMATS)
		self.__sliderDisplayCount = QSlider(Qt.Horizontal)
		self.__sliderDisplayCount.setTickPosition(QSlider.TicksBothSides)
		self.__sliderDisplayCount.setTickInterval(10)
		self.__sliderDisplayCount.setSingleStep(10)
		self.__sliderDisplayCount.setRange(10, 100)
		self.__sliderDisplayCount.setValue(50)
		self.__labelDisplayCountMin = QLabel(text="Small")
		self.__labelDisplayCountMax = QLabel(text="Large")
		self.__buttonOutputLocation = QPushButton(text="Output Location:")
		self.__lineOutputLocation = QLineEdit()
		self.__lineOutputLocation.setReadOnly(True)
		self.__labelInfo = QLabel(text="Info:")
		self.__textOutput = QTextEdit()
		self.__textOutput.setReadOnly(True)
		self.__textOutput.setStyleSheet("background-color: rgb(224,224,224);")
		self.__canvas = DataCanvas(self)
		
		# LAYOUT
		self.__layout.addWidget(self.__buttonStartTest,	 		0, 0, 1, 1)
		self.__layout.addWidget(self.__buttonCancelTest, 		1, 0, 1, 1)
		self.__layout.addWidget(self.__labelIPDevice,			0, 1, 1, 2, alignment=Qt.AlignRight)
		self.__layout.addWidget(self.__labelPortDevice, 		1, 1, 1, 2, alignment=Qt.AlignRight)
		self.__layout.addWidget(self.__labelPortInterface, 		2, 1, 1, 2, alignment=Qt.AlignRight)
		self.__layout.addWidget(self.__labelDuration,	 		3, 1, 1, 2, alignment=Qt.AlignRight)
		self.__layout.addWidget(self.__labelInterval,	 		4, 1, 1, 2, alignment=Qt.AlignRight)
		self.__layout.addWidget(self.__labelFormat,	 			5, 1, 1, 2, alignment=Qt.AlignRight)
		self.__layout.addWidget(self.__labelDisplayCount,	 	6, 1, 1, 2, alignment=Qt.AlignRight)
		self.__layout.addWidget(self.__lineIPDevice, 			0, 3, 1, 2)
		self.__layout.addWidget(self.__linePortDevice,		 	1, 3, 1, 2)
		self.__layout.addWidget(self.__linePortInterface,		2, 3, 1, 2)
		self.__layout.addWidget(self.__lineDuration,	 		3, 3, 1, 2)
		self.__layout.addWidget(self.__lineInterval,	 		4, 3, 1, 2)
		self.__layout.addWidget(self.__boxFormat,	 			5, 3, 1, 2)
		self.__layout.addWidget(self.__sliderDisplayCount,	 	6, 3, 1, 2)
		self.__layout.addWidget(self.__labelDisplayCountMin,	7, 3, 1, 1, alignment=Qt.AlignLeft)
		self.__layout.addWidget(self.__labelDisplayCountMax,	7, 4, 1, 1, alignment=Qt.AlignRight)
		self.__layout.addWidget(self.__checkGenerateFile,		8, 0, 1, 1)
		self.__layout.addWidget(self.__buttonOutputLocation,	9, 0, 1, 1)
		self.__layout.addWidget(self.__lineOutputLocation,		9, 1, 1, 4)
		self.__layout.addWidget(self.__labelInfo, 	 			10, 0, 1, 2)
		self.__layout.addWidget(self.__textOutput,		 		11, 0, 1, 5)
		self.__layout.addWidget(self.__canvas,					0, 5, 12, 1)
		
		# ACTIONS
		self.__buttonStartTest.clicked.connect(self.__buttonStartTestClick)
		self.__buttonCancelTest.clicked.connect(self.__buttonCancelTestClick)
		self.__checkGenerateFile.toggled.connect(self.__checkGenerateFileToggle)
		self.__lineIPDevice.textChanged.connect(self.__lineIPDeviceChanged)
		self.__linePortDevice.textChanged.connect(self.__linePortDeviceChanged)
		self.__linePortInterface.textChanged.connect(self.__linePortInterfaceChanged)
		self.__lineDuration.textChanged.connect(self.__lineDurationChanged)
		self.__lineInterval.textChanged.connect(self.__lineIntervalChanged)
		self.__boxFormat.currentIndexChanged.connect(self.__boxFormatChanged)
		self.__sliderDisplayCount.valueChanged.connect(self.__sliderDisplayCountChanged)
		self.__lineOutputLocation.textChanged.connect(self.__lineOutputLocationChanged)
		self.__buttonOutputLocation.clicked.connect(self.__buttonOutputLocationClick)
		
		# STATE
		self.__guiTestRunning = False
		self.__guiRefresh()
		
		# THREADS
		self.__thread = QThread()
		self.__worker = TestExecutionWorker()
		self.__worker.moveToThread(self.__thread)
		self.__thread.started.connect(self.__worker.run)
		self.__worker.finished.connect(self.__thread.quit)
		self.__worker.progress.connect(self.__printOut)
		self.__thread.finished.connect(self.__endTest)

	# Used to provide additional validation of integer fields, as QIntValidator doesn't limit upper values correctly
	def __manualFieldValidation(self):
		return int(self.__linePortDevice.text()) >= MIN_PORT and int(self.__linePortDevice.text()) <= MAX_PORT and \
			int(self.__linePortInterface.text()) >= MIN_PORT and int(self.__linePortInterface.text()) <= MAX_PORT and \
			int(self.__lineInterval.text()) >= MIN_INTERVAL and int(self.__lineInterval.text()) <= MAX_INTERVAL and \
			int(self.__lineDuration.text()) >= 1

	def __guiRefresh(self):
		if self.__guiTestRunning:
			self.__buttonStartTest.setDisabled(True)
			self.__buttonCancelTest.setDisabled(False)
			self.__checkGenerateFile.setDisabled(True)
			self.__lineIPDevice.setDisabled(True)
			self.__linePortDevice.setDisabled(True)
			self.__linePortInterface.setDisabled(True)
			self.__lineDuration.setDisabled(True)
			self.__lineInterval.setDisabled(True)
			self.__boxFormat.setDisabled(True)
			self.__sliderDisplayCount.setDisabled(True)
			self.__buttonOutputLocation.setDisabled(True)
			self.__lineOutputLocation.setDisabled(True)
		else:
			self.__buttonCancelTest.setDisabled(True)
			self.__checkGenerateFile.setDisabled(False)
			self.__lineIPDevice.setDisabled(False)
			self.__linePortDevice.setDisabled(False)
			self.__linePortInterface.setDisabled(False)
			self.__lineDuration.setDisabled(False)
			self.__lineInterval.setDisabled(False)
			self.__boxFormat.setDisabled(False)
			self.__sliderDisplayCount.setDisabled(False)
			if self.__IPDeviceRegex.exactMatch(self.__lineIPDevice.text()) and self.__linePortDevice.text() != "" and \
					self.__linePortInterface.text() != "" and self.__lineDuration.text() != "" and \
					self.__lineInterval.text() != "" and self.__manualFieldValidation() == True and \
					(not self.__checkGenerateFile.isChecked() or \
					(self.__checkGenerateFile.isChecked() and self.__lineOutputLocation.text() != "")):
				self.__buttonStartTest.setDisabled(False)
			else:
				self.__buttonStartTest.setDisabled(True)
			if self.__checkGenerateFile.isChecked():
				self.__boxFormat.setDisabled(False)
				self.__buttonOutputLocation.setDisabled(False)
				self.__lineOutputLocation.setDisabled(False)
			else:
				self.__boxFormat.setDisabled(True)
				self.__buttonOutputLocation.setDisabled(True)
				self.__lineOutputLocation.setDisabled(True)

	def __printOut(self, text):
		if text != "":
			self.__textOutput.append(text)

	def __startTest(self):
		self.__guiTestRunning = True
		self.__textOutput.clear()
		self.__guiRefresh()

	def __endTest(self):
		self.__guiTestRunning = False
		self.__guiRefresh()
		
	def __buttonStartTestClick(self):
		if (self.__linePortDevice.text() == self.__linePortInterface.text()):
			self.__printOut("ERROR: Interface port must be different from device port")
		else:
			self.__worker.updateParameters(self.__lineIPDevice.text(), int(self.__linePortDevice.text()), 
										int(self.__linePortInterface.text()), int(self.__lineDuration.text()), \
										int(self.__lineInterval.text()), self.__boxFormat.currentText(), \
										self.__sliderDisplayCount.value(), self.__checkGenerateFile.isChecked(), \
										self.__lineOutputLocation.text(), self.__canvas, self.__timestamps, \
										self.__mvData, self.__maData)
			self.__startTest()
			self.__thread.start()
 
	def __buttonCancelTestClick(self):
		self.__worker.interfaceCancel()

	def __checkGenerateFileToggle(self):
		self.__guiRefresh()
		
	def __lineIPDeviceChanged(self):
		self.__guiRefresh()
	
	def __linePortDeviceChanged(self):
		self.__guiRefresh()
	
	def __linePortInterfaceChanged(self):
		self.__guiRefresh()
	
	def __lineDurationChanged(self):
		self.__guiRefresh()
	
	def __lineIntervalChanged(self):
		self.__guiRefresh()
	
	def __boxFormatChanged(self):
		self.__guiRefresh()
	
	def __sliderDisplayCountChanged(self):
		self.__guiRefresh()
	
	def __buttonOutputLocationClick(self):
		self.__dialog = QFileDialog()
		self.__lineOutputLocation.setText(self.__dialog.getExistingDirectory())
	
	def __lineOutputLocationChanged(self):
		self.__guiRefresh()

	def getWidget(self):
		return self.__widget

# ***** EXECUTION *****
app = QtWidgets.QApplication(argv)
try:
	gui = MainWindow()
	widget = gui.getWidget()
	widget.show()
except SystemExit as error:
	gui.__printOut(f"Program terminated with exit code: {error}")
except KeyboardInterrupt as error:
	gui.__printOut(f"Program terminated by keyboard interrupt: {error}")
except Exception as error:
	gui.__printOut(str(error))
except:
	gui.__printOut("Error occurred during program execution")
finally:
	exit(app.exec())