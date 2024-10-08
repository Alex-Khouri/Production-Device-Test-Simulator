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

# ***** CONSTANTS *****
OUTPUT_FORMATS			= ["PDF", "PNG", "SVG"]
PDF						= "PDF"
PNG						= "PNG"
SVG						= "SVG"
BUFFER_SIZE				= 1024
MIN_PORT				= 1024
MAX_PORT				= 65535
MIN_INTERVAL			= 10		# Milliseconds
MAX_INTERVAL			= 10000		# Milliseconds
LIVE_DISPLAY_FREQENCY	= 100		# Milliseconds
MSG_TYPE_DISCOVERY		= "ID"
MSG_TYPE_STATUS			= "STATUS"
MSG_TYPE_TEST			= "TEST"
MSG_RESULT_STARTED		= "STARTED"
MSG_RESULT_STOPPED		= "STOPPED"
MSG_RESULT_ERROR		= "ERROR"
MSG_FULL_STARTED		= "TEST;RESULT=STARTED"
MSG_FULL_STOPPED		= "TEST;RESULT=STOPPED"
MSG_FULL_STOP			= "TEST;CMD=STOP;"

# ***** CANVAS *****
class DataCanvas(FigureCanvas):
	def __init__(self, parent=None, width=6, height=6, dpi=100):
		figure = Figure(figsize=(width, height), dpi=dpi)
		self.axes = figure.add_subplot(111)
		self.axes.set_xlabel("Time (milliseconds)")
		self.axes.set_ylabel("Level (mA/mV)")
		super(DataCanvas, self).__init__(figure)

