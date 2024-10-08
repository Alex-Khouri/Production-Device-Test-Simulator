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

class AppGUI(QtWidgets.QMainWindow):
	def __init__(self, *args, **kwargs):
		super(AppGUI, self).__init__(*args, **kwargs)
		# GENERAL
		self.IPDeviceRegex = QRegExp("((2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[0-9]?[0-9])\.){3}(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[0-9]?[0-9])")
		self.layout = QGridLayout()
		self.widget = QWidget()
		self.widget.setLayout(self.layout)
		self.widget.setWindowTitle("Production Automation Interface")
		self.widget.setMinimumSize(1300, 600)
		
		# DATA
		self.timestamps = []
		self.mvData = []
		self.maData = []
		
		# COMPONENTS
		self.buttonStartTest = QPushButton(text="Start")
		self.buttonCancelTest = QPushButton(text="Cancel")
		self.checkGenerateFile = QCheckBox("Generate File")
		self.labelIPDevice = QLabel(text="IP Address (Device):")
		self.labelPortDevice = QLabel(text="Port Number (Device):")
		self.labelPortInterface = QLabel(text="Port Number (Interface):")
		self.labelDuration = QLabel(text="Test Duration (secs):")
		self.labelInterval = QLabel(text="Test Interval (millisecs):")
		self.labelFormat = QLabel(text="Output File Format:")
		self.labelDisplayCount = QLabel(text="Live Display Scale:")
		self.lineIPDevice = QLineEdit()
		self.lineIPDevice.setValidator(QRegExpValidator(self.IPDeviceRegex))
		self.linePortDevice = QLineEdit()
		self.linePortDevice.setValidator(QIntValidator(MIN_PORT, MAX_PORT))
		self.linePortDevice.setPlaceholderText(f"{MIN_PORT} - {MAX_PORT}")
		self.linePortInterface = QLineEdit()
		self.linePortInterface.setValidator(QIntValidator(MIN_PORT, MAX_PORT))
		self.linePortInterface.setPlaceholderText(f"{MIN_PORT} - {MAX_PORT}")
		self.lineDuration = QLineEdit()
		self.lineDuration.setValidator(QIntValidator(bottom=1))
		self.lineInterval = QLineEdit()
		self.lineInterval.setValidator(QIntValidator(bottom=MIN_INTERVAL, top=MAX_INTERVAL))
		self.lineInterval.setPlaceholderText(f"{MIN_INTERVAL} - {MAX_INTERVAL}")
		self.boxFormat = QComboBox()
		self.boxFormat.addItems(OUTPUT_FORMATS)
		self.sliderDisplayCount = QSlider(Qt.Horizontal)
		self.sliderDisplayCount.setTickPosition(QSlider.TicksBothSides)
		self.sliderDisplayCount.setTickInterval(10)
		self.sliderDisplayCount.setSingleStep(10)
		self.sliderDisplayCount.setRange(10, 100)
		self.sliderDisplayCount.setValue(50)
		self.labelDisplayCountMin = QLabel(text="Small")
		self.labelDisplayCountMax = QLabel(text="Large")
		self.buttonOutputLocation = QPushButton(text="Output Location:")
		self.lineOutputLocation = QLineEdit()
		self.lineOutputLocation.setReadOnly(True)
		self.labelInfo = QLabel(text="Info:")
		self.textOutput = QTextEdit()
		self.textOutput.setReadOnly(True)
		self.textOutput.setStyleSheet("background-color: rgb(224,224,224);")
		self.canvas = DataCanvas(self)
		
		# LAYOUT
		self.layout.addWidget(self.buttonStartTest,	 		0, 0, 1, 1)
		self.layout.addWidget(self.buttonCancelTest, 		1, 0, 1, 1)
		self.layout.addWidget(self.labelIPDevice,			0, 1, 1, 2, alignment=Qt.AlignRight)
		self.layout.addWidget(self.labelPortDevice, 		1, 1, 1, 2, alignment=Qt.AlignRight)
		self.layout.addWidget(self.labelPortInterface, 		2, 1, 1, 2, alignment=Qt.AlignRight)
		self.layout.addWidget(self.labelDuration,	 		3, 1, 1, 2, alignment=Qt.AlignRight)
		self.layout.addWidget(self.labelInterval,	 		4, 1, 1, 2, alignment=Qt.AlignRight)
		self.layout.addWidget(self.labelFormat,	 			5, 1, 1, 2, alignment=Qt.AlignRight)
		self.layout.addWidget(self.labelDisplayCount,	 	6, 1, 1, 2, alignment=Qt.AlignRight)
		self.layout.addWidget(self.lineIPDevice, 			0, 3, 1, 2)
		self.layout.addWidget(self.linePortDevice,		 	1, 3, 1, 2)
		self.layout.addWidget(self.linePortInterface,		2, 3, 1, 2)
		self.layout.addWidget(self.lineDuration,	 		3, 3, 1, 2)
		self.layout.addWidget(self.lineInterval,	 		4, 3, 1, 2)
		self.layout.addWidget(self.boxFormat,	 			5, 3, 1, 2)
		self.layout.addWidget(self.sliderDisplayCount,	 	6, 3, 1, 2)
		self.layout.addWidget(self.labelDisplayCountMin,	7, 3, 1, 1, alignment=Qt.AlignLeft)
		self.layout.addWidget(self.labelDisplayCountMax,	7, 4, 1, 1, alignment=Qt.AlignRight)
		self.layout.addWidget(self.checkGenerateFile,		8, 0, 1, 1)
		self.layout.addWidget(self.buttonOutputLocation,	9, 0, 1, 1)
		self.layout.addWidget(self.lineOutputLocation,		9, 1, 1, 4)
		self.layout.addWidget(self.labelInfo, 	 			10, 0, 1, 2)
		self.layout.addWidget(self.textOutput,		 		11, 0, 1, 5)
		self.layout.addWidget(self.canvas,					0, 5, 12, 1)
		
		# ACTIONS
		self.buttonStartTest.clicked.connect(self.buttonStartTestClick)
		self.buttonCancelTest.clicked.connect(self.buttonCancelTestClick)
		self.checkGenerateFile.toggled.connect(self.checkGenerateFileToggle)
		self.lineIPDevice.textChanged.connect(self.lineIPDeviceChanged)
		self.linePortDevice.textChanged.connect(self.linePortDeviceChanged)
		self.linePortInterface.textChanged.connect(self.linePortInterfaceChanged)
		self.lineDuration.textChanged.connect(self.lineDurationChanged)
		self.lineInterval.textChanged.connect(self.lineIntervalChanged)
		self.boxFormat.currentIndexChanged.connect(self.boxFormatChanged)
		self.sliderDisplayCount.valueChanged.connect(self.sliderDisplayCountChanged)
		self.lineOutputLocation.textChanged.connect(self.lineOutputLocationChanged)
		self.buttonOutputLocation.clicked.connect(self.buttonOutputLocationClick)
		
		# STATE
		self.guiTestRunning = False
		self.guiRefresh()
		
		# THREADS
		self.thread = QThread()
		self.worker = RunTestWorker()
		self.worker.moveToThread(self.thread)
		self.thread.started.connect(self.worker.run)
		self.worker.finished.connect(self.thread.quit)
		self.worker.progress.connect(self.printOut)
		self.thread.finished.connect(self.endTest)

	# Used to provide additional validation of integer fields, as QIntValidator doesn't limit upper values correctly
	def manualFieldValidation(self):
		return int(self.linePortDevice.text()) >= MIN_PORT and int(self.linePortDevice.text()) <= MAX_PORT and \
			int(self.linePortInterface.text()) >= MIN_PORT and int(self.linePortInterface.text()) <= MAX_PORT and \
			int(self.lineInterval.text()) >= MIN_INTERVAL and int(self.lineInterval.text()) <= MAX_INTERVAL and \
			int(self.lineDuration.text()) >= 1

	def guiRefresh(self):
		if self.guiTestRunning:
			self.buttonStartTest.setDisabled(True)
			self.buttonCancelTest.setDisabled(False)
			self.checkGenerateFile.setDisabled(True)
			self.lineIPDevice.setDisabled(True)
			self.linePortDevice.setDisabled(True)
			self.linePortInterface.setDisabled(True)
			self.lineDuration.setDisabled(True)
			self.lineInterval.setDisabled(True)
			self.boxFormat.setDisabled(True)
			self.sliderDisplayCount.setDisabled(True)
			self.buttonOutputLocation.setDisabled(True)
			self.lineOutputLocation.setDisabled(True)
		else:
			self.buttonCancelTest.setDisabled(True)
			self.checkGenerateFile.setDisabled(False)
			self.lineIPDevice.setDisabled(False)
			self.linePortDevice.setDisabled(False)
			self.linePortInterface.setDisabled(False)
			self.lineDuration.setDisabled(False)
			self.lineInterval.setDisabled(False)
			self.boxFormat.setDisabled(False)
			self.sliderDisplayCount.setDisabled(False)
			if self.IPDeviceRegex.exactMatch(self.lineIPDevice.text()) and self.linePortDevice.text() != "" and \
					self.linePortInterface.text() != "" and self.lineDuration.text() != "" and \
					self.lineInterval.text() != "" and self.manualFieldValidation() == True and \
					(not self.checkGenerateFile.isChecked() or \
					(self.checkGenerateFile.isChecked() and self.lineOutputLocation.text() != "")):
				self.buttonStartTest.setDisabled(False)
			else:
				self.buttonStartTest.setDisabled(True)
			if self.checkGenerateFile.isChecked():
				self.boxFormat.setDisabled(False)
				self.buttonOutputLocation.setDisabled(False)
				self.lineOutputLocation.setDisabled(False)
			else:
				self.boxFormat.setDisabled(True)
				self.buttonOutputLocation.setDisabled(True)
				self.lineOutputLocation.setDisabled(True)

	def printOut(self, text):
		if text != "":
			self.textOutput.append(text)

	def startTest(self):
		self.guiTestRunning = True
		self.textOutput.clear()
		self.guiRefresh()

	def endTest(self):
		self.guiTestRunning = False
		self.guiRefresh()
		
	def buttonStartTestClick(self):
		if (self.linePortDevice.text() == self.linePortInterface.text()):
			self.printOut("ERROR: Interface port must be different from device port")
		else:
			self.worker.updateParameters(self.lineIPDevice.text(), int(self.linePortDevice.text()), 
										int(self.linePortInterface.text()), int(self.lineDuration.text()), \
										int(self.lineInterval.text()), self.boxFormat.currentText(), \
										self.sliderDisplayCount.value(), self.checkGenerateFile.isChecked(), \
										self.lineOutputLocation.text(), self.canvas, self.timestamps, \
										self.mvData, self.maData)
			self.startTest()
			self.thread.start()
 
	def buttonCancelTestClick(self):
		self.worker.interfaceCancel()

	def checkGenerateFileToggle(self):
		self.guiRefresh()
		
	def lineIPDeviceChanged(self):
		self.guiRefresh()
	
	def linePortDeviceChanged(self):
		self.guiRefresh()
	
	def linePortInterfaceChanged(self):
		self.guiRefresh()
	
	def lineDurationChanged(self):
		self.guiRefresh()
	
	def lineIntervalChanged(self):
		self.guiRefresh()
	
	def boxFormatChanged(self):
		self.guiRefresh()
	
	def sliderDisplayCountChanged(self):
		self.guiRefresh()
	
	def buttonOutputLocationClick(self):
		self.dialog = QFileDialog()
		self.lineOutputLocation.setText(self.dialog.getExistingDirectory())
	
	def lineOutputLocationChanged(self):
		self.guiRefresh()

	def getWidget(self):
		return self.widget