import sys

from os.path import isdir, isfile
from os import listdir

from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg

from Settings import Settings

from procsimulator import ConsumptionGenerator as CG

import antgen
import pandas as pd

class InternalCsvSelector(qw.QWidget):
	def __init__(self, paths):
		"""
		Widget to select the path of existing CSV files form the simulation

		Args:
			paths: dictionary with relevant paths
		"""
		super().__init__()

		self.community = CG.ConsumptionGenerator(paths.get("json"), None, None).get_community()
		self.selection = None

		self.folders = {"Original Data": None}		
		min_folder = paths.get("minute")
		if min_folder is not None and isdir(min_folder) and len(listdir(min_folder)) != 0:
			self.folders["Original Data"] = min_folder
		
		for i, optName in enumerate(Settings.optimizationNames()):
			self.folders[f"{optName} Optimization"] = None
			self.folders[f"2nd {optName} Optimization"] = None

			opt1_folder = paths.get(f"met{i}opt1")
			opt2_folder = paths.get(f"met{i}opt2")

			if opt1_folder is not None and isdir(opt1_folder) and len(listdir(opt1_folder)) != 0:
				self.folders[f"{optName} Optimization"] = opt1_folder
			if opt2_folder is not None and isdir(opt2_folder) and len(listdir(opt2_folder)) != 0:
				self.folders[f"2nd {optName} Optimization"] = opt2_folder 

		folderSelector = qw.QComboBox()
		folderSelector.setPlaceholderText("Select Folder")
		folderSelector.setCurrentIndex(-1)
		for key in self.folders.keys():
			if self.folders[key] != None:
				folderSelector.addItem(key)
		folderSelector.currentTextChanged.connect(self.folderSelected)
		self.form = qw.QFormLayout()
		self.form.addRow("Folder:", folderSelector)
		formWidget = qw.QWidget()
		formWidget.setLayout(self.form)

		self.ok = False
		self.btnOk = qw.QPushButton("Ok")
		self.btnOk.setCheckable(True)
		self.btnOk.setChecked(True)
		self.btnOk.clicked.connect(self.btnOkClicked)

		self.btnCancel = qw.QPushButton("Cancel")
		self.btnCancel.clicked.connect(self.cancelled.emit)

		layout = qw.QGridLayout()
		layout.addWidget(formWidget, 0, 0, 1, -1)

		layout.addWidget(self.btnCancel, 1, 0, 1, 1)
		layout.addWidget(self.btnOk, 1, 1, 1, 1)

		self.setLayout(layout)

	madeSelection = qc.Signal(str, str, str, str, str)
	cancelled = qc.Signal()

	def btnOkClicked(self):
		"""
		Finishes the selection if all needed fields have been selected
		"""
		if self.ok:
			folderName, name, house, path, var = self.selection
			self.madeSelection.emit(folderName, name, house, path, var)
		else:
			self.setOk(False)

	def setSelection(self, folderName, name, house = "Community", path = None, var = "Power"):
		"""
		Sets the selection of the CSV

		Args:
			folderName: name of the folder containing the selected CSV
			name: name of the CSV
			house: house folder of the file ('Community' if outside a house folder)
			path: path selected
			var: name of the selected column for CSVs with multiple columns
		"""
		if path == None:
			return
		self.selection = (folderName, name, house, path, var)
		self.setOk(True)

	def setOk(self, val):
		"""
		Sets if the selection is ready to be finished

		Args:
			val: if it's ok or not to finish
		"""
		self.ok = val
		self.btnOk.setChecked(not val)

	def folderSelected(self, folderName):
		"""
		Handles selection of the folder containing the CSV
		Args:
			folderName: name of the selected folder
		"""
		self.setOk(False)
		for i in range(1, self.form.rowCount()):
			self.form.removeRow(1)
		houseSelector = qw.QComboBox()
		houseSelector.setPlaceholderText("Select House")
		houseSelector.setCurrentIndex(-1)
		houseSelector.addItem("Community")
		for i in range(len(self.community)):
			houseName = self.community[i]["house"]
			houseLabel = str(i) + " - " + houseName
			houseSelector.addItem(houseLabel)
		houseSelector.currentTextChanged.connect(\
			lambda houseName: self.houseSelected(folderName, houseName))
		self.form.addRow("House:", houseSelector)

	def houseSelected(self, folderName, houseName):
		"""
		Handles the selection of the house containing the CSV

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house ('Community' for file not in a house folder)
		"""
		self.setOk(False)
		for i in range(2, self.form.rowCount()):
			self.form.removeRow(2)
		if houseName == "Community":
			focusSelector = qw.QComboBox()
			focusSelector.setPlaceholderText("Select Focus")
			focusSelector.setCurrentIndex(-1)
			focusSelector.addItem("Community")
			focusSelector.addItem("Community Baseload")
			focusSelector.addItem("Community Not Baseload")
			focusSelector.addItem("Energy")
			focusSelector.addItem("Netload")
			focusSelector.currentTextChanged.connect(\
				lambda focus: self.communityFocusSelected(folderName, focus))
			self.form.addRow("Focus:", focusSelector)
		else:
			houseNo = int(houseName[:houseName.find(" ")])
			focusSelector = qw.QComboBox()
			focusSelector.setPlaceholderText("Select Focus")
			focusSelector.setCurrentIndex(-1)
			focusSelector.addItem("Activity")
			focusSelector.addItem("Appliance")
			focusSelector.addItem("Baseload")
			focusSelector.addItem("Person")
			focusSelector.addItem("Total")
			focusSelector.currentTextChanged.connect(\
				lambda focus: self.houseFocusSelected(folderName, houseName, houseNo, focus))
			self.form.addRow("Focus:", focusSelector)
	
	def communityFocusSelected(self, folderName, focus):
		"""
		Handles selection of a focus from the 'Community'

		Args:
			folderName: name of the selected folder
			focus: selected focus
		"""
		self.setOk(False)
		if focus == "Netload":
			self.netloadSelected(folderName)
		else:
			self.focusFileSelected(folderName, None, None, focus)

	def houseFocusSelected(self, folderName, houseName, houseNo, focus):
		"""
		Handles selection of a focus from a house folder

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house
			houseNo: number of the house in the json file
			focus: selected focus
		"""
		self.setOk(False)
		for i in range(3, self.form.rowCount()):
			self.form.removeRow(3)

		if focus == "Activity":
			self.activitySelected(folderName, houseName, houseNo)
		elif focus == "Appliance":
			self.applianceSelected(folderName, houseName, houseNo)
		elif focus == "Baseload":
			self.focusFileSelected(folderName, houseName, houseNo, focus)
		elif focus == "Person":
			self.personSelected(folderName, houseName, houseNo)
		elif focus == "Total":
			self.focusFileSelected(folderName, houseName, houseNo, focus)
		else:
			raise ValueError("invalid focus value")

	def netloadSelected(self, folderName):
		"""
		Handles selection of the Netload focus

		Args:
			folderName: name of the selected folder
		"""
		netloadPath = self.folders[folderName] + "/netload.csv"
		file = open(netloadPath)
		variables = sorted(file.readline().split(";")[1:], key=str.casefold) # all variables except the date
		file.close()
		variableSelector = qw.QComboBox()
		variableSelector.setPlaceholderText("Select Variable")
		variableSelector.setCurrentIndex(-1)
		for variable in variables:
			variableSelector.addItem(variable.replace("_", " ").replace("\n", ""))
		variableSelector.currentTextChanged.connect(\
			lambda variable: self.netloadBuildPath(folderName, netloadPath, variable))
		self.form.addRow("Variable:", variableSelector)

	def activitySelected(self, folderName, houseName, houseNo):
		"""
		Handles selection of the activity focus

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house
			houseNo: number of the house in the json file
			focus: selected focus
		"""
		# getting all relevant activities
		activityModels = []
		for schedule in self.community[houseNo]["schedules"]:
			for activity in schedule["activities"]:
				if activity["model"] not in activityModels:
					activityModels.append(activity["model"])
		antgenPath = str(antgen.__path__).split('[')[1].split("]")[0].replace("'", "")
		activities = []
		for model in activityModels:
			modelPath = antgenPath + "/activities/" + model
			if not isfile(modelPath):
				raise ValueError("path to activity model not found")
			modelFile = open(modelPath, 'r')
			reading = modelFile.readline()
			name = None
			while reading != "":
				nameStr = "name = "
				idx = reading.find(nameStr) 
				if idx != -1:
					# found the name
					name = reading[idx + len(nameStr):-1]
					modelFile.close()
					break
				reading = modelFile.readline()
			if name is None:
				raise ValueError("name not found")
			activities.append(name)

		activities.sort()
		activitySelector = qw.QComboBox()
		activitySelector.setPlaceholderText("Select Activity")
		activitySelector.setCurrentIndex(-1)
		for activity in activities:
			activitySelector.addItem(activity)
		activitySelector.currentTextChanged.connect(\
			lambda name: self.activityBuildPath(folderName, houseName, houseNo, name))
		self.form.addRow("Activity:", activitySelector)

	def applianceSelected(self, folderName, houseName, houseNo):
		"""
		Handles selection of the appliance focus

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house
			houseNo: number of the house in the json file
			focus: selected focus
		"""
		# getting all relevant activities
		activityModels = []
		for schedule in self.community[houseNo]["schedules"]:
			for activity in schedule["activities"]:
				if activity["model"] not in activityModels:
					activityModels.append(activity["model"])
		antgenPath = str(antgen.__path__).split('[')[1].split("]")[0].replace("'", "")
		appliances = []
		for model in activityModels:
			modelPath = antgenPath + "/activities/" + model
			if not isfile(modelPath):
				raise ValueError("path to activity model not found")
			modelFile = open(modelPath, 'r')
			reading = modelFile.readline()
			name = None
			inCorrectLines = False
			hasBeenCorrect = False
			while reading != "":
				if reading[0] == '[':
					if reading == "[devices]\n":
						inCorrectLines = True
						hasBeenCorrect = True
					else:
						inCorrectLines = False
				elif inCorrectLines:
					equalStr = " = "
					idx = reading.find(equalStr) 
					if idx != -1:
						# getting the name from the line where it is
						name = reading[idx + len(equalStr):-1]
						if name not in appliances:
							appliances.append(name)
				elif not inCorrectLines and hasBeenCorrect:
					break
				reading = modelFile.readline()

		appliances.sort()
		applianceSelector = qw.QComboBox()
		applianceSelector.setPlaceholderText("Select Appliance")
		applianceSelector.setCurrentIndex(-1)
		for appliance in appliances:
			applianceSelector.addItem(appliance)
		applianceSelector.currentTextChanged.connect(\
			lambda name: self.applianceBuildPath(folderName, houseName, houseNo, name))
		self.form.addRow("Appliance:", applianceSelector)

	def personSelected(self, folderName, houseName, houseNo):
		"""
		Handles selection of the person focus

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house
			houseNo: number of the house in the json file
			focus: selected focus
		"""
		people = sorted(self.community[houseNo]["people"])
		personSelector = qw.QComboBox()
		personSelector.setPlaceholderText("Select Person")
		personSelector.setCurrentIndex(-1)
		for person in people:
			if person != "baseload": # baseload is not a real person and has its own section
				personSelector.addItem(person)
		personSelector.currentTextChanged.connect(\
			lambda name: self.personBuildPath(folderName, houseName, houseNo, name))
		self.form.addRow("Person:", personSelector)

	def focusFileSelected(self, folderName, houseName, houseNo, focus):
		"""
		Handles selection of a focus when the focus is directly a file 
		i.e. Baseload or Total or Community files

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house
			houseNo: number of the house in the json file
			focus: selected focus
		"""
		h = "" if houseNo is None else "/house" + str(houseNo) 
		path = self.folders[folderName] + h + "/" + focus.lower().replace(" ", "_") +".csv"
		if houseName:
			self.setSelection(folderName, focus, houseName, path)
		else:
			self.setSelection(folderName, focus, path = path)

	def netloadBuildPath(self, folderName, path, variable):
		"""
		Builds the path when the focus is Netload

		Args:
			folderName: name of the selected folder
			path: path to the netload.csv file
			variable: name of the selected column
		"""
		variableFormat = variable.replace(" ", "_")
		self.setSelection(folderName, variable, path = path, var = variableFormat)

	def activityBuildPath(self, folderName, houseName, houseNo, name):
		"""
		Builds path when the focus is Activity

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house
			houseNo: number of the house in the json file
			name: name of the activity
		"""
		formatName = name.replace(" ", "_")
		path = self.folders[folderName] + "/house" + str(houseNo) + "/" + formatName + ".csv"
		self.setSelection(folderName, name, houseName, path)

	def applianceBuildPath(self, folderName, houseName, houseNo, name):
		"""
		Builds path when the focus is Appliance

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house
			houseNo: number of the house in the json file
			name: name of the appliance
		"""
		formatName = name.upper().replace(" ", "")
		path = self.folders[folderName] + "/house" + str(houseNo) + "/" + formatName + ".csv"
		self.setSelection(folderName, name, houseName, path)

	def personBuildPath(self, folderName, houseName, houseNo, name):
		"""
		Builds path when the focus is Persons

		Args:
			folderName: name of the selected folder
			houseName: name of the selected house
			houseNo: number of the house in the json file
			name: name of the person
		"""
		path = self.folders[folderName] + "/house" + str(houseNo) + "/" + name + ".csv"
		self.setSelection(folderName, name, houseName, path)

