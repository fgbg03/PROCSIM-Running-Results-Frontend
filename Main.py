import sys
from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg

from ECSimulator import ECSimulator
from ECOptimizer import ECOptimizer
from Settings import Settings
from Help import Help
from Home import Home
from ResultScreen import Overview
from Util import Util

class SideButton(qw.QPushButton):
	def __init__(self, label, checkable = True):
		"""
		Widget for the buttons on the side bar
		
		Args:
			label: label on the button
			checkable: if the buttonis kept down after clicking
		"""
		super().__init__()

		self.setStyleSheet("text-align: left")

		self.setMinimumSize(200,30)

		policy = qw.QSizePolicy()
		policy.setHeightForWidth(True)
		policy.setWidthForHeight(True)
		policy.setControlType(qw.QSizePolicy.PushButton)
		policy.setHorizontalPolicy(qw.QSizePolicy.MinimumExpanding)
		policy.setVerticalPolicy(qw.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(policy)

		self.setFlat(True)
		self.setCheckable(checkable)
		self.setAutoExclusive(True)
		self.setText(label)

	def sizeHint(self):
		"""
		Override of parent method
		"""
		hint = qc.QSize()
		hint.setHeight(15)
		hint.setWidth(100)
		return hint

class SideBar(qw.QWidget):
	def __init__(self):
		"""
		Side bar widget
		"""
		super().__init__()

		self.setAutoFillBackground(True)

		self.btnGroup = qw.QButtonGroup()
		self.btnGroup.setExclusive(True)
		self.btnGroup.idToggled.connect(self.toggledBtn)

		self.btnHome = SideButton("Home")
		self.btnGroup.addButton(self.btnHome)
		self.btnSim = SideButton("EC Simulator")
		self.btnGroup.addButton(self.btnSim)

		for i, optim in enumerate(Settings.optimizationNames()):
			btn = SideButton(f"{optim} Optimizer")
			self.btnGroup.addButton(btn, i) # button id is the index in tuple

		self.btnOverview = SideButton("Overview")
		self.btnGroup.addButton(self.btnOverview)

		# botões que acionam popups não ficam checked
		self.btnSettings = SideButton("Settings", checkable = False)
		self.btnHelp = SideButton("Help", checkable = False)
		
		spacer = qw.QSpacerItem(1, 1000, qw.QSizePolicy.Maximum, qw.QSizePolicy.Maximum)

		layout = qw.QVBoxLayout()
		layout.addWidget(self.btnHome)
		layout.addWidget(self.btnSim)
		for i in range(len(Settings.optimizationNames())):
			layout.addWidget(self.btnGroup.button(i))
		layout.addWidget(self.btnOverview)
		layout.addSpacerItem(spacer)
		layout.addWidget(self.btnSettings)
		layout.addWidget(self.btnHelp)

		self.setLayout(layout)

	optimButtonToggled = qc.Signal(int, bool)

	def setButtonsEnabled(self, val):
		"""
		Sets the enabled state of the side bar buttons

		Args:
			val: True or False
		"""
		for btn in self.btnGroup.buttons():
			btn.setEnabled(val)

	def toggledBtn(self, idx, checked):
		"""
		Emit a signal when an optimisation button has been toggled

		Args:
			idx: index of the button toggled (equal to the index of the optimisation method)
			checked: if the button is checked
		"""
		if idx < 0:
			return
		self.optimButtonToggled.emit(idx,checked)

class MainWindow(qw.QMainWindow):
	def __init__(self):
		"""
		QMainWindow of this application
		"""
		super().__init__()

		self.communityFile = None
		self.currentGraphConn = None #variable to keep track of the connection to closeOpenGraphs

		self.setAutoFillBackground(True)

		self.setWindowTitle("PROCSIM")
		#Adding Sider Bar as a ToolBar
		self.sideBar = SideBar()
		self.sideBar.btnHome.toggled.connect(self.goToHome)
		self.sideBar.btnSim.toggled.connect(self.goToEcSim)
		self.sideBar.optimButtonToggled.connect(self.goToOptim)
		self.sideBar.btnOverview.toggled.connect(self.goToOverview)
		self.sideBar.btnSettings.clicked.connect(self.popupSettings)
		self.sideBar.btnHelp.clicked.connect(self.popupHelp)
		toolBar = qw.QToolBar()
		toolBar.setFloatable(False)
		toolBar.setMovable(False)
		toolBar.setAllowedAreas(qc.Qt.LeftToolBarArea)
		toolBar.addWidget(self.sideBar)
		self.addToolBar(qc.Qt.LeftToolBarArea,toolBar)

		#entering home
		self.sideBar.btnHome.setChecked(True)

		self.sideBar.setButtonsEnabled(False)

	leftSettings = qc.Signal()
	closeOpenGraphs = qc.Signal()

	def setCommunityFile(self, communityFile):
		"""
		Sets the currently selected community json file.
		Changes the title of the window to contain the file name.

		Args:
			communityFile: path to the community json file to set
		"""
		self.communityFile = communityFile
		self.sideBar.setButtonsEnabled(True)
		name = Util.fileName(self.communityFile)
		self.setWindowTitle(f"{name} - PROCSIM")

	def goToHome(self, checked = None):
		"""
		Set home screen as the central widget

		Args:
			checked: if the button was checked
		"""
		if checked is None: #if checked was not provided, programmatically checks the button that activates this funtion
			self.sideBar.btnHome.setChecked(True)
			return

		if not checked:
			return
		home = Home(self.communityFile)
		home.simChosen.connect(self.goToEcSim)
		home.communitySelected.connect(self.setCommunityFile)
		home.optimChosen.connect(self.goToOptim)
		home.overviewChosen.connect(self.goToOverview)
		self.leftSettings.connect(home.updateFolder)
		self.closeOpenGraphs.emit()
		self.severConnection()
		self.setCentralWidget(home)

	def goToEcSim(self, checked = None):
		"""
		Set EC Simulator as the central widget

		Args:
			checked: if the button was checked
		"""
		if checked is None: #if checked was not provided, programmatically checks the button that activates this funtion
			self.sideBar.btnSim.setChecked(True)
			return

		if not checked:
			return
		ecSim = ECSimulator(self.communityFile)
		self.closeOpenGraphs.emit()
		self.severConnection()
		self.currentGraphConn = self.closeOpenGraphs.connect(ecSim.closeOpenGraphs.emit)
		self.setCentralWidget(ecSim)

	def goToOptim(self, idx, checked = None):
		"""
		Sets an EC Optimizer as the central widget

		Args:
			idx: index of the selected optimisation method
			checked: if the button was checked
		"""
		if checked is None: #if checked was not provided, programmatically checks the button that activates this funtion
			self.sideBar.btnGroup.button(idx).setChecked(True)
			return

		if not checked:
			return
		ecOptim = ECOptimizer(idx, self.communityFile)
		self.closeOpenGraphs.emit()
		self.severConnection()
		self.currentGraphConn = self.closeOpenGraphs.connect(ecOptim.closeOpenGraphs.emit)
		self.setCentralWidget(ecOptim)

	def goToOverview(self, checked = None):
		"""
		Sets the central widget to the Overview screen

		Args:
			checked: if the button was checked
		"""
		if checked is None: #if checked was not provided, programmatically checks the button that activates this funtion
			self.sideBar.btnOverview.setChecked(True)
			return

		if not checked:
			return		
		ov = Overview(self.communityFile)
		if ov.error: # if there are no simulations to view
			self.goToHome()
			return
		self.closeOpenGraphs.emit()
		self.severConnection()
		self.currentGraphConn = self.closeOpenGraphs.connect(ov.closeOpenGraphs.emit)
		self.setCentralWidget(ov)

	def popupSettings(self):
		"""
		Show settings window
		"""
		settings = Settings()
		settings.exec()

		self.leftSettings.emit()

	def popupHelp(self):
		"""
		Show help window
		"""
		helpWidget = Help()
		helpWidget.exec()

	def severConnection(self):
		"""
		Disconnects the currentGraphConn if it exists
		"""
		if self.currentGraphConn is not None:
			qc.QObject.disconnect(self.currentGraphConn)
			self.currentGraphConn = None
		
if __name__ == "__main__":
	app = qw.QApplication([])

	widget = MainWindow()
	widget.showMaximized()
	with open("StyleSheet.qss", "r") as f:
		_style = f.read()
		app.setStyleSheet(_style)

	sys.exit(app.exec())