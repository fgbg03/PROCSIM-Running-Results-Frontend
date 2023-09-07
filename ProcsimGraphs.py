import sys
import matplotlib
import json
import numpy as np

from os.path import isfile

import PySide6.QtWidgets as qw
import PySide6.QtCore as qc

import matplotlib.pyplot as plt
import pandas as pd
import datetime

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from procsimulator.Evaluation import Evaluation

from ClickableGraph import ClickableGraph
from Settings import Settings

class Worker(qc.QObject):
    def __init__(self, func):
        """
        Class to create graphs in a thread

        Args:
            func: funtion used to create the graph
        """
        super().__init__()
        self.func = func

    finished = qc.Signal()

    def run(self):
        """
        Create the graph
        """
        self.func()
        self.finished.emit()

class PreloadedGraph(ClickableGraph):
    def __init__(self, func, thread = False, left = 0.125, right = 0.9, top = 0.9, bottom = 0.11):
        super().__init__(placeholderText = "Loading Image", left = left, right = right, top = top, bottom = bottom)
        """
        Class of graphs that come with a function to create their image

        Args:
            func: function used to create the graph
            thread: whether to create this graph in a thread (not advised, use if intensive calculations are needed, may not be reliable)
            left: size of the left margin
            right: size of the right margin
            top: size of the top margin
            bottom: size of the bottom margin
        """
        if thread:
            #create graph and show it through a thread
            self.thread = qc.QThread()
            self.worker = Worker(func)
            #move to thread
            self.worker.moveToThread(self.thread)
            #connect to start
            self.thread.started.connect(self.worker.run)
            #connect to worker finished
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            #connect to thread finished
            self.thread.finished.connect(self.thread.deleteLater)
            #run
            self.thread.start()
        else:
            func()

    def buildPathName(self, paths):
        """
        Build a dictionary with paths to simulation/optimisation folders associated with names to diplay for each one

        Args:
            paths: dicitonary of useful paths

        Returns:
            dictionary with paths and names {path: name}, if any path was not provided in the argument, there will be a None key
        """
        pathName = {paths.get("minute"): "Original"}

        for i, optName in enumerate(Settings.optimizationNames()):
            pathName[paths.get(f"met{i}opt1")] = f"{optName} Opt."
            pathName[paths.get(f"met{i}opt2")] = f"2nd {optName} Opt."
            
        return pathName

#isto talvez seja igual para todos, mas existem ficheiros análogos em todas as pastas, talvez possam mudar se a flexibilidade for maior, é melhor manter
class BaseloadGraph(PreloadedGraph):
    def __init__(self, community, paths):
        """
        Graph of the baseload taken from PROCSIM's ConsumptionGenerator for each optimisation

        Args:
            community: reading of the community's json file
            min_folder: path of the resampled consumption profiles (at 1/60Hz)
        """
        self.community = community
        self.paths = paths
        super().__init__(self.set_community_baseload_graph)

    def set_community_baseload_graph(self):
        """
        Creates the graph of the baseload for each optimisation
        """
        community = self.community
        paths = self.paths

        pathName = self.buildPathName(paths)
        baseloadSuf = '/community_baseload.csv'
        notBaseloadSuf = '/community_not_baseload.csv'
        baselineSuf = '/community_not_baseload.csv'
        
        pathsToUse = []

        for path in pathName:
            if path is None:
                continue
            if isfile(path + baseloadSuf):
                pathsToUse.append(path)
        
        graphs = len(pathsToUse)

        if graphs == 0:
            print("NO BASELOAD DATA")
            return

        fig, axes = plt.subplots(graphs)

        num_houses = len(community)
        for i, path in enumerate(pathsToUse):
            baseload = pd.read_csv(path + baseloadSuf, sep=';')["Power"]
            not_baseload = pd.read_csv(path + notBaseloadSuf, sep=';')["Power"]
            baseline = pd.read_csv(path + baselineSuf, sep=';')["Power"]
            
            minutes = len(baseload.index)
            labels = list(range(0, minutes))

            baseline_val = 0
            for x in range(num_houses):
              baseline_val += int(community[x]["contracted_power"] * 1000 * 0.01)

            baseline.iloc[0:minutes] = baseline_val
            width = 0.35  # the width of the bars: can also be len(x) sequence

            if graphs != 1:
                #ax.plot(labels, baseload, width, label='Non-Flexible')
                axes[i].stackplot(labels, baseline, baseload, not_baseload, labels=['Baseline', 'Non-Flexible', 'Flexible'])
                if i == graphs - 1:
                    axes[i].set_xlabel('Time (min)')
                axes[i].set_ylabel('Power (W)')
                axes[i].set_title(f'{pathName[path]} Baseload')
                axes[i].legend()
            else:
                #ax.plot(labels, baseload, width, label='Non-Flexible')
                axes.stackplot(labels, baseline, baseload, not_baseload, labels=['Baseline', 'Non-Flexible', 'Flexible'])
                axes.set_xlabel('Time (min)')
                axes.set_ylabel('Power (W)')
                axes.set_title(f'{pathName[path]} Baseload')
                axes.legend()

        
        print("BASELOADGRAPH")
        self.showGraphFromFigure(fig)

