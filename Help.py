import sys
from PySide6 import QtCore as qc, QtWidgets as qw, QtGui as qg

from Settings import Settings

class HelpWidget(qw.QWidget):
	def __init__(self, name, labels):
		"""
		Base widget to use when creating tabs with help

		Args:
			name: Name of the tabs that will contain this HelpWidget
			labels: list of QLabels to display
		"""
		super().__init__()

		self.name = name

		layout = qw.QVBoxLayout()
		for l in labels:
			layout.addWidget(l)
		self.setLayout(layout)

class HelpProcsim(HelpWidget):
	def __init__(self):
		"""
		Information about what's PROCSIM
		"""
		super().__init__("About", [LabelProcsim()])
		
class LabelProcsim(qw.QLabel):
	def __init__(self):
		"""
		Label about PROCSIM
		"""
		super().__init__(
			"""The PROCSIM simulator is an open source python energy community simulator to develop and evaluate load balancing schemes designed to allow researchers of this field to easily create ECs datasets for multiple purposes as well as test and evaluate their load balancing strategies."""
			)
		self.setWordWrap(True)

class HelpHome(HelpWidget):
	def __init__(self):
		"""
		Information about the Home screen
		"""
		super().__init__("Home", [LabelHome(), LabelCommunities()])

class LabelHome(qw.QLabel):
	def __init__(self):
		"""
		Label about the Home Menu
		"""
		super().__init__(
			"""Use the Home Menu to access PROCSIM's different functionalities.""")
		self.setWordWrap(True)

class LabelCommunities(qw.QLabel):
	def __init__(self):
		"""
		Label about the selection of Communities
		"""
		super().__init__(
			"""Select an energy community from the folder selected in the settings.
To the right of each community you'll find information on the number of days that were simulated and optimized using that community."""
			)
		self.setWordWrap(True)

class HelpSim(HelpWidget):
	def __init__(self):
		"""
		Information about the EC Simulator
		"""
		super().__init__("ECSimulator", [LabelSim(), LabelSimOptions(), LabelResults("the simulation")])

class LabelSim(qw.QLabel):
	def __init__(self):
		"""
		Label about the Simulator
		"""
		super().__init__(
			"""Use the ECSimulator to simulate the consumption of the community."""
			)
		self.setWordWrap(True)

class LabelSimOptions(qw.QLabel):
	def __init__(self):
		"""
		Label about the simulation options
		"""
		super().__init__("""Options:
	Days: Select the number of days to simulate;
	Skip Consumption Generator: Used to only re-simulate the Renewable Energy of the community (on already simulated communities);
	Solar Data From File: Used so the Renewable Energy Generation uses a file instead of accessing the internet for solar data (select the file to use in the settings)."""
		)
		self.setWordWrap(True)

class LabelResults(qw.QLabel):
	def __init__(self, source):
		"""
		Label about the Result Screen

		Args:
			source: string related to which tab this Label is being shown in (e.g. Simulator, Optimizer, etc.)
		"""
		super().__init__(f"""View the results of {source}.
Contains multiple graphs with information about {source}.
You can click the graphs to open them on a separate window and save them to the computer."""
		)
		self.setWordWrap(True)

class HelpOptim(HelpWidget):
	def __init__(self):
		"""
		Information about the EC Optimizer
		"""
		super().__init__("ECOptimizer", [LabelOptim(), LabelOptimOptions(), LabelResults("the optimization")])

class LabelOptim(qw.QLabel):
	def __init__(self):
		"""
		Label about the Optimizer
		"""
		optims = Settings.optimizationNames()
		super().__init__(
			f"""Use the ECOptimizer to optimize the consumption of the community through the {f"{', '.join(optims[:-1])} and {optims[-1]}"} optimization methods."""
			)
		self.setWordWrap(True)

class LabelOptimOptions(qw.QLabel):
	def __init__(self):
		"""
		Label about the optimisation options
		"""
		super().__init__("""Options:
	Days: Select the number of days simulated in the simulation you want to optimize."""
	)
		self.setWordWrap(True)

class HelpOverview(HelpWidget):
	def __init__(self):
		"""
		Information about the Overview screen
		"""
		super().__init__("Overview", [LabelResults("every simulation and optimization of a community"), LabelCustomGraph()])

class LabelCustomGraph(qw.QLabel):
	def __init__(self):
		"""
		Label about the Custom Graph
		"""
		super().__init__(
			"""Create graphs your own graphs.
Custom graphs can be saved to CSV files.
Use the right mouse button to toggle between time series and totals.
To create a graph, specify the lines you want to see by adding parameters to the line.
Parameters are chosen from the simulation/ optimization files (Internal CSV) or from computer files (External CSV).
Within a line the parameters can be added or subtracted."""
			)
		self.setWordWrap(True)

class Help(qw.QDialog):
	def __init__(self):
		"""
		Dialog with help
		"""
		super().__init__()

		widgets = [HelpProcsim(), HelpHome(), HelpSim(), HelpOptim(), HelpOverview()]
		self.setWindowTitle("Help")

		self.tabs = qw.QTabWidget()
		for w in widgets:
			self.tabs.addTab(w, w.name)
		layout = qw.QVBoxLayout() 
		layout.addWidget(self.tabs)
		self.setLayout(layout)

	def sizeHint(self):
		"""
		Override of parent method
		"""
		hint = qc.QSize()
		hint.setHeight(500)
		hint.setWidth(700)
		return hint

	def resizeEvent(self, event): # makes the tabs occupy the full width of the widget
		"""
		Override of parent method
		"""
		self.tabs.tabBar().setFixedWidth(self.width())
		super().resizeEvent(event)