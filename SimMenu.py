import sys
from os.path import isfile
from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg
from Settings import Settings

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
	def __init__(self):
		"""
		Widget for selection of the simulation options:
		-number of days to simulate
		-whether to skip Consumption Generator
		-whether to skip Renewable Energy Generator
		-whether to use local solar data
		"""
		super().__init__()

		label = CustomLab("Simulation Options")

		self.daysSpinBox = qw.QSpinBox()
		self.daysSpinBox.setMinimum(1)
		self.daysSpinBox.setSuffix(" day(s)")

		self.skipCgBox = qw.QCheckBox("Skip Consumption Generator")
		self.skipCgBox.toggled.connect(self.cgToggled)

		self.localPVBox = qw.QCheckBox("Solar Data From File")
		self.localPVBox.toggled.connect(self.localPVToggled)

		layout = qw.QHBoxLayout()
		layout.addWidget(label)
		layout.addWidget(self.daysSpinBox)
		layout.addWidget(self.skipCgBox)
		layout.addWidget(self.localPVBox)
		layout.addStretch()
		self.setLayout(layout)

	def cgToggled(self, checked):
		"""
		Keeps the settings consistent with the skipCg state.
		Now unused. Add clauses if conflicting settings are added

		Args:
			checked: if the check box is checked
		"""
		pass
	
	def localPVToggled(self, checked):
		"""
		Keeps the settings consistent.
		Checks if the path in the settings is valid and warns if it is not when trying to use it

		Args:
			checked: if the check box is checked
		"""

		if checked:
			path = Settings.getPVData()
			if not path or not isfile(path):
				self.localPVBox.setChecked(False)
				errorPopup = qw.QMessageBox()
				errorPopup.setWindowTitle("Warning")
				errorPopup.setText("No Photovoltaic Data file found.\nSelect one in the Settings to use this option.")
				errorPopup.exec()

	def skipCg(self):
		"""
		Returns:
			if Consumption Generator should be skipped
		"""
		return self.skipCgBox.isChecked()

	def useLocalPV(self):
		"""
		Returns:
			if local solar data should be used
		"""
		return self.localPVBox.isChecked()

	def getDays(self):
		"""
		Returns:
			number of days to simulate
		"""
		return self.daysSpinBox.value()

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

class SimMenu(qw.QWidget):
	def __init__(self):
		"""
		Screen with the menu to start a simulation using PROCSIM
		Contains community file selector, start simulation button, simulation options and show results button 
		"""
		super().__init__()

		self.btnSim = CustomBtn("Start Simulation")
		self.btnSim.setObjectName("BigButton")
		self.simOptions = SimOptions()
		self.btnRes = CustomBtn("Show Previous Results")

		layout = qw.QGridLayout()
		
		layout.addWidget(self.btnSim,0,0,1,-1)
		
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
		self.simOptions.skipCgBox.setChecked(Settings.getSkipCg())
		self.simOptions.localPVBox.setChecked(Settings.getlocalPV())
		self.simOptions.daysSpinBox.setValue(Settings.getDays())

	def saveOptions(self):
		"""
		Saves used options
		"""
		s = Settings()
		s.skipCg = self.skipCg()
		s.localPV = self.useLocalPV()
		s.days = self.getDays()
		s.save()

	def skipCg(self):
		"""
		Returns:
			if Consumption Generator should be skipped
		"""
		return self.simOptions.skipCg()

	def useLocalPV(self):
		"""
		Returns:
			if local solar data should be used
		"""
		return self.simOptions.useLocalPV()

	def getDays(self):
		"""
		Returns:
			number of days to simulate
		"""
		return self.simOptions.getDays()