class HouseGraph(PreloadedGraph):
    def __init__(self, paths, houseNo = '0', community = None):
        """
        Graph comparing a house's consumption across different optimisations

        Args:
            paths: dictionary of relevant paths
            houseNo: number of the house in the community file
            community: reading of the community's json file
        """
        self.paths = paths
        self.houseNo = houseNo
        self.community = community
        super().__init__(self.set_house_total_graph, left = 0.1975, bottom = 0.15)

    def set_house_total_graph(self):
        """
        Creates the graph using the existing total.csv files of all optimisations 
        """
        paths = self.paths 
        houseNo = self.houseNo
        community = self.community
        
        pathName = self.buildPathName(paths)

        suf = f"/house{houseNo}/total.csv"
        
        colNames = []
        df = None
        first = True

        for path in pathName.keys():
            if path is None:
                continue
            filePath = path + suf
            if isfile(filePath):
                if first:
                    colNames = ["Date", pathName[path]]
                    df = pd.read_csv(filePath, sep = ";")
                    first = False
                else:
                    df2 = pd.read_csv(filePath, sep = ";")
                    df = df.merge(df2, on = "Date", suffixes = ("", "_"+pathName[path]))
                    colNames.append(pathName[path])

        if df is None:
            print(f"HOUSE {houseNo} NO DATAFRAME")
            return

        df.columns = colNames

        self.showGraphFromDf(df)
        title = None
        if community is None:
            title = f"House {houseNo}"
        else:
            title = f"{houseNo} - {community[int(houseNo)]['house']}"
        if len(title) > 30:
            title = title[:30 - 3] + "..."
        self.ax.set_title(title)
        self.ax.legend(prop={'size': 6}, fancybox=True, borderaxespad=0.)
        print("HOUSE"+str(houseNo))

        #creating space by rotating the x and y labels
        axesList = self.figure.get_axes()
        for ax in axesList:
            ax.tick_params(axis = 'y', labelrotation = 60)
            ax.tick_params(axis = 'x', labelrotation = -30)

