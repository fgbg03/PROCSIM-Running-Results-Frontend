import sys

from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg

from OptimMenu import OptimMenu
from ResultScreen import DefaultGraphs
from ProcsimRun import ProcsimRun, InfoScreen
from Settings import Settings
from Util import Util

from os.path import isfile, isdir
from os import listdir

class ECOptimizer(qw.QMainWindow):
	def __init__(self, optimMethod, jsonPath):
		"""
		Screen pertaining to energy community optimisation

		Args:
			jsonPath: path to the json of the community
		"""
		super().__init__()

		self.optimMethod = optimMethod
		self.jsonPath = jsonPath

		self.goToOptimMenu()

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
			if days == -1:
				self.warnNotSimulated()
				return

		# building dictionary with useful paths to be used in the showing of results
		paths = {}
		jsonName = Util.fileName(pj)
		paths["json"] = pj
		x, y, paths[f"met{self.optimMethod}opt1"], paths[f"met{self.optimMethod}opt2"] = Settings.getOutputPaths(jsonName, days, self.optimMethod)
		
		testPath = paths[f"met{self.optimMethod}opt1"]
		if not isdir(testPath) or len(listdir(testPath)) == 0:
			self.warnNotOptimized()
			return

		graphScreen = DefaultGraphs(paths)
		graphScreen.goBack.connect(self.goToOptimMenu)
		self.closeOpenGraphs.connect(graphScreen.closeGraphs)
		self.setCentralWidget(graphScreen)

	def goToOptimMenu(self):
		"""
		Sets Optim Menu as central widget
		"""
		optimMenu = OptimMenu(self.optimMethod, self.jsonPath)
		optimMenu.loadOptions()
		optimMenu.btnRes.clicked.connect(lambda:self.goToResults())
		optimMenu.btnOptim.clicked.connect(self.optimize)
		self.setCentralWidget(optimMenu)

	def warnNoCommunity(self):
		"""
		Shows a message box warning no community's been selected
		"""
		errorPopup = qw.QMessageBox()
		errorPopup.setWindowTitle("Warning")
		errorPopup.setText("Please select a community before proceding.")
		errorPopup.exec()

	def warnNotOptimized(self):
		"""
		Shows a message box warning no community's been selected
		"""
		errorPopup = qw.QMessageBox()
		errorPopup.setWindowTitle("Warning")
		errorPopup.setText("No optimization found.")
		errorPopup.exec()

	def warnNotSimulated(self):
		"""
		Shows a message box warning no community's been selected
		"""
		errorPopup = qw.QMessageBox()
		errorPopup.setWindowTitle("Warning")
		errorPopup.setText("No simulation found.")
		errorPopup.exec()

	def optimize(self):
		"""
		Optimise Energy Community
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
			qc.QObject.disconnect(endGoToConnection)
			self.thread.finished.connect(self.goToOptimMenu)
			self.thread.finished.connect(lambda:print("Cancelled"))

		def error(exception):
			"""
			Show error message from the simulation

			Args:
				exception: exception raised during simulation
			"""
			print("Error\n"+str(exception))
			qc.QObject.disconnect(endGoToConnection)
			self.thread.finished.connect(self.goToOptimMenu)
			errorPopup = qw.QMessageBox()
			errorPopup.setWindowTitle("Something went wrong")
			errorPopup.setText("An error occurred during optimisation. Try checking the integrity of this community's simulation.")
			
			errorPopup.setInformativeText("Error details:\n"+str(exception))
			errorPopup.exec()
		
		pj = self.jsonPath
		if pj is None: # check if a community was selected
			self.warnNoCommunity()
			return

		# get needed values for simulation
		jsonName = Util.fileName(pj)
		days = self.centralWidget().getDays()
		if days == -1:
			self.warnNotSimulated()
			return
		ps, pm, p1o, p2o = Settings.getOutputPaths(jsonName, days, self.optimMethod)

		# set simulation information screen
		info = InfoScreen("Optimizing", "Preparing classes")
		self.setCentralWidget(info)

		# prepare thread for running simulation
		self.thread = qc.QThread()
		self.thread.setTerminationEnabled()
		self.worker = ProcsimRun(optimize = True, days = days, optimMethod = self.optimMethod,\
			path_steps_seconds = ps, path_steps_minutes = pm, \
			path_steps_after_first = p1o, path_steps_after_second = p2o, community_file = pj)

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
		endGoToConnection = self.thread.finished.connect(lambda:self.goToResults(days, pj))
		#connect to wroker progress
		self.worker.progress.connect(info.controlProgress)
		#connect to worker error
		self.worker.error.connect(error)
		#run
		self.thread.start()