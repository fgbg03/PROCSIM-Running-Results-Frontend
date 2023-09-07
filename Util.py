from Settings import Settings

from os.path import isfile

class Util:
	@staticmethod
	def fileName(path):
		"""
		Args:
			path: path to the desired file
		Returns:
			name of a file from a given path with no extension
		"""
		return path.split("/")[-1][:path.split("/")[-1].rfind(".")]

	@staticmethod
	def infoFile(name):
		"""
		Args:
			name: name or path to the desired file
		Returns:
			path to the .info file of the community
		"""
		if "." in name:
			name = Util.fileName(name)
		return f"{Settings.getOutputPath()}/{name}.info"

	@staticmethod
	def loggedDays(name):
		"""
		Args:
			name: name or path to the desired file
		Returns:
			list of the number of days (in string format) used in the file's simulations
		"""
		file = Util.infoFile(name)

		if not isfile(file):
			return []
		with open(file, "r") as f:
			loggedDays = f.read().split("\n")[:-1] #last line will be empty, so ignore it

		return loggedDays

	@staticmethod
	def daysString(days):
		"""
		Args:
			days: number of simulated days in string format

		Returns:
			The number of days with the string 'day' or 'days' (according to the number) in front
		"""
		s = "" if days == "1" else "s"
		return f"{days} day{s}"