class SelfSufficiencyGraph(PreloadedGraph):
    def __init__(self, paths):
        """
        Graph comparing different optimisations' self sufficiency and self consumption

        Args:
            paths: dictionary of relevant paths
        """
        self.paths = paths
        super().__init__(self.set_self_suf_graph)

    def set_self_suf_graph(self):
        """
        Uses PROCSIM's Evaluation module to calculate self sufficiency and self consumption across all optimisations that have files
        """
        paths = self.paths

        pathName = self.buildPathName(paths)

        usedFolder = []
        selfSufList = []
        selfConsList = []
        for path in pathName.keys():
            if path is None:
                continue
            filePath = path + "/netload.csv"
            if isfile(filePath):
                df = pd.read_csv(filePath, sep=';')
                df.columns = ['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload']
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date')

                ev = Evaluation(None, df)

                usedFolder.append(pathName[path])
                selfSufList.append(ev.get_self_sufficiency()*100)
                selfConsList.append(ev.get_self_consumption()*100)

        fig, ax = plt.subplots()

        barWidth = 0.4

        x_axis = np.arange(len(usedFolder))
        
        ax.bar(x_axis - barWidth/2, selfSufList, barWidth, label = "Self.Suf. (%)")
        ax.bar(x_axis + barWidth/2, selfConsList, barWidth, label = "Self.Cons. (%)") 

        ax.set_xticks(x_axis)
        ax.set_xticklabels(usedFolder)
        ax.set_title("Self Sufficiency and Self Consumption")
        ax.set_ylabel("")
        ax.set_xlabel("")
        ax.legend()   

        print("SELFSUFFICIENCYGRAPH")
        self.showGraphFromFigure(fig)   

class TimeslotsGraph(PreloadedGraph):
    def __init__(self, paths, houseNo = '0', community = None):
        """
        Graph comparing different optimisations' timeslot placement (only accounts for flexible appliances since every other is fixed)

        Args:
            paths: dictionary of relevant paths
        """
        self.paths = paths
        self.houseNo = houseNo
        self.left = 0.1975
        self.bottom = 0.15
        self.community = community
        super().__init__(self.set_timeslots_graph, left = self.left, bottom = self.bottom)

    def set_timeslots_graph(self):
        """
        Creates graph comparing different optimisations' timeslot placement
        """
        def width_calc(i, hyperbola=False):
            """
            Gives the width of a bar for the graph in order to show overlapping bars
            
            Args:
                i: how many bars are overlapped in this position
                hyperbola: whether to use a hyperbolic function to determine the width (useful if the number gets larger, as it never reaches 0)

            Returns:
                value of the width
            """
            if not hyperbola:
                if i <=4:
                    return 0.8 - 0.1*i
                if i <= 8:
                    return 0.8 - 0.1*4 - 0.05*(i-4)
                else:
                    return width_calc(i+2,hyperbola=True) # i+2 so it's smaller than the previous width
            else: #use hyperbolic function
                return 0.8/(0.3*i+1)

        def buildTimeslotDict(filePath, maxDay, allAppliances):
            """
            Builds the dictionary with the timeslot infromation from a file
            Counts the number of days the timeslots occupy
            Updates the list of appliances used in the timeslots

            Args:
                path: path to the file with the timeslot information
                maxDay: the number of the highest day a timeslot was placed in until now
                allAppliances: list of appliances to update

            Returns:
                [0] dictionary with timeslot information {appliance_name: [(start, end), ...], ...}
                [1] highest day a timeslot was placed in
            """
            timeslot = {}
            with open(filePath, "r") as f:
                r = f.readline()
                while r != "":
                    idx = r.find("(")
                    applianceName = r[:idx]
                    slots = []
                    r = r[idx:]
                    while r != "\n": # reading (HH:MM-hh:mm,DAY)...
                        idx = r.find(")")
                        day = int(r[13:idx]) #day of the timeslot to integer
                        maxDay = day if day > maxDay else maxDay #update maxDay
                        start = 24*(day-1)+int(r[1:3])+int(r[4:6])/60 #first timestamp to float
                        end = 24*(day-1)+int(r[7:9])+int(r[10:12])/60 #second timestamp to float
                        slots.append((start,end))
                        r = r[idx+1:] # new '(' or '\n'
                    timeslot[applianceName] = slots
                    if applianceName not in allAppliances:
                        allAppliances.append(applianceName)
                    r = f.readline()
            return timeslot, maxDay

        paths = self.paths
        houseNo = self.houseNo

        pathName = self.buildPathName(paths)

        filePaths = {}
        n = 0
        for path in pathName.keys():
            if path == None:
                continue
            fp = f"{path}/house{houseNo}/timeslots"
            if isfile(fp):
                n += 1
                filePaths[pathName[path]] = fp 
        
        multi = n > 1 # changes the colouring of the graph depending on the number of paths used
                
        if n == 0: #no timeslots found
            print("NO TIMESLOTS FOUND") #the app should not try to create these if there are no files
            return

        tims = {}
        maxDay = 1
        allAppliances = []
        for name in filePaths.keys():
            tims[name], d = buildTimeslotDict(filePaths[name], maxDay, allAppliances)
            maxDay = max(d, maxDay)

        applianceNumbers = {}
        applianceNo = 0
        for a in sorted(allAppliances):
            applianceNumbers[a] = applianceNo
            applianceNo += 1

        fig, ax = plt.subplots()
        fig.subplots_adjust(left = self.left, bottom = self.bottom)
        #drawing the timeslots
        for i, folder in enumerate(tims):
            tim = tims[folder]
            for j, appliance in enumerate(tim):
                for k, slots in enumerate(tim[appliance]):
                    if j == 0 and k == 0: #Only add a label the first time a bar is added in a given folder
                        ax.barh(applianceNumbers[appliance],width=slots[1]-slots[0],left=slots[0],color=f"C{i if multi else applianceNumbers[appliance]}", 
                            height=width_calc(i),label=folder)
                    else:
                        ax.barh(applianceNumbers[appliance],width=slots[1]-slots[0],left=slots[0],color=f"C{i if multi else applianceNumbers[appliance]}",
                            height=width_calc(i))

        if self.community is None:
            ax.set_title(f"House {houseNo} Timeslots")
        else:
            ax.set_title(f"{houseNo} - {self.community[int(houseNo)]['house']} Timeslots")
        #set y ticks to the applinces' names
        tim1 = tims[list(tims.keys())[0]] #example timeslots to extract data from
        ax.set_yticks(range(len(tim1)))
        ax.set_yticklabels(tim1.keys())
        #set x ticks to HH:MM
        ticks = range(0, 24*maxDay+1, 2*maxDay)  #tick every 2*maxDay hours
        ax.set_xticks(ticks)
        ax.set_xticklabels(map(lambda x: f"{x%24:02d}:00", ticks))
        if multi:
            ax.legend(prop={'size': 6}, fancybox=True, borderaxespad=0.)

        #rotate labels
        axesList = fig.get_axes()
        for ax in axesList:
            ax.tick_params(axis = 'y', labelrotation = 30)
            ax.tick_params(axis = 'x', labelrotation = -40)

        print(f"TIMESLOTS{houseNo}")
        self.showGraphFromFigure(fig)