class ExternalCsvSelector(qw.QWidget):
	def __init__(self):
		"""
		Widget to select the path to CSV files outside of the simulation
		"""
		super().__init__()

		self.selection = None

		self.btnFile = qw.QPushButton("No File")
		self.btnFile.clicked.connect(self.chooseFile)

		self.form = qw.QFormLayout()
		self.form.addRow("File:", self.btnFile)

		formWidget = qw.QWidget()
		formWidget.setLayout(self.form)

		self.ok = False
		self.btnOk = qw.QPushButton("Ok")
		self.btnOk.setCheckable(True)
		self.btnOk.setChecked(True)
		self.btnOk.clicked.connect(self.btnOkClicked)

		self.btnCancel = qw.QPushButton("Cancel")
		self.btnCancel.clicked.connect(self.cancelled.emit)

		layout = qw.QGridLayout()
		layout.addWidget(formWidget, 0, 0, 1, -1)

		layout.addWidget(self.btnCancel, 1, 0, 1, 1)
		layout.addWidget(self.btnOk, 1, 1, 1, 1)

		self.setLayout(layout)

	madeSelection = qc.Signal(str, str, str, str, str)
	cancelled = qc.Signal()

	def warnInvalidCsv(self):
		"""
		Shows a message box warning the CSV is invalid
		"""
		errorPopup = qw.QMessageBox()
		errorPopup.setWindowTitle("Warning")
		errorPopup.setText("Please select a CSV containing the 'Date' column and at least one column with power.")
		errorPopup.exec()

	def btnOkClicked(self):
		"""
		Finishes the selection if all needed fields have been selected
		"""
		if self.ok:
			folderName, name, house, path, var = self.selection
			self.madeSelection.emit(folderName, name, house, path, var)
		else:
			self.setOk(False)

	def setOk(self, val):
		"""
		Sets if the selection is ready to be finished

		Args:
			val: if it's ok or not to finish
		"""
		self.ok = val
		self.btnOk.setChecked(not val)

	def chooseFile(self):
		"""
		Open a QFileDialog to choose the file
		"""
		path = qw.QFileDialog.getOpenFileName(caption = "Choose CSV File", filter = "CSV File (*.csv)")[0]
		if path == "":
			return

		df = pd.read_csv(path, sep = ";")
		if len(df.columns) < 2 or df.columns[0] != "Date":
			self.warnInvalidCsv()
			return

		self.setOk(False)

		idx = path.rfind("/") + 1 # if it doesn't find a '/' it will be 0, if it does it will skip the '/'
		self.btnFile.setText(path[idx:])

		for i in range(1, self.form.rowCount()):
			self.form.removeRow(1)
		columnSelector = qw.QComboBox()
		columnSelector.setPlaceholderText("Select Column")
		columnSelector.setCurrentIndex(-1)
		for col in df.columns[1:]:
			columnSelector.addItem(col)
		columnSelector.currentTextChanged.connect(\
			lambda name: self.setSelection(path, col, idx))
		self.form.addRow("Column:", columnSelector)

	def setSelection(self, path, col, idx):
		"""
		Sets the selection of the CSV

		Args:
			path: path to the selected CSV
			col: name of the column of interest in the CSV file
			idx: index to character of the path string where the file name begins
		"""
		fileName = path[idx:]
		self.selection = ("External", col, fileName, path, col)
		self.setOk(True)	

