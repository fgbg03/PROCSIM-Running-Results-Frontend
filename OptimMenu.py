import sys
from os.path import isfile
from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg
from Settings import Settings
from Util import Util

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

class SimOptions(qw.QWidget):
	def __init__(self, communityFile):
		"""
		Widget for selection of the simulation options:
		-number of days of the simulation to optimise
		
		Args:
			communityFile: path to the community json file
		"""
		super().__init__()

		label = CustomLab("Optimize Simulation of ")

		self.daysComboBox = qw.QComboBox()
		self.daysComboBox.setPlaceholderText("No simulation")
		loggedDays = Util.loggedDays(communityFile)

		for day in sorted(loggedDays, key = int):
			self.daysComboBox.addItem(Util.daysString(day))

		layout = qw.QHBoxLayout()
		layout.addWidget(label)
		layout.addWidget(self.daysComboBox)
		layout.addStretch()
		self.setLayout(layout)

	def getDays(self):
		"""
		Returns:
			number of days to simulate
		"""
		text = self.daysComboBox.currentText()
		i = text.find(" day")
		if i == -1:
			return -1
		days = int(text[:i])
		return days

	def setDays(self, days):
		"""
		Sets the days combo box to the given value if it is found
		If it is not found defaults to the first option in the combobox

		Args:
			days: number of days to optimise
		"""
		i = self.daysComboBox.findText(Util.daysString(days))
		if i == -1:
			i = 0
		self.daysComboBox.setCurrentIndex(i)

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

class OptimMenu(qw.QWidget):
	def __init__(self, optimMethod, communityFile):
		"""
		Screen with the menu to start an optimulation using PROCSIM
		Contains community file selector, start optimisation button, optimisation options and show results button 
		
		Args:
			communityFile: path to the community json file
		"""
		super().__init__()

		self.optimMethod = optimMethod

		optimName = Settings.optimizationNames()[self.optimMethod]
		self.btnOptim = CustomBtn(f"Start {optimName} Optimization")
		self.btnOptim.setObjectName("BigButton")
		self.simOptions = SimOptions(communityFile)
		self.btnRes = CustomBtn("Show Previous Results")

		layout = qw.QGridLayout()
		
		layout.addWidget(self.btnOptim,0,0,1,-1)
		
		layout.addWidget(self.simOptions, 1, 0, 1, -1)

		layout.addWidget(self.btnRes,2,0,1,-1)

		layout.setRowStretch(0,15)
		layout.setRowStretch(1,1)
		layout.setRowStretch(2,5)

		self.setLayout(layout)

	def loadOptions(self):
		"""
		Load previously used options
		"""
		self.simOptions.setDays(Settings.getDays())

	def getDays(self):
		"""
		Returns:
			number of days to simulate
		"""
		return self.simOptions.getDays()