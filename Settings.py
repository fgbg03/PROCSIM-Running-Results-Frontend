import sys

from os.path import isdir, isfile
from os.path import realpath
from os import listdir
from os import getcwd

from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg

class CSVFileSelector(qw.QWidget):
	def __init__(self):
		"""
		Widget for selecting a CSV file
		"""
		super().__init__()

		self.default = ""
		self.path = None
		self.label = qw.QLineEdit("")
		self.label.setReadOnly(True)
		self.setPath(self.default)

		self.btnChooseFile = qw.QPushButton()
		icon = self.style().standardIcon(qw.QStyle.SP_DirIcon)
		self.btnChooseFile.setIcon(icon) 
		self.btnChooseFile.clicked.connect(self.chooseFile)
		
		layout = qw.QGridLayout()
		layout.addWidget(self.label, 0, 0)
		layout.addWidget(self.btnChooseFile, 0, 1)

		self.setLayout(layout)

	def setPath(self, path):
		"""
		Set the path that was selected

		Args:
			path: selected path
		"""
		self.path = path
		if path:
			self.label.setText(self.path)
		else:
			self.label.setText("No File Selected")

	def chooseFile(self):
		"""
		Open a QFileDialog to choose the file
		"""
		path = qw.QFileDialog.getOpenFileName(caption = "Choose Solar Data File", filter = "CSV File (*.csv)")[0]
		if path == "":
			return
		self.setPath(path)

class FolderSelector(qw.QWidget):
	def __init__(self, default):
		"""
		Widget for selecting a folder

		Args:
			default: default folder
		"""
		super().__init__()

		self.default = realpath(default)
		self.path = None
		self.label = qw.QLineEdit("")
		self.label.setReadOnly(True)
		self.setPath(self.default)

		self.btnChooseDir = qw.QPushButton()
		icon = self.style().standardIcon(qw.QStyle.SP_DirIcon)
		self.btnChooseDir.setIcon(icon) 
		self.btnChooseDir.clicked.connect(self.chooseDir)
		self.btnChooseDir.setEnabled(False)

		self.checkBoxDefault = qw.QCheckBox("Use default")
		self.checkBoxDefault.setChecked(True)
		self.checkBoxDefault.toggled.connect(self.defaultToggled)
		
		layout = qw.QGridLayout()
		layout.addWidget(self.label, 0, 0)
		layout.addWidget(self.btnChooseDir, 0, 1)
		layout.addWidget(self.checkBoxDefault, 1, 0)

		self.setLayout(layout)

	def setPath(self, path):
		"""
		Set the path that was selected

		Args:
			path: selected path
		"""
		self.path = path
		self.label.setText(self.path)

	def chooseDir(self):
		"""
		Open a QFileDialog to choose the directory
		"""
		path = qw.QFileDialog.getExistingDirectory()
		if path == "":
			return
		self.setPath(path)

	def uncheck(self):
		"""
		Unchecks the 'default' check box
		"""
		self.checkBoxDefault.setChecked(False)

	def defaultToggled(self, checked):
		"""
		Action of the 'default' checkbox, select the default path if checked, enable path selection if not

		Args:
			checked: if the check box is checked
		"""
		if checked:
			self.setPath(self.default)
			self.btnChooseDir.setEnabled(False)
		else:
			self.btnChooseDir.setEnabled(True)