class CsvSelector(qw.QTabWidget):
	def __init__(self, paths):
		"""
		Widget with tabs enabling the selection of CSV from the simulation and outside of it

		Args:
			paths: dictionary with relevant paths
		"""
		super().__init__()

		internal = InternalCsvSelector(paths)
		internal.cancelled.connect(self.cancelled.emit)
		internal.madeSelection.connect(self.madeSelection.emit)
		external = ExternalCsvSelector()
		external.cancelled.connect(self.cancelled.emit)
		external.madeSelection.connect(self.madeSelection.emit)

		self.addTab(internal, "Internal CSV")
		self.addTab(external, "External CSV")

	cancelled = qc.Signal()
	madeSelection = qc.Signal(str, str, str, str, str)

	def resizeEvent(self, event): # makes the tabs occupy the full width of the widget
		"""
		Override of parent method
		"""
		self.tabBar().setFixedWidth(self.width())
		super().resizeEvent(event)

class PopupCsvSelector(qw.QDialog):
    def __init__(self, paths):
        """
        Window containing the CSV Selector

        Args:
        	paths: dictionary with relevant paths
        """
        super().__init__()

        self.setWindowTitle("Select Parameter")
        self.selector = CsvSelector(paths)
        self.selector.cancelled.connect(self.close)
        self.selector.madeSelection.connect(self.select)

        layout = qw.QVBoxLayout()
        layout.addWidget(self.selector)

        self.setLayout(layout)

	# folderName, name, house, path, var
    selected = qc.Signal(str, str, str, str, str)

    def select(self, folderName, name, house, path, var):
    	"""
    	Signal the selection of a CSV file and close the window

    	Args:
    		folderName: folder containing the file
    		name: name of the file
    		house: house where the file is from ('Community' if oustide a house folder)
    		path: path to the CSV file
    		var: column of the CSV file to use
    	"""
    	self.selected.emit(folderName, name, house, path, var)
    	self.close()

