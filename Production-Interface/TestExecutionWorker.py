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
########################################

class TestExecutionWorker(QObject):
	progress = pyqtSignal(str)
	cancelled = pyqtSignal()
	finished = pyqtSignal()
	
	def __init__(self):
		super().__init__()
		self.__IPDevice = "0.0.0.0"
		self.__portDevice = 0
		self.__portInterface = 0
		self.__duration = 0	# Milliseconds
		self.__interval = 0	# Milliseconds
		self.__outputFormat = ""
		self.__generateFile = False
		self.__destination = ""
		self.__canvas = None
		self.__timestamps = []
		self.__mvData = []
		self.__maData = []
		self.__displayTimestamps = []
		self.__displaymvData = []
		self.__displaymaData = []
		self.__displayFrequencyFilter = 0
		self.__displayFrameCounter = 0
		self.__mvMin = 0
		self.__mvMax = 0
		self.__mvAvg = 0
		self.__maMin = 0
		self.__maMax = 0
		self.__maAvg = 0
		self.__messages = []
		self.__displayCount = 0
		self.__deviceName = ""
		self.__UDPSocket = None
		self.__running = False
		self.__receivingMessages = False
		self.__endedByDevice = False
		self.__endedByInterface = False

	def updateParameters(self, IPDevice, portDevice, portInterface, duration, interval, outputFormat, \
							displayCount, generateFile, destination, canvas, timestamps, mvData, maData):
		self.__IPDevice = IPDevice
		self.__portDevice = portDevice
		self.__portInterface = portInterface
		self.__duration = duration * 1000		# Convert seconds to milliseconds
		self.__interval = interval			# Milliseconds
		self.__outputFormat = outputFormat
		self.__displayCount = displayCount
		self.__generateFile = generateFile
		self.__destination = destination
		self.__canvas = canvas
		self.__timestamps = timestamps
		self.__mvData = mvData
		self.__maData = maData
		self.__displayFrequencyFilter = max(LIVE_DISPLAY_FREQENCY / self.__interval, 1)
	
	def __safePath(self, path):
		return path.replace('\\', '_').replace('/', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('.', '_') # Remove problematic path characters

	def __saveGraph(self):
		dateString = datetime.today().strftime("%Y-%m-%d")
		fileName = f"Production Test Data | {self.__deviceName} | {dateString}"
		figure, axes = pyplot.subplots()
		pyplot.rcParams["figure.figsize"] = [8.00, 4.00]
		pyplot.rcParams["figure.autolayout"] = True
		pyplot.grid()
		pyplot.margins(x=0, y=0)
		pyplot.suptitle(fileName, fontsize=12)
		dataLine1 = f"Voltage Range: {self.__mvMin}-{self.__mvMax} (Average={round(self.__mvAvg, 3)})"
		dataLine2 = f"Current Range: {self.__maMin}-{self.__maMax} (Average={round(self.__maAvg, 3)})"
		pyplot.title(f"{dataLine1} .... {dataLine2}", fontsize=10)
		pyplot.xlabel("Time (seconds)")
		pyplot.ylabel("Level (mV/mA)")
		pyplot.plot(self.__timestamps, self.__mvData, 'b.-', linewidth=1, markersize=1, label="Voltage")
		pyplot.plot(self.__timestamps, self.__maData, 'r.-', linewidth=1, markersize=1, label="Current")
		pyplot.legend()
		pyplot.xlim(0, self.__timestamps[-1])
		pyplot.ylim(0, max(max(self.__mvData), max(self.__maData)))
		figure.canvas.draw()
		xLabels = [label.get_text() for label in axes.get_xticklabels()]
		axes.set_xticklabels(xLabels, rotation=45, horizontalalignment='right')
		if self.__outputFormat == PDF:
			PdfPages.savefig(f"{self.__destination}/{self.__safePath(fileName)}.pdf", bbox_inches='tight')
		elif self.__outputFormat == PNG:
			pyplot.savefig(f"{self.__destination}/{self.__safePath(fileName)}.png", dpi=300, bbox_inches='tight')
		elif self.__outputFormat == SVG:
			pyplot.savefig(f"{self.__destination}/{self.__safePath(fileName)}.svg", dpi=300, bbox_inches='tight')
		else:
			self.__printOut("Invalid output format selected")
	
	def __printOut(self, text):
		self.__progress.emit(str(text))
	
	def interfaceCancel(self):
		self.__running = False
		self.__endedByInterface = True

	def __deviceCancel(self):
		self.__running = False
		self.__endedByDevice = True

	def __updateGraph(self):
		self.__canvas.axes.cla()
		minVal = max(0, len(self.__timestamps) - self.__displayCount)
		self.__displayTimestamps = self.__timestamps[minVal:]
		self.__displaymvData = self.__mvData[minVal:]
		self.__displaymaData = self.__maData[minVal:]
		self.__canvas.axes.plot(self.__displayTimestamps, self.__displaymvData, 'r', label="Voltage")
		self.__canvas.axes.plot(self.__displayTimestamps, self.__displaymaData, 'b', label="Current")
		self.__canvas.axes.set_xlabel("Time (seconds)")
		self.__canvas.axes.set_ylabel("Level (mA/mV)")
		self.__canvas.axes.legend(loc="upper right")
		self.__canvas.draw()
	
	def __clearTestData(self):
		self.__timestamps.clear()
		self.__mvData.clear()
		self.__maData.clear()
		self.__canvas.axes.cla()
	
	def __sendMessage(self, message):
		dataToSend = bytes(message, "utf-8")
		sentBytes = self.__UDPSocket.sendto(dataToSend, (self.__IPDevice, self.__portDevice))
	
	def __processMessage(self, message):
		messageType = message.split(";")[0]
		if messageType == MSG_TYPE_DISCOVERY:
			self.__printOut("Connection established!")
			model = message.split(";")[1].split("=")[1]
			serial = message.split(";")[2].split("=")[1]
			self.__deviceName = f"{model} (#{serial})"
			outputMsg = f"TEST;CMD=START;DURATION={self.__duration};RATE={self.__interval};"
			self.__printOut("Starting test...")
			self.__sendMessage(outputMsg)
		elif messageType == MSG_TYPE_TEST:
			result = message.split(";")[1].split("=")[1]
			if (result == MSG_RESULT_STARTED):
				self.__printOut("Receiving test data...")
			elif (result == MSG_RESULT_STOPPED):
				self.__printOut("Test finishing...")
				self.__deviceCancel()
				self.__mvMin = min(self.__mvData)
				self.__mvMax = max(self.__mvData)
				self.__mvAvg = sum(self.__mvData) / len(self.__mvData)
				self.__maMin = min(self.__maData)
				self.__maMax = max(self.__maData)
				self.__maAvg = sum(self.__maData) / len(self.__maData)
				self.__printOut("----------------------------------------")
				self.__printOut("Data Summary:")
				self.__printOut(f"Voltage Range (mV): {self.__mvMin}-{self.__mvMax} (Average={round(self.__mvAvg, 3)})")
				self.__printOut(f"Current Range (mA): {self.__maMin}-{self.__maMax} (Average={round(self.__maAvg, 3)})")
				self.__printOut("----------------------------------------")
			elif (result == MSG_RESULT_ERROR):
				errorMessage = message.split(";")[2].split("=")[1]
				self.__printOut(f"ERROR: {errorMessage}")
			else:
				self.__printOut("ERROR: Test message received with unknown result")
		elif messageType == MSG_TYPE_STATUS:
			time = int(message.split(";")[1].split("=")[1])
			mv = int(message.split(";")[2].split("=")[1])
			ma = int(message.split(";")[3].split("=")[1])
			self.__timestamps.append(time/1000)
			self.__mvData.append(mv)
			self.__maData.append(ma)
			if self.__displayFrameCounter == 0:	# Limit PyQt redraw rate due to performance limitations (max=100ms)
				self.__updateGraph()
			self.__displayFrameCounter = (self.__displayFrameCounter + 1) % self.__displayFrequencyFilter
		else:
			self.__printOut("ERROR: Unknown message type received")

	# Discard timeout errors generated while listening for messages, as the `UDPSocket.recv` function will
	# continue to run inside the loop until either a message is received, or the test is terminted by the
	# user pressing the 'Cancel' button.
	# The timeouts are used to make the `UDPSocket.recv` function periodically break from its execution,
	# which allows the `self.__running` variable to be checked in order to determine whether the 'Cancel' button
	# has been pressed.
	def __receiveMessages(self):
		self.__receivingMessages = True
		if self.__running:
			while True:
				data = None
				try:
					data = self.__UDPSocket.recv(BUFFER_SIZE)
				except:
					pass	# Disregard timeout error messages
				if data or not self.__running: break
			if data:
				message = data.decode('utf-8')
				self.__processMessage(message)
		self.__receivingMessages = False
	
	def __getData(self):
		self.__UDPSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.__UDPSocket.bind((self.__IPDevice, self.__portInterface))
		self.__UDPSocket.settimeout(1)
		self.__printOut("Contacting device...")
		self.__sendMessage(MSG_TYPE_DISCOVERY)
		while True:
			if not self.__receivingMessages:
				self.__receiveMessages()
			if not self.__running:
				break

	def run(self):
		try:
			self.__running = True
			self.__timestamps.clear()
			self.__mvData.clear()
			self.__maData.clear()
			self.__canvas.axes.cla()
			self.__canvas.draw()
			self.__getData()
			if self.__endedByDevice:
				self.__printOut("Test completed successfully!")
				if self.__generateFile == True:
					self.__saveGraph()
					self.__printOut("Check 'Production Test Data' files for saved output.")
			elif self.__endedByInterface:
				self.__sendMessage(MSG_FULL_STOP)
				self.__printOut("Test cancelled")
			else:
				self.__printOut("ERROR: Test ended for unknown reason")
		except SystemExit as error:
			self.__printOut(f"Program terminated with exit code: {error}")
		except KeyboardInterrupt as error:
			self.__printOut(f"Program terminated by keyboard interrupt: {error}")
		except Exception as error:
			self.__printOut(str(error))
		except:
			self.__printOut("Test execution terminated due to error")
		finally:
			self.__endedByDevice = False
			self.__endedByInterface = False
			self.__running = False
			self.__clearTestData()
			self.__finished.emit()