"""
class FlexGraph(PreloadedGraph): #This graph causes a lot of delay and I'm not even sure it's useful
    def __init__(self, min_folder="output/minute", ao_folder="output/afteroptimization", \
        a2o_folder="output/aftersecoptimization"):
        super().__init__(lambda: self.set_flexibility_evolution_graph(min_folder, ao_folder, a2o_folder), True)

    def set_flexibility_evolution_graph(self, min_folder, ao_folder, a2o_folder):
        path = [[min_folder, ao_folder],[a2o_folder,a2o_folder]]
        # fig, ax1 = plt.subplots()
        fig, axes = plt.subplots(nrows=2, ncols=2, constrained_layout=True, )

        for p in range(2):
            for j in range(2):

                abc = pd.read_csv(path[p][j] + '/netload.csv', sep=';')
                #abc.columns = ['Date', 'Demand', 'Production', 'Netload']
                abc.columns = ['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload'] #teste
                abc.drop('PV_Production', inplace=True, axis=1) #teste
                abc.drop('Wind_Production', inplace=True, axis=1) #teste
                abc.drop('Netload', inplace=True, axis=1)
                abc.drop('Demand', inplace=True, axis=1)
                # abc.drop('Production', inplace=True, axis=1)

                abc.set_index('Date')

                tim1 = pd.read_csv(path[p][j] + '/house0/WASHINGMACHINE.csv', sep=';')
                # tim1['Power'] = tim1['Power'] + 62.1 * 30;
                tim1 = tim1.rename(columns={"Power": "Timeslot 1 - Washing Machine - House 0"})
                tim1.set_index('Date')

                tim2 = pd.read_csv(path[p][j] + '/house3/DISHWASHER.csv', sep=';')
                # tim10['Power'] = tim10['Power'] + 62.1 * 30
                tim2 = tim2.rename(columns={"Power": "Timeslot 2 - Dishwasher - House 3"})
                tim2.set_index('Date')

                tim3 = pd.read_csv(path[p][j] + '/house4/WASHINGMACHINE.csv', sep=';')
                # tim3['Power'] = tim3['Power'] + 62.1 * 30
                tim3 = tim3.rename(columns={"Power": "Timeslot 3 - Washing Machine - House 4"})
                tim3.set_index('Date')

                df = pd.merge(pd.merge(pd.merge(abc, tim1, on='Date', how='left'), tim2, on='Date', how='left'), tim3,
                              on='Date',
                              how='left')
                df.set_index('Date')

                df['Time'] = df['Date'].map(
                    lambda x: datetime.datetime.strptime(str(x), "%Y-%m-%d %H:%M:%S").strftime("%H:%M"))

                axes[p, j].set_xlabel('Time')
                axes[p, j].set_ylabel('Power (W)', color='red')
                plt1 = axes[p, j].plot(df['Time'], df["Timeslot 1 - Washing Machine - House 0"], color='red',
                                       label='Timeslot 1 - Washing Machine - House 0')
                plt2 = axes[p, j].plot(df['Time'], df["Timeslot 2 - Dishwasher - House 3"], color='green',
                                       label='Timeslot 2 - Dishwasher - House 3')
                plt3 = axes[p, j].plot(df['Time'], df["Timeslot 3 - Washing Machine - House 4"], color='orange',
                                       label='Timeslot 3 - Washing Machine - House 4')
                axes[p, j].axis(ymin=-280, ymax=7500)
                # ax1.set_xticks(df['Time'])
                # ax1.tick_params(axis='y', labelcolor='red')

                # Adding Twin Axes

                ax2 = axes[p, j].twinx()

                ax2.set_ylabel('Production (W)', color='blue')
                plt4 = ax2.plot(df['Time'], df["Production"], color='blue', label='Production')

                # ax1.get_shared_y_axes().join(ax1, ax3)

                # adds space between x values because there are a lot of different values for the x-axis and not all of them can be displayed
                # ref. https://stackoverflow.com/questions/48251417/matplotlib-plots-multiple-dark-lines-on-x-axis
                spacing = 500
                visible = axes[p, j].xaxis.get_ticklabels()[::spacing]
                for label in axes[p, j].xaxis.get_ticklabels():
                    if label not in visible:
                        label.set_visible(False)
                visible = axes[p, j].xaxis.get_ticklines()[::spacing]
                for label in axes[p, j].xaxis.get_ticklines():
                    if label not in visible:
                        label.set_visible(False)

                # join labels of both axis (ax1 and ax2)
                plts = plt1 + plt2 + plt3 + plt4
                labs = [l.get_label() for l in plts]
                axes[p, j].legend(plts, labs, loc=2, prop={'size': 6})

            # ax.get_xaxis().set_visible(False)
            # Show plot

        axes[0, 0].set_title("A) Flexibility of 25%")
        axes[0, 1].set_title("B) Flexibility of 50%")
        axes[1, 0].set_title("C) Flexibility of 75%")
        axes[1, 1].set_title("D) Flexibility of 100%")
        
        print("FLEXGRAPH")
        self.showGraphFromFigure(fig)
"""