class LineList(qw.QWidget):
	def __init__(self):
		"""
		Widget containing widgets (LineWdiget or ParamWidget) in a vertical arrangement
		"""
		super().__init__()
		l = qw.QVBoxLayout()
		l.setAlignment(qc.Qt.AlignTop)
		self.setLayout(l)

	def addWidget(self, widget):
		"""
		Add a widget to the line list

		Args:
			widget: widget to add
		"""
		self.layout().addWidget(widget)

class LineWidget(qw.QPushButton):
	def __init__(self, name, params):
		"""
		Widget that contains information about a created line

		Args:
			name: name given to the line
			params: list of parameters used to create the line
		"""
		super().__init__(name)
		self.lineName = name
		self.params = []
		self.clicked.connect(self.edit)

		for param in params:
			pName, folder, house = param.labelParts
			path = param.path
			column = param.column
			idx = len(self.params)
			negative = param.negative
			self.params.append((pName, folder, house, path, column, idx, negative))


	removeRequest = qc.Signal(int)
	editRequest = qc.Signal(qw.QWidget) #can't specify LineWidget here

	def index(self):
		"""
		Returns:
			index of the line on the LineList
		"""
		return self.parent().layout().indexOf(self)

	def remove(self):
		"""
		Request removal of the line form the list
		"""
		self.removeRequest.emit(self.index())

	def edit(self):
		"""
		Request editing of the line's parameters
		"""
		self.editRequest.emit(self)

	def setLineName(self, name):
		"""
		Sets the name of the line

		Args:
			name: name to set
		"""
		self.lineName = name
		self.setText(name)

	def setParams(self, params):
		"""
		Sets received the parameters on a list

		Args:
			params: parameters to organise on the list
		"""
		self.params = []
		for param in params:
			pName, folder, house = param.labelParts
			path = param.path
			column = param.column
			idx = len(self.params)
			negative = param.negative
			self.params.append((pName, folder, house, path, column, idx, negative))

	def createDf(self):
		"""
		Returns:
			dataframe from the lines parameters
		"""
		params = self.params
		df = pd.read_csv(params[0][3], sep = ";")
		for col in df.columns:
			if col != "Date" and col != params[0][4]:
				df.drop(col, inplace=True, axis=1)
		df.columns = ["Date", "Power"]

		if params[0][6]:
			df["Power"] = df["Power"].mul(-1)

		for param in params[1:]:
			paramDf = pd.read_csv(param[3], sep = ";")
			for col in paramDf.columns:
				if col != "Date" and col != param[4]:
					paramDf.drop(col, inplace=True, axis=1)
			paramDf.columns = ["Date", "Power"]

			isMinus = param[6]

			if isMinus:
				df["Power"] = df["Power"].sub(paramDf["Power"], fill_value=0)
			else:
				df["Power"] = df["Power"].add(paramDf["Power"], fill_value=0)
				
		return df