# ***** WORKER *****
class RunTestWorker(QObject):
	progress = pyqtSignal(str)
	cancelled = pyqtSignal()
	finished = pyqtSignal()
	
	def __init__(self):
		super().__init__()
		self.IPDevice = "0.0.0.0"
		self.portDevice = 0
		self.portInterface = 0
		self.duration = 0	# Milliseconds
		self.interval = 0	# Milliseconds
		self.outputFormat = ""
		self.generateFile = False
		self.destination = ""
		self.canvas = None
		self.timestamps = []
		self.mvData = []
		self.maData = []
		self.displayTimestamps = []
		self.displaymvData = []
		self.displaymaData = []
		self.displayFrequencyFilter = 0
		self.displayFrameCounter = 0
		self.mvMin = 0
		self.mvMax = 0
		self.mvAvg = 0
		self.maMin = 0
		self.maMax = 0
		self.maAvg = 0
		self.messages = []
		self.displayCount = 0
		self.deviceName = ""
		self.UDPSocket = None
		self.running = False
		self.receivingMessages = False
		self.endedByDevice = False
		self.endedByInterface = False

	def updateParameters(self, IPDevice, portDevice, portInterface, duration, interval, outputFormat, \
							displayCount, generateFile, destination, canvas, timestamps, mvData, maData):
		self.IPDevice = IPDevice
		self.portDevice = portDevice
		self.portInterface = portInterface
		self.duration = duration * 1000		# Convert seconds to milliseconds
		self.interval = interval			# Milliseconds
		self.outputFormat = outputFormat
		self.displayCount = displayCount
		self.generateFile = generateFile
		self.destination = destination
		self.canvas = canvas
		self.timestamps = timestamps
		self.mvData = mvData
		self.maData = maData
		self.displayFrequencyFilter = max(LIVE_DISPLAY_FREQENCY / self.interval, 1)
	
	def safePath(self, path):
		return path.replace('\\', '_').replace('/', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('.', '_') # Remove problematic path characters

	def saveGraph(self):
		dateString = datetime.today().strftime("%Y-%m-%d")
		fileName = f"Production Test Data | {self.deviceName} | {dateString}"
		figure, axes = pyplot.subplots()
		pyplot.rcParams["figure.figsize"] = [8.00, 4.00]
		pyplot.rcParams["figure.autolayout"] = True
		pyplot.grid()
		pyplot.margins(x=0, y=0)
		pyplot.suptitle(fileName, fontsize=12)
		dataLine1 = f"Voltage Range: {self.mvMin}-{self.mvMax} (Average={round(self.mvAvg, 3)})"
		dataLine2 = f"Current Range: {self.maMin}-{self.maMax} (Average={round(self.maAvg, 3)})"
		pyplot.title(f"{dataLine1} .... {dataLine2}", fontsize=10)
		pyplot.xlabel("Time (seconds)")
		pyplot.ylabel("Level (mV/mA)")
		pyplot.plot(self.timestamps, self.mvData, 'b.-', linewidth=1, markersize=1, label="Voltage")
		pyplot.plot(self.timestamps, self.maData, 'r.-', linewidth=1, markersize=1, label="Current")
		pyplot.legend()
		pyplot.xlim(0, self.timestamps[-1])
		pyplot.ylim(0, max(max(self.mvData), max(self.maData)))
		figure.canvas.draw()
		xLabels = [label.get_text() for label in axes.get_xticklabels()]
		axes.set_xticklabels(xLabels, rotation=45, horizontalalignment='right')
		if self.outputFormat == PDF:
			PdfPages.savefig(f"{self.destination}/{self.safePath(fileName)}.pdf", bbox_inches='tight')
		elif self.outputFormat == PNG:
			pyplot.savefig(f"{self.destination}/{self.safePath(fileName)}.png", dpi=300, bbox_inches='tight')
		elif self.outputFormat == SVG:
			pyplot.savefig(f"{self.destination}/{self.safePath(fileName)}.svg", dpi=300, bbox_inches='tight')
		else:
			self.printOut("Invalid output format selected")
	
	def printOut(self, text):
		self.progress.emit(str(text))
	
	def interfaceCancel(self):
		self.running = False
		self.endedByInterface = True

	def deviceCancel(self):
		self.running = False
		self.endedByDevice = True

	def updateGraph(self):
		self.canvas.axes.cla()
		minVal = max(0, len(self.timestamps) - self.displayCount)
		self.displayTimestamps = self.timestamps[minVal:]
		self.displaymvData = self.mvData[minVal:]
		self.displaymaData = self.maData[minVal:]
		self.canvas.axes.plot(self.displayTimestamps, self.displaymvData, 'r', label="Voltage")
		self.canvas.axes.plot(self.displayTimestamps, self.displaymaData, 'b', label="Current")
		self.canvas.axes.set_xlabel("Time (seconds)")
		self.canvas.axes.set_ylabel("Level (mA/mV)")
		self.canvas.axes.legend(loc="upper right")
		self.canvas.draw()
	
	def clearTestData(self):
		self.timestamps.clear()
		self.mvData.clear()
		self.maData.clear()
		self.canvas.axes.cla()
	
	def sendMessage(self, message):
		dataToSend = bytes(message, "utf-8")
		sentBytes = self.UDPSocket.sendto(dataToSend, (self.IPDevice, self.portDevice))
	
	def processMessage(self, message):
		messageType = message.split(";")[0]
		if messageType == MSG_TYPE_DISCOVERY:
			self.printOut("Connection established!")
			model = message.split(";")[1].split("=")[1]
			serial = message.split(";")[2].split("=")[1]
			self.deviceName = f"{model} (#{serial})"
			outputMsg = f"TEST;CMD=START;DURATION={self.duration};RATE={self.interval};"
			self.printOut("Starting test...")
			self.sendMessage(outputMsg)
		elif messageType == MSG_TYPE_TEST:
			result = message.split(";")[1].split("=")[1]
			if (result == MSG_RESULT_STARTED):
				self.printOut("Receiving test data...")
			elif (result == MSG_RESULT_STOPPED):
				self.printOut("Test finishing...")
				self.deviceCancel()
				self.mvMin = min(self.mvData)
				self.mvMax = max(self.mvData)
				self.mvAvg = sum(self.mvData) / len(self.mvData)
				self.maMin = min(self.maData)
				self.maMax = max(self.maData)
				self.maAvg = sum(self.maData) / len(self.maData)
				self.printOut("----------------------------------------")
				self.printOut("Data Summary:")
				self.printOut(f"Voltage Range (mV): {self.mvMin}-{self.mvMax} (Average={round(self.mvAvg, 3)})")
				self.printOut(f"Current Range (mA): {self.maMin}-{self.maMax} (Average={round(self.maAvg, 3)})")
				self.printOut("----------------------------------------")
			elif (result == MSG_RESULT_ERROR):
				errorMessage = message.split(";")[2].split("=")[1]
				self.printOut(f"ERROR: {errorMessage}")
			else:
				self.printOut("ERROR: Test message received with unknown result")
		elif messageType == MSG_TYPE_STATUS:
			time = int(message.split(";")[1].split("=")[1])
			mv = int(message.split(";")[2].split("=")[1])
			ma = int(message.split(";")[3].split("=")[1])
			self.timestamps.append(time/1000)
			self.mvData.append(mv)
			self.maData.append(ma)
			if self.displayFrameCounter == 0:	# Limit PyQt redraw rate due to performance limitations (max=100ms)
				self.updateGraph()
			self.displayFrameCounter = (self.displayFrameCounter + 1) % self.displayFrequencyFilter
		else:
			self.printOut("ERROR: Unknown message type received")

	# Discard timeout errors generated while listening for messages, as the `UDPSocket.recv` function will
	# continue to run inside the loop until either a message is received, or the test is terminted by the
	# user pressing the 'Cancel' button.
	# The timeouts are used to make the `UDPSocket.recv` function periodically break from its execution,
	# which allows the `self.running` variable to be checked in order to determine whether the 'Cancel' button
	# has been pressed.
	def receiveMessages(self):
		self.receivingMessages = True
		if self.running:
			while True:
				data = None
				try:
					data = self.UDPSocket.recv(BUFFER_SIZE)
				except:
					pass	# Disregard timeout error messages
				if data or not self.running: break
			if data:
				message = data.decode('utf-8')
				self.processMessage(message)
		self.receivingMessages = False
	
	def getData(self):
		self.UDPSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.UDPSocket.bind((self.IPDevice, self.portInterface))
		self.UDPSocket.settimeout(1)
		self.printOut("Contacting device...")
		self.sendMessage(MSG_TYPE_DISCOVERY)
		while True:
			if not self.receivingMessages:
				self.receiveMessages()
			if not self.running:
				break

	def run(self):
		try:
			self.running = True
			self.timestamps.clear()
			self.mvData.clear()
			self.maData.clear()
			self.canvas.axes.cla()
			self.canvas.draw()
			self.getData()
			if self.endedByDevice:
				self.printOut("Test completed successfully!")
				if self.generateFile == True:
					self.saveGraph()
					self.printOut("Check 'Production Test Data' files for saved output.")
			elif self.endedByInterface:
				self.sendMessage(MSG_FULL_STOP)
				self.printOut("Test cancelled")
			else:
				self.printOut("ERROR: Test ended for unknown reason")
		except SystemExit as error:
			self.printOut(f"Program terminated with exit code: {error}")
		except KeyboardInterrupt as error:
			self.printOut(f"Program terminated by keyboard interrupt: {error}")
		except Exception as error:
			self.printOut(str(error))
		except:
			self.printOut("Test execution terminated due to error")
		finally:
			self.endedByDevice = False
			self.endedByInterface = False
			self.running = False
			self.clearTestData()
			self.finished.emit()

# ***** GUI *****
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

# ***** EXECUTION *****
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