class Settings(qw.QDialog):
	__filename = "settings.conf" # file with the saved settings
	__json_path = "." # default folder path with the json (community configuration) files
	__output_path = "output" # default output path
	__sec_folder_name = "second" # folder name for the antegen files (at 1Hz)
	__min_folder_name = "minute" # folder name for the resampled files (at 1/60Hz)
	__ao_folder_name = "afteroptimization" # folder name for the 1st optimisation files
	__a2o_folder_name = "aftersecoptimization" # folder name for the 2nd optimisation files
	__optimization_names = ("Default", "Pyomo") # tuple containing the names of the optimisation method
	__default_skip_cg = False # default setting for skipping Consumption Generator
	__default_local_pv = False # default setting for using the local solar data file
	__default_days = 1 # default number of days to simulate
	
	def __init__(self):
		"""
		Dialog to change the application Settings and manager of other settings set outside of this window
		Settings changed in this window:
		- JSON folder path
		- Output folder path
		- Solar data CSV file path
		"""
		super().__init__()

		policy = qw.QSizePolicy()
		policy.setHorizontalPolicy(qw.QSizePolicy.MinimumExpanding)
		policy.setVerticalPolicy(qw.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(policy)

		self.setWindowTitle("Settings")

		self.json_selector = FolderSelector(self.__json_path)

		self.output_path_selector = FolderSelector(self.__output_path)

		self.pv_file_selector = CSVFileSelector()

		form = qw.QFormLayout()
		form.addRow("Community Directory", self.json_selector)
		form.addRow("Output Directory", self.output_path_selector)
		form.addRow("Solar Data File", self.pv_file_selector)

		btnCancel = qw.QPushButton("Cancel")
		btnCancel.clicked.connect(self.cancel)
		btnSave = qw.QPushButton("Save")
		btnSave.clicked.connect(self.save)
		buttons_layout = qw.QHBoxLayout()
		buttons_layout.addWidget(btnCancel)
		buttons_layout.addWidget(btnSave)

		layout = qw.QVBoxLayout()
		layout.addLayout(form)
		layout.addStretch()
		layout.addLayout(buttons_layout)
		self.setLayout(layout)

		self.skipCg = Settings.__default_skip_cg
		self.localPV = Settings.__default_local_pv
		self.days = Settings.__default_days

		if isfile(self.__filename):
			self.loadConfig()

	def cancel(self):
		"""
		Closes the window without saving the new settings
		"""
		self.close()

	def save(self):
		"""
		Saves the selected settings and closes the window
		"""
		f = open(self.__filename, "w")

		f.write(f"#saved paths\n")
		f.write(f"json_path={self.json_selector.path}\n")
		f.write(f"output_path={self.output_path_selector.path}\n")
		f.write(f"pv_data={self.pv_file_selector.path}\n")
		
		f.write(f"#last runner options used\n")
		f.write(f"skip_cg={int(self.skipCg)}\n")
		f.write(f"local_pv={int(self.localPV)}\n")
		f.write(f"days={self.days}\n")

		f.close()

		self.close()

	def loadConfig(self):
		"""
		Read saved settings and load them to be shown in the window
		"""
		pathJson = Settings.getJsonPath()
		pathOutput = Settings.getOutputPath()
		pathPVData = Settings.getPVData()
		if not (pathJson is None or pathJson == self.__json_path \
			or pathJson == realpath(self.__json_path)):
			self.json_selector.uncheck()
			self.json_selector.setPath(pathJson)
		if not (pathOutput is None or pathOutput == self.__output_path \
			or pathOutput == realpath(self.__output_path)):
			self.output_path_selector.uncheck()
			self.output_path_selector.setPath(pathOutput)
		self.pv_file_selector.setPath(pathPVData)

		skip_cg = Settings.getSkipCg()
		local_pv = Settings.getlocalPV()
		days = Settings.getDays()

		self.skipCg = skip_cg
		self.localPV = local_pv
		self.days = days

	def sizeHint(self):
		"""
		Override of parent method
		"""
		hint = qc.QSize()
		hint.setHeight(300) #will be bigger
		hint.setWidth(700) #gives enough room for the text to be readable
		return hint
	
	@staticmethod		
	def findInFile(label):
		"""
		Finds the value of a setting in the settings file

		Args:
			label: label ('foo=') that identifies the wanted setting
		"""
		if isfile(Settings.__filename):
			f = open(Settings.__filename, "r")
			reading = f.readline()
			while reading != "":
				idx = reading.find(label)
				if idx != -1:
					path = reading[idx + len(label):-1]
					f.close()
					return path
				reading = f.readline()
			f.close()
		return None
	
	@staticmethod
	def getJsonPath():
		"""
		Returns:
			the path to the folder containg the json files
		"""
		return Settings.findInFile("json_path=") or Settings.__json_path
	
	@staticmethod
	def getOutputPath():
		"""
		Returns:
			the path to the output folder
		"""
		return Settings.findInFile("output_path=") or Settings.__output_path
	
	@staticmethod
	def getPVData():
		"""
		Returns:
			the path to the solar data CSV file
		"""
		path = Settings.findInFile("pv_data=")
		if path and isfile(path):
			return path
		else:
			return ""
	@staticmethod
	def getOutputPaths(community_name, days, optim_method = 0):
		"""
		Args:
			community_name: name of the community json file is in use (without .json extension)
			days: number of simulated days
			optim_method: optimisation method in use
		Returns:
			tuple of the paths used to run a simulation with the set optimisation method
			[0] path of the consumption profiles generated by ANTGen (at 1 Hz)
			[1] path of the resampled consumption profiles (at 1/60Hz)
			[2] path of the consumption profiles after the 1st step of the optimization
			[3] path of the consumption profiles after the 2nd step of the optimization
			"""
		if optim_method >= len(Settings.__optimization_names):
			print("Optimization method not in range, defaulting")
			optim_method = 0
		name = community_name
		i = optim_method
		output = Settings.getOutputPath()
		
		secPath = f"{output}/{name}-{days}days/{Settings.__sec_folder_name}"
		minPath = f"{output}/{name}-{days}days/{Settings.__min_folder_name}"
		a1oPath = f"{output}/{name}-{days}days/{Settings.__optimization_names[i].lower()}/{Settings.__ao_folder_name}"
		a2oPath = f"{output}/{name}-{days}days/{Settings.__optimization_names[i].lower()}/{Settings.__a2o_folder_name}"

		return secPath, minPath, a1oPath, a2oPath

	@staticmethod
	def optimizationNames():
		"""
		Returns:
			tuple containing the names of the available optimisation methods
		"""
		return Settings.__optimization_names

	@staticmethod
	def getSkipCg():
		"""
		Returns:
			last setting of the Skip Consumption Generator option
		"""
		s = Settings.findInFile("skip_cg=")
		s = Settings.__default_skip_cg if s is None else bool(int(s))
		return s
	
	def getlocalPV():
		"""
		Returns:
			last setting of the Use Local Lolar Data option
		"""
		pv = Settings.findInFile("local_pv=")
		pv = Settings.__default_local_pv if pv is None else bool(int(pv))
		return pv
	
	def getDays():
		"""
		Returns:
			last setting of the number of days to simulate option
		"""
		d = Settings.findInFile("days=")
		d = Settings.__default_days if d is None else int(d)
		return d