class LineLister(qw.QScrollArea):
	def __init__(self):
		"""
		Scroll Area to contain all the created lines
		"""
		super().__init__()
		self.setWidgetResizable(True)
		lineList = LineList()
		self.setWidget(lineList)

	editRequest = qc.Signal(LineWidget)

	def addLine(self, name, params):
		"""
		Add a line to the list

		Args:
			name: name of the line
			params: parameters that define the line
		"""
		lw = LineWidget(name, params)
		lw.removeRequest.connect(self.removeLine)
		lw.editRequest.connect(self.editLine)
		self.widget().addWidget(lw)

	def removeLine(self, idx):
		"""
		Remove a line from the list

		Args:
			idx: index of the line on the LineList
		"""
		item = self.widget().layout().takeAt(idx)
		item.widget().deleteLater()

	def editLine(self, line):
		"""
		Request editing of a line

		Args:
			line: LineWidget to edit
		"""
		self.editRequest.emit(line)

	def countLines(self):
		"""
		Returns:
			number of lines in the LineList
		"""
		return self.widget().layout().count()

	def getLines(self):
		"""
		Returns:
			list of all the LineWidgets
		"""
		lines = []
		for i in range(self.countLines()):
			line = self.widget().layout().itemAt(i).widget()
			lines.append(line)
		return lines

