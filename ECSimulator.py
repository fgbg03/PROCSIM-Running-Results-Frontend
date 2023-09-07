import sys

from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg

from SimMenu import SimMenu
from ResultScreen import DefaultGraphs
from ProcsimRun import ProcsimRun, InfoScreen
from Settings import Settings
from Util import Util

from os.path import isfile, isdir
from os import listdir

class ECSimulator(qw.QMainWindow):
	def __init__(self, jsonPath):
		"""
		Screen pertaining to energy community simulation

		Args:
			jsonPath: path to the json of the community
		"""
		super().__init__()

		self.jsonPath = jsonPath

		self.goToSimMenu()

	closeOpenGraphs = qc.Signal()

	def goToResults(self, days = None, pj = None):
		"""
		Sets Result Screen as central widget

		Args:
			days: number of days in the simulation we're checking the results of
			pj: path to the community's json file
		"""
		if pj is None: # gets the json if it's not given as an argument
			pj = self.jsonPath
			if pj is None: # warns none was selected
				self.warnNoCommunity()
				return

		if days == None: # gets the days if it's not given as an argument
			days = self.centralWidget().getDays()

		# building dictionary with useful paths to be used in the showing of results
		paths = {}
		jsonName = Util.fileName(pj)
		paths["json"] = pj
		x, paths["minute"], y, z = Settings.getOutputPaths(jsonName, days)
		
		testPath = paths["minute"]
		if not isdir(testPath) or len(listdir(testPath)) == 0:
			self.warnNotSimulated()
			return

		graphScreen = DefaultGraphs(paths)
		graphScreen.goBack.connect(self.goToSimMenu)
		self.closeOpenGraphs.connect(graphScreen.closeGraphs)
		self.setCentralWidget(graphScreen)

	def goToSimMenu(self):
		"""
		Sets Sim Menu as central widget
		"""
		simMenu = SimMenu()
		simMenu.loadOptions()
		simMenu.btnRes.clicked.connect(lambda:self.goToResults())
		simMenu.btnSim.clicked.connect(self.simulate)
		self.setCentralWidget(simMenu)

	def warnNoCommunity(self):
		"""
		Shows a message box warning no community's been selected
		"""
		errorPopup = qw.QMessageBox()
		errorPopup.setWindowTitle("Warning")
		errorPopup.setText("Please select a community before proceding.")
		errorPopup.exec()

	def warnNotSimulated(self):
		"""
		Shows a message box warning no community's been selected
		"""
		errorPopup = qw.QMessageBox()
		errorPopup.setWindowTitle("Warning")
		errorPopup.setText("No simulation found.")
		errorPopup.exec()

	def simulate(self):
		"""
		Simulate Energy Community
		"""
		def cancel(checked):
			"""
			Cancel the simulation when possible

			Args:
				checked: if the cancel button is checked
			"""

			#make it so it doesn't repeat if it already's been cancelled
			if not checked:
				info.btnCancel.setChecked(True)
				return
			if info.cancelled:
				return
			print("Cancelling")
			info.setCancelled()
			self.worker.cancel = True
			qc.QObject.disconnect(logSimulationConnection)
			qc.QObject.disconnect(endGoToConnection)
			self.thread.finished.connect(self.goToSimMenu)
			self.thread.finished.connect(lambda:print("Cancelled"))

		def error(exception):
			"""
			Show error message from the simulation

			Args:
				exception: exception raised during simulation
			"""
			print("Error\n"+str(exception))
			qc.QObject.disconnect(logSimulationConnection)
			qc.QObject.disconnect(endGoToConnection)
			self.thread.finished.connect(self.goToSimMenu)
			errorPopup = qw.QMessageBox()
			errorPopup.setWindowTitle("Something went wrong")
			errorPopup.setText("An error occurred during simulation. Try checking your internet connection or the community file's integrity.")
			if "period_end" in str(exception):
				exception = "Problem accessing solar information"
			errorPopup.setInformativeText("Error details:\n"+str(exception))
			errorPopup.exec()
		
		pj = self.jsonPath
		if pj is None: # check if a community was selected
			self.warnNoCommunity()
			return

		self.centralWidget().saveOptions()

		# get needed values for simulation
		jsonName = Util.fileName(pj)
		skipCg = self.centralWidget().skipCg()
		localPV = "" if not self.centralWidget().useLocalPV() else Settings.getPVData()
		days = self.centralWidget().getDays()
		ps, pm, p1o, p2o = Settings.getOutputPaths(jsonName, days)

		# set simulation information screen
		info = InfoScreen("Simulating", "Preparing classes")
		self.setCentralWidget(info)

		# prepare thread for running simulation
		self.thread = qc.QThread()
		self.thread.setTerminationEnabled()
		self.worker = ProcsimRun(simulate = True, skipCg=skipCg, localPV=localPV, days = days, \
			path_steps_seconds = ps, path_steps_minutes = pm, community_file = pj)

		#enable cancelling of the simulation
		info.btnCancel.toggled.connect(cancel)

		#move to thread
		self.worker.moveToThread(self.thread)
		#connect to start
		self.thread.started.connect(self.worker.run)
		#connect to worker finished
		self.worker.finished.connect(self.thread.quit)
		self.worker.finished.connect(self.worker.deleteLater)
		#connect to thread finished
		self.thread.finished.connect(self.thread.deleteLater)
		logSimulationConnection = self.thread.finished.connect(lambda:self.logSimulation(days, jsonName))
		endGoToConnection = self.thread.finished.connect(lambda:self.goToResults(days, pj))
		#connect to wroker progress
		self.worker.progress.connect(info.controlProgress)
		#connect to worker error
		self.worker.error.connect(error)
		#run
		self.thread.start()

	def logSimulation(self, days, name):
		"""
		Creates or edits a file (if necessary) with the information on which amounts of days have been simulated using the current json file

		Args:
			days: number of days in the current simulation
			name: name of the community currently in use
		"""
		loggedDays = Util.loggedDays(name)
		if str(days) in loggedDays: # simulation of this number of days has already been logged
			return
		path = Util.infoFile(name)
		f = open(path, "a")
		f.write(f"{days}\n")
		f.close()