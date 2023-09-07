import sys
import json

from os.path import isfile
import matplotlib.pyplot as plt

from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg

from ClickableGraph import CustomGraph
from ProcsimGraphs import BaseloadGraph, HouseGraph, SelfSufficiencyGraph, TimeslotsGraph
from GraphParamSelector import GraphParamSelector
from Settings import Settings
from Util import Util

class DefaultGraphs(qw.QWidget):
	def __init__(self, paths, backButton = True):
		"""
		Widget to show pre selected graphs

		Args:
			paths: dictionary with relevant paths
			backButton: whether to create a button to return to the last screen (useful when arriving at the default graphs from the simulation or optimisation screen)
		"""
		super().__init__()

		policy = qw.QSizePolicy()
		policy.setControlType(qw.QSizePolicy.PushButton)
		policy.setHorizontalPolicy(qw.QSizePolicy.Maximum)
		policy.setVerticalPolicy(qw.QSizePolicy.Maximum)

		icon = self.style().standardIcon(qw.QStyle.SP_ArrowBack)

		btnBack = qw.QPushButton()
		btnBack.setSizePolicy(policy)
		btnBack.setIcon(icon) 
		btnBack.clicked.connect(lambda: self.goBack.emit())
		btnBack.clicked.connect(lambda: self.closeGraphs.emit())

		with open(paths.get("json")) as json_file:
			community = json.load(json_file)

		#house graphs
		houseGraphsLayout = qw.QHBoxLayout()
		for i in range(len(community)):
			hg = HouseGraph(paths, i, community)
			self.closeGraphs.connect(hg.closeFigure)
			houseGraphsLayout.addWidget(hg)
		houseGraphs = qw.QWidget()
		houseGraphs.setLayout(houseGraphsLayout)

		houseGraphsScrollArea = qw.QScrollArea()
		houseGraphsScrollArea.setHorizontalScrollBarPolicy(qc.Qt.ScrollBarAlwaysOn)
		policy = qw.QSizePolicy() # to make the scroll area only use the vertical space needed
		policy.setHorizontalPolicy(qw.QSizePolicy.MinimumExpanding)
		policy.setVerticalPolicy(qw.QSizePolicy.Maximum)
		houseGraphsScrollArea.setSizePolicy(policy)
		houseGraphsScrollArea.setWidget(houseGraphs)

		#timeslots graphs
		timsGraphsLayout = qw.QHBoxLayout()
		for i in range(len(community)):
			tg = TimeslotsGraph(paths, i, community)
			self.closeGraphs.connect(tg.closeFigure)
			timsGraphsLayout.addWidget(tg)
		timsGraphs = qw.QWidget()
		timsGraphs.setLayout(timsGraphsLayout)

		timsGraphsScrollArea = qw.QScrollArea()
		timsGraphsScrollArea.setHorizontalScrollBarPolicy(qc.Qt.ScrollBarAlwaysOn)
		policy = qw.QSizePolicy() # to make the scroll area only use the vertical space needed
		policy.setHorizontalPolicy(qw.QSizePolicy.MinimumExpanding)
		policy.setVerticalPolicy(qw.QSizePolicy.Maximum)
		timsGraphsScrollArea.setSizePolicy(policy)
		timsGraphsScrollArea.setWidget(timsGraphs)

		#other graphs
		baseloadGraph = BaseloadGraph(community, paths)
		self.closeGraphs.connect(baseloadGraph.closeFigure)

		selfSufficiencyGraph = SelfSufficiencyGraph(paths)
		self.closeGraphs.connect(selfSufficiencyGraph.closeFigure)

		layout = qw.QGridLayout()

		if backButton:
			layout.addWidget(btnBack , 0, 0)

		layout.addWidget(houseGraphsScrollArea, 1, 0, 1, -1)
		
		layout.addWidget(timsGraphsScrollArea, 2, 0, 1, -1)

		layout.addWidget(baseloadGraph, 3, 0, 1, 1)
		layout.addWidget(selfSufficiencyGraph, 3, 1, 1, 1)

		self.setLayout(layout)
	
	goBack = qc.Signal() #signal for clicking the back button
	closeGraphs = qc.Signal() #signal telling to close the graphs

class GraphCreator(qw.QWidget):
	def __init__(self, paths):
		"""
		Widget to enabled creation of graphs form the created CSV files

		Args:
			paths: dictionary with relevant paths
		"""
		super().__init__()

		self.paramSelector = GraphParamSelector(paths)
		self.customGraph = CustomGraph()
		self.closeGraph.connect(self.customGraph.closeFigure)
		self.paramSelector.dataframeCreated.connect(self.customGraph.showGraphFromDf)

		layout = qw.QGridLayout()
		layout.addWidget(self.paramSelector,0,0)
		layout.addWidget(self.customGraph,0,1)

		layout.setColumnStretch(0, 1)
		layout.setColumnStretch(1, 2)

		self.setLayout(layout)

	closeGraph = qc.Signal()

class ResultScreen(qw.QTabWidget):
	def __init__(self, paths, delayCreation = False):
		"""
		Tab widget containing two tabs with results from the simulation

		Args:
			paths: dictionary with relevant paths
			delayCreation: whether to create tabs on init (used so it doesn't load graphs unnecessarily)
		"""
		super().__init__()

		self.tabsCreated = False
		self.paths = paths

		if not delayCreation:
			self.createTabs()

	closeOpenGraphs = qc.Signal()

	def createTabs(self):
		"""
		Creates the tabs of this widget. DefaultGraphs and GraphCreator
		"""
		if not self.tabsCreated:
			dg = DefaultGraphs(self.paths, backButton = False)
			self.closeOpenGraphs.connect(dg.closeGraphs)
			self.addTab(dg, "Default Graphs")
			gc = GraphCreator(self.paths)
			self.closeOpenGraphs.connect(gc.closeGraph)
			self.addTab(gc, "Graph Creator")
			self.tabsCreated = True

	def resizeEvent(self, event): # makes the tabs occupy the full width of the widget
		"""
		Override of parent method
		"""
		self.tabBar().setFixedWidth(self.width())
		super().resizeEvent(event)

class Overview(qw.QTabWidget):
	def __init__(self, communityFile):
		"""
		Widget to show every result of the given community.
		Every simulation will be in a tab identified by the number of simulated days.

		Args:
			communityFile: path to the json file of the community in use
		"""
		super().__init__()
		self.error = False
		self.communityFile = communityFile

		loggedDays = Util.loggedDays(self.communityFile)

		if len(loggedDays) == 0:
			self.warnNotSimulated()
			self.error = True
			return

		self.resultScreens = []
		for day in sorted(loggedDays, key = int):
			rs = self.createResScreen(int(day))
			self.resultScreens.append(rs)
			self.addTab(rs, Util.daysString(day))

		self.currentChanged.connect(self.initTabs)

	noTabs = qc.Signal()
	closeOpenGraphs = qc.Signal()

	def showEvent(self, event):
		"""
		Override of the parent method to open the tab corresponding to the last day used upon showing the widget
		"""
		super().showEvent(event)

		#switch to the tab representing the number of days used in the app
		self.setTabByDay(Settings.getDays())
		#show the tabs of the current widget when setTabsByDay fails or selects the first tab
		self.currentWidget().createTabs()

	def initTabs(self, idx):
		"""
		Creates the tabs os the ResultScreen in the given index

		Args:
			idx: index of the ResultScreen
		"""
		self.resultScreens[idx].createTabs()

	def setTabByDay(self, day):
		"""
		Selects the tab which refferences the given days

		Args:
			day: the number of days in the simulation to open the tab of
		"""
		for i in range(len(self.resultScreens)):
			if self.tabText(i) == Util.daysString(day):
				self.setCurrentIndex(i)

	def createResScreen(self, days):
		"""
		Creates a ResultScreen using the community file stored in the object and the number of days simulated

		Args:
			days: number of days in the simulation the ResultScreen being created pertains to
		"""
		# building dictionary with useful paths to be used in the showing of results
		paths = {}
		jsonName = Util.fileName(self.communityFile)
		paths["json"] = self.communityFile
		for i in range(len(Settings.optimizationNames())):
			paths["second"], \
			paths["minute"], \
			paths[f"met{i}opt1"], \
			paths[f"met{i}opt2"] = Settings.getOutputPaths(jsonName, days, i)
		
		rs = ResultScreen(paths, delayCreation = True)
		self.closeOpenGraphs.connect(rs.closeOpenGraphs)
		return rs

	def warnNotSimulated(self):
		"""
		Shows a message box warning no community's been selected
		"""
		errorPopup = qw.QMessageBox()
		errorPopup.setWindowTitle("Warning")
		errorPopup.setText("No simulations found.")
		errorPopup.exec()