class ParamWidget(qw.QWidget):
	def __init__(self, name, folder, house, path, column, idx, negative = False):
		"""
		Widget to represent a parameter that defines a line

		Args:
			name: name of the CSV
			folder: name of folder containing the CSV
			house: name of the house containing the CSV
			path: path to the CSV
			column: column of interest in the CSV
			negative: if the values of the CSV are to be subtracted on the final line
		"""
		super().__init__()
		self.labelParts = (name, folder, house)
		self.path = path
		self.column = column # column of the csv file to use
		self.negative = negative # if we are going to subtract these values in the creation of the line

		self.btnSign = qw.QPushButton(" ")
		self.setSign(idx)
		self.btnSign.clicked.connect(self.changeSign)
		label = self.__buildLabel()
		btnRemove = qw.QPushButton("X")
		btnRemove.clicked.connect(self.remove)
		layout = qw.QHBoxLayout()
		layout.addWidget(self.btnSign)
		layout.addWidget(label)
		layout.addWidget(btnRemove)
		self.setLayout(layout)

	removeRequest = qc.Signal(int)
	changedSign = qc.Signal()

	def __buildLabel(self):
		"""
		Creates a widget to textually represent the parameter
		"""
		w = qw.QWidget()
		l = qw.QGridLayout()
		name, folder, house = self.labelParts
		nameFormat = name if len(name) <= 24 else name[0:24-3]+'...'
		# labels, settings in the style sheet
		nameLab = qw.QLabel(nameFormat)
		folderLab = qw.QLabel(folder)
		houseLab = qw.QLabel(house)
		nameLab.setObjectName("nameLab")
		folderLab.setObjectName("folderLab")
		houseLab.setObjectName("houseLab")

		l.addWidget(nameLab, 0, 1)
		l.addWidget(folderLab, 0, 0)
		l.addWidget(houseLab, 0, 2)
		l.setColumnStretch(0, 3)
		l.setColumnStretch(1, 1)
		l.setColumnStretch(2, 3)
		w.setLayout(l)
		return w

	def index(self):
		"""
		Returns:
			the index of the parameter in the LineList
		"""
		return self.parent().layout().indexOf(self)

	def changeSign(self):
		"""
		Switches between + and - as to indicate if the values from this parameter are to be added or subtracted
		"""
		self.negative = not self.negative
		self.setSign()
		self.changedSign.emit()

	def setSign(self, idx = None):
		"""
		Sets the operation sign of the parameter

		Args:
			idx: index of the parameter in the LineList
		"""
		if idx == None: #at creation parent is not yet set, thus index() cannot be used
			idx = self.index()
		txt = None
		if self.negative:
			txt = "-"
		else:
			if  idx == 0:
				txt = " "
			else:
				txt = "+"
		self.btnSign.setText(txt)

	def remove(self):
		self.removeRequest.emit(self.index())

class ParamList(qw.QScrollArea):
	def __init__(self):
		"""
		Scroll Area to contain all the created parameters
		"""
		super().__init__()
		self.setWidgetResizable(True)
		lineList = LineList()
		self.setWidget(lineList)

	changed = qc.Signal()

	def addParam(self, folderName, name, houseName, path, var, idx = None, negative = None):
		"""
		Add a parameter to the list

		Args:
			folderName: name of the folder containing the CSV file
			name: name of the CSV file
			houseName: name of the house containing the CSV file
			path: path to the CSV file
			var: columns of interest of the CSV file
			idx: index of the parameter in the LineList
			negative: if the values of the parameter are to be subtracted when creating the line
		"""
		pw = None
		if idx is None or negative is None:
			pw = ParamWidget(name, folderName, houseName, path, var, self.nextIndex())
		else:
			pw = ParamWidget(name, folderName, houseName, path, var, idx, negative)
		pw.removeRequest.connect(self.removeParam)
		pw.removeRequest.connect(self.hasChanged)
		pw.changedSign.connect(self.hasChanged)
		self.widget().addWidget(pw)

	def removeParam(self, idx):
		"""
		Remove a parameter from the list

		Args:
			idx: index of the parameter on the LineList
		"""
		item = self.widget().layout().takeAt(idx)
		item.widget().deleteLater()
		if idx == 0:
			i = self.widget().layout().itemAt(idx)
			if i is not None:
				i.widget().setSign()

	def nextIndex(self):
		"""
		Retruns:
			the index of the next parameter to add to the list/ the list's length
		"""
		return self.widget().layout().count()

	def getParams(self):
		"""
		Returns:
			list of all the ParamWidgets
		"""
		params = []
		for i in range(self.nextIndex()):
			param = self.widget().layout().itemAt(i).widget()
			params.append(param)
		return params

	def hasChanged(self):
		"""
		Signals that the list has changed
		"""
		self.changed.emit()

class LineSpecifier(qw.QWidget):
	def __init__(self, paths):
		"""
		Widget with the controls to create or edit LineWidgets from the CSVs of the simulation

		Args:
			paths: dictionary with relevant paths
		"""
		super().__init__()
		self.changed = None
		self.line = None
		self.nameLineEdit = None
		self.paramList = None
		self.paths = paths
		self.createNew()

	lineCreated = qc.Signal(str, list)

	def deleteAndReplaceLayout(self, newLayout):
		"""
		Method to switch the layouts of the LineSpecifier

		Args:
			newLayout: the layout to switch to
		"""
		currentLayout = self.layout()
		if currentLayout:
			while currentLayout.count():
				item = currentLayout.takeAt(0)
				widget = item.widget()
				if widget:
					widget.deleteLater()
			currentLayout.destroyed.connect(lambda: self.setLayout(newLayout))
			currentLayout.deleteLater()
		else:
			self.setLayout(newLayout)

	def createNew(self):
		"""
		Shows the controls to create a line
		"""
		self.nameLineEdit = qw.QLineEdit()
		paramAddBtn = qw.QPushButton("Add")
		paramAddBtn.clicked.connect(self.popupCsvSelector)
		form = qw.QFormLayout()
		form.addRow("Name:", self.nameLineEdit)
		form.addRow("Parameters:", paramAddBtn)
		formWidget = qw.QWidget()
		formWidget.setLayout(form)

		self.paramList = ParamList()

		btnCancel = qw.QPushButton("Cancel")
		btnCancel.clicked.connect(self.cancel)

		btnCreate = qw.QPushButton("Create Line")
		btnCreate.clicked.connect(self.create)

		layout = qw.QGridLayout()
		layout.addWidget(formWidget, 0, 0, 1, -1)
		layout.addWidget(self.paramList, 1, 0, 1, -1)
		layout.addWidget(btnCancel, 2, 0, 1, 1)
		layout.addWidget(btnCreate, 2, 1, 1, 1)
		self.deleteAndReplaceLayout(layout)

	def colapseDown(self):
		"""
		Hides the creation/editing controls
		"""
		btnAdd = qw.QPushButton("Add Line")
		btnAdd.clicked.connect(self.addLine)

		layout = qw.QGridLayout()
		layout.addWidget(btnAdd, 0, 0, 1, -1)
		self.deleteAndReplaceLayout(layout)
		self.paramList = None
		self.nameLineEdit = None
		self.changed = None
		self.line = None

	def editLine(self, line):
		"""
		Shows controls to edit the line

		Args:
			line: LineWidget to edit
		"""
		self.changed = False
		self.line = line
		self.nameLineEdit = qw.QLineEdit()
		self.nameLineEdit.setText(line.lineName)
		paramAddBtn = qw.QPushButton("Add")
		paramAddBtn.clicked.connect(self.popupCsvSelector)
		# an attempt at not doing anything if nothing is changed
		# very simple should change later
		self.nameLineEdit.textChanged.connect(self.hasChanged)
		paramAddBtn.clicked.connect(self.hasChanged)

		form = qw.QFormLayout()
		form.addRow("Name:", self.nameLineEdit)
		form.addRow("Parameters:", paramAddBtn)
		formWidget = qw.QWidget()
		formWidget.setLayout(form)

		self.paramList = ParamList()
		self.paramList.changed.connect(self.hasChanged)

		for param in self.line.params:
			name, folder, house, path, column, idx, negative = param
			self.paramList.addParam(folder, name, house, path, column, idx, negative)

		btnDelete = qw.QPushButton("Delete")
		btnDelete.clicked.connect(self.delLine)

		btnCancel = qw.QPushButton("Cancel")
		btnCancel.clicked.connect(self.cancel)

		btnSave = qw.QPushButton("Save")
		btnSave.clicked.connect(self.save)

		layout = qw.QGridLayout()
		layout.addWidget(formWidget, 0, 0, 1, -1)
		layout.addWidget(self.paramList, 1, 0, 1, -1)
		layout.addWidget(btnDelete, 2, 0, 1, 1)
		layout.addWidget(btnCancel, 2, 1, 1, 1)
		layout.addWidget(btnSave, 2, 2, 1, 1)
		self.deleteAndReplaceLayout(layout)

	def hasChanged(self):
		"""
		Changes the value to signal the line has been edited
		"""
		self.changed = True

	def delLine(self):
		"""
		Removes the line
		"""
		self.line.remove()
		self.colapseDown()

	def addLine(self):
		"""
		Shows the controls to add a line
		"""
		self.createNew()

	def popupCsvSelector(self):
		"""
		Pops up the window for the selection of a CSV file
		"""
		popup = PopupCsvSelector(self.paths)
		popup.selected.connect(self.addParam)
		popup.exec()

	def addParam(self, folderName, name, houseName, path, var):
		"""
		Adds a parameter to the ParamList

		Args:
			folderName: name of the folder containing the CSV file
			name: name of the CSV file
			houseName: name of the house containing the CSV file
			path: path to the CSV file
			var: columns of interest of the CSV file
		"""
		if self.paramList == None:
			return
		self.paramList.addParam(folderName, name, houseName, path, var)

	def cancel(self):
		"""
		Closes the parameter editor without saving
		"""
		self.colapseDown()

	def create(self):
		"""
		Adds this line to the list
		"""
		if not self.okCondition():
			errorPopup = qw.QMessageBox()
			errorPopup.setWindowTitle("Warning")
			errorPopup.setText("Line must have a Name and at least one Parameter.")
			errorPopup.exec()
			return
		p = self.paramList.getParams()
		self.lineCreated.emit(self.nameLineEdit.text(), p)
		self.colapseDown()

	def save(self):
		"""
		Saves changes made to the line while editing it
		"""
		if self.changed:
			if not self.okCondition():
				errorPopup = qw.QMessageBox()
				errorPopup.setWindowTitle("Warning")
				errorPopup.setText("Line must have a Name and at least one Parameter.")
				errorPopup.exec()
				return
			self.line.setLineName(self.nameLineEdit.text())
			self.line.setParams(self.paramList.getParams())

		self.colapseDown()

	def okCondition(self):
		"""
		Returns:
			if it all the condition are met to create a line
		"""
		return self.nameLineEdit.text() and self.paramList.nextIndex() > 0

class GraphParamSelector(qw.QWidget):
	def __init__(self, paths):
		"""
		Widget for the creation of dataframes through the creation of multiple lines from the simulation's CSV files
		
		Args:
			paths: dictionary with relevant paths
		"""
		super().__init__()

		self.lineLister = LineLister()
		self.lineSpec = LineSpecifier(paths)
		self.lineLister.editRequest.connect(self.lineSpec.editLine)
		self.lineSpec.lineCreated.connect(self.lineLister.addLine)
		btnProduceGraph = qw.QPushButton("Produce Graph")
		btnProduceGraph.clicked.connect(self.produceDf)

		layout = qw.QVBoxLayout()
		layout.addWidget(self.lineLister)
		layout.addWidget(self.lineSpec)
		layout.addWidget(btnProduceGraph)
		self.setLayout(layout)

	dataframeCreated = qc.Signal(pd.core.frame.DataFrame)

	def produceDf(self):
		"""
		Creates a dataframe containing the information of all the lines
		Returns the dataframe through a signal
		"""
		if self.lineLister.countLines() <= 0:
			errorPopup = qw.QMessageBox()
			errorPopup.setWindowTitle("Warning")
			errorPopup.setText("Your graph must have at least one Line.")
			errorPopup.exec()
			return
		if self.lineSpec.paramList is not None:
			errorPopup = qw.QMessageBox()
			errorPopup.setWindowTitle("Warning")
			errorPopup.setText("Finish selecting your Parameters before producing the graph.")
			errorPopup.exec()
			return
		lines = self.lineLister.getLines()
		colNames = ["Date", lines[0].lineName]
		df = lines[0].createDf()
		dupPreventor = {lines[0].lineName: 0}
		for l in lines[1:]:
			name = l.lineName
			if dupPreventor.get(name) is None:
				dupPreventor[name] = 0
			else:
				dupPreventor[name] += 1
				name = f"{name} ({dupPreventor[name]})"

			colNames.append(name)
			df2 = l.createDf()
			df = df.merge(df2, on = "Date", suffixes = ("", "_"+name))
		df.columns = colNames
		print("Created dataframe")
		self.dataframeCreated.emit(df)

if __name__ == '__main__':
	app = qw.QApplication([])

	widget = GraphParamSelector()
	widget.show()

	sys.exit(app.exec())