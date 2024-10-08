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
import AppGUI
import DataCanvas
########################################

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