import sys

from os.path import isdir
from os import listdir

from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg

from Util import Util
from Settings import Settings
from GraphParamSelector import LineList #provavelmente faria mais sentido se isto fosse buscado pelos dois modulos a um sitio comum

class CustomBtn(qw.QPushButton):
	def __init__(self, label):
		"""
		QPushButton with custom size policy

		Args:
			label: text displayed on the button
		"""
		super().__init__(label)

		policy = qw.QSizePolicy()
		policy.setControlType(qw.QSizePolicy.PushButton)
		policy.setHorizontalPolicy(qw.QSizePolicy.Ignored)
		policy.setVerticalPolicy(qw.QSizePolicy.Ignored)
		self.setSizePolicy(policy)

class CustomLab(qw.QLabel):
	def __init__(self, text):
		"""
		QLabel with custom size policy

		Args:
			text: label text
		"""
		super().__init__(text)
		self.setAlignment(qc.Qt.AlignLeft | qc.Qt.AlignVCenter)
		policy = qw.QSizePolicy()
		policy.setHorizontalPolicy(qw.QSizePolicy.Minimum)
		policy.setVerticalPolicy(qw.QSizePolicy.Maximum)
		self.setSizePolicy(policy)

class OptimMethodSelect(qw.QWidget):
	def __init__(self):
		"""
		Widget to select an optimisation window to switch to
		(automatically arranges the method from the Settings.optimizationNames tuple)
		"""
		super().__init__()

		self.btnGroup = qw.QButtonGroup()

		methods = Settings.optimizationNames()

		for i, method in enumerate(methods): # Creating a button per method
			btn = CustomBtn(f"{method} Optimizer")
			self.btnGroup.addButton(btn, i) # button id is the index in tuple

		label = CustomLab("Optimize Community")
		layout = qw.QGridLayout()

		layout.addWidget(label, 0, 0, 1, -1)

		for btn in self.btnGroup.buttons(): # Arranging the buttons in a grid with height 2
			idx = self.btnGroup.id(btn)
			row = idx % 2 + 1 # +1 because of the label
			col = idx // 2
			layout.addWidget(btn, row, col)

		self.setLayout(layout)

class HomeMenu(qw.QWidget):
	def __init__(self):
		"""
		Widget with buttons to access the community selector and the screens from the side bar
		"""
		super().__init__()

		selectComm = CustomBtn("Select Community")
		selectComm.clicked.connect(lambda: self.commChosen.emit())

		selectSim = CustomBtn("EC Simulator")
		selectSim.clicked.connect(lambda: self.simChosen.emit())

		selectOptim = OptimMethodSelect()
		selectOptim.btnGroup.idClicked.connect(lambda optim: self.optimChosen.emit(optim))

		selectOverview = CustomBtn("Overview")
		selectOverview.clicked.connect(lambda: self.overviewChosen.emit())

		layout = qw.QVBoxLayout()
		layout.addWidget(selectComm)
		layout.addStretch(1)
		layout.addWidget(selectSim)
		layout.addWidget(selectOptim)
		layout.addWidget(selectOverview)
		layout.setStretch(0, 4)
		layout.setStretch(2, 6)
		layout.setStretch(3, 6)
		layout.setStretch(4, 4)
		self.setLayout(layout)

	commChosen = qc.Signal()
	simChosen = qc.Signal()
	optimChosen = qc.Signal(int)
	overviewChosen = qc.Signal()

class CommunityWidget(qw.QWidget):
	def __init__(self, path):
		"""
		Widget that represents a communtiy in the community selector.
		Contains a button to select it and information about which simulations and optimisations have been done on this community.

		Args:
			path: path to the community
		"""
		super().__init__()
		self.path = path

		fileName = Util.fileName(self.path)
		loggedDays = Util.loggedDays(fileName)
		optimNames = Settings.optimizationNames()
		nOptims = len(optimNames)
		simulated = []
		optims = [[] for i in range(nOptims)]
		for day in sorted(loggedDays, key = int):
			simulated.append(day)
			for i in range(nOptims):
				optimPath = Settings.getOutputPaths(fileName, day, i)[2]
				if isdir(optimPath) and len(listdir(optimPath)) != 0:
					optims[i].append(day)

		btn = qw.QPushButton(fileName)
		btn.clicked.connect(lambda: self.chosen.emit(self.path))

		simLabel = ", ".join(simulated)
		simLabel = Util.daysString(simLabel) if simLabel != "" else "--"
		simLabel = f"Simulated: {simLabel}"
		for i, optim in enumerate(optims):
			optimLabel = ", ".join(optim) or "--"
			if optimLabel == "--":
				continue
			simLabel = f"{simLabel}    {optimNames[i]}: {Util.daysString(optimLabel)}"
		lab = qw.QLabel(simLabel)

		layout = qw.QHBoxLayout()
		layout.addWidget(btn)
		layout.addWidget(lab)
		layout.setStretch(0, 3)
		layout.setStretch(1, 1)
		
		self.setLayout(layout)

	chosen = qc.Signal(str)		

class CommunitySelector(qw.QWidget):
	def __init__(self, firstSelection):
		"""
		Widget to select a community from the folder selected in the settings

		Args:
			firstSelection: whether this is the first selection after opening the app, disabling the return to the HomeMenu
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
		btnBack.clicked.connect(lambda: self.returnHome.emit())
		
		label = qw.QLabel("Select Community")

		fileList = self.createFileList()

		self.scrollArea = qw.QScrollArea()
		self.scrollArea.setVerticalScrollBarPolicy(qc.Qt.ScrollBarAlwaysOn)
		self.scrollArea.setWidget(fileList)

		layout = qw.QVBoxLayout()
		if not firstSelection:
			layout.addWidget(btnBack)
		layout.addWidget(label)
		layout.addWidget(self.scrollArea)

		self.setLayout(layout)

	communitySelected = qc.Signal(str)
	returnHome = qc.Signal()

	def updateCommunitiesList(self):
		"""
		Updates the list of community files.
		Used when the setting is changed while in this screen.
		"""
		fileList = self.createFileList()
		self.scrollArea.setWidget(fileList)

	def createFileList(self):
		"""
		Creates a list with the paths to the json files in the json path folder in the settings
		"""
		fileList = LineList()
		jsonFiles = []
		jsonFodler = Settings.getJsonPath()
		for file in listdir(jsonFodler):
			if file[-5:] == ".json":
				jsonFiles.append(f"{jsonFodler}/{file}")
		for path in sorted(jsonFiles, key = lambda p: p[:-5]): #sorted ignoring .json extention
			w = CommunityWidget(path)
			w.chosen.connect(lambda p: self.communitySelected.emit(p))
			fileList.addWidget(w)

		return fileList
		

class Home(qw.QMainWindow):
	def __init__(self, community_file = None):
		"""
		Manages the Home Menu and Community Selector screens

		Args:
			community_file: path to the json of the community
		"""
		super().__init__()

		if community_file is None:
			self.goToSelectCommunity(first = True)
		else:
			self.goToHomeMenu()

	#Signals pertaining to the selection of buttons shared with the side bar
	simChosen = qc.Signal()
	optimChosen = qc.Signal(int)
	overviewChosen = qc.Signal()
	#Signal telling a community has been selected
	communitySelected = qc.Signal(str)
	#Signal telling the json folder has been changed
	update = qc.Signal()

	def goToHomeMenu(self):
		"""
		Sets the Home Menu as the central widget
		"""
		hm = HomeMenu()
		hm.commChosen.connect(self.goToSelectCommunity)
		hm.simChosen.connect(lambda: self.simChosen.emit())
		hm.optimChosen.connect(lambda optim: self.optimChosen.emit(optim))
		hm.overviewChosen.connect(lambda: self.overviewChosen.emit())
		self.setCentralWidget(hm)

	def goToSelectCommunity(self, first = False):
		"""
		Sets the Community Selector as the central widget

		Args:
			fisrt: whether this is the first time selecting a community after starting the app
		"""
		commSelector = CommunitySelector(first)
		commSelector.communitySelected.connect(self.selectCommunity)
		commSelector.returnHome.connect(self.goToHomeMenu)
		self.update.connect(commSelector.updateCommunitiesList)
		self.setCentralWidget(commSelector)

	def selectCommunity(self, path):
		"""
		Selects the community json file

		Args:
			path: path to the selected community
		"""
		self.communitySelected.emit(path)
		self.goToHomeMenu()

	def updateFolder(self):
		"""
		Emits a signal informing the json folder has been updates
		"""
		self.update.emit()
		