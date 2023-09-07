import sys
import matplotlib

from PySide6 import QtWidgets as qw, QtCore as qc, QtGui as qg

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure

class PopupGraph(qw.QDialog):
    def __init__(self, canvas):
        """
        QDialog containing a canvas with a figure to show and a button to save it as a file

        Args:
            canvas: FigureCanvas to show
        """
        super().__init__()

        self.setSizeGripEnabled(True)

        self.setWindowTitle("Popup Graph")
        #setting to default margins
        canvas.figure.subplots_adjust(left = 0.125, right = 0.9, top = 0.9, bottom = 0.11)
        self.canvas = canvas
        self.btnSave = qw.QPushButton("Save Graph to File")

        layout = qw.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.btnSave)

        self.setLayout(layout)

        self.btnSave.clicked.connect(self.openFolderDialog)

    def spoofResize(self):
        """
        Simulates a resize event
        """
        #para contornar um erro onde a o gráfico desformata após abertura de nova janela 
        #força-se a redimensão o ecrã de modo a ele tornar a formatar
        resize_event = qg.QResizeEvent(self.canvas.size(),self.canvas.size())
        self.canvas.resizeEvent(resize_event)

    def openFolderDialog(self):
        """
        Opens QFileDialog to select the path to save the file to
        """
        acceptedExtensions = (".jpeg", ".jpg", ".png", ".webp", ".pdf")
        fileName, selectedFilter = qw.QFileDialog.getSaveFileName(caption="Save Graph to File", dir ="untitled", 
            filter="JPEG File (*.jpeg *.jpg);; PNG File (*.png);; WEBP File (*.webp);; PDF File (*.pdf)")
        if fileName == "":
            return # cancelled
        index = fileName.rfind('.')
        if index == -1:
            extension = selectedFilter[selectedFilter.rfind('.'):selectedFilter.rfind(')')]
            fileName += extension
            print(extension)
            print(fileName)
        else:
            fileExtension = fileName[index:]
            if fileExtension not in acceptedExtensions:
                error_message = f"{fileExtension} is not a valid extension. Please select any of the following extensions: {' '.join(acceptedExtensions)}"
                qw.QMessageBox.critical(None, "Error saving file", error_message)
                return
        self.canvas.figure.savefig(fileName)

class CustomPopupGraph(PopupGraph):
    def __init__(self, canvas, dataframe):
        """
        QDialog containing a canvas with a figure to show and a button to save it as a file
        Adds ability to save graphs to csv files

        Args:
            canvas: FigureCanvas to show
            dataframe: dataframe of the graph being shown (to save to csv if needed)
        """
        super().__init__(canvas)
        self.df = dataframe

    def openFolderDialog(self):
        """
        Opens QFileDialog to select the path to save the file to
        Capable of saving the CustomGraph's dataframe to a csv file
        """
        acceptedExtensions = (".csv", ".jpeg", ".jpg", ".png", ".webp", ".pdf")
        fileName, selectedFilter = qw.QFileDialog.getSaveFileName(caption="Save Graph to File", dir ="untitled", 
            filter="CSV File (*.csv);; JPEG File (*.jpeg *.jpg);; PNG File (*.png);; WEBP File (*.webp);; PDF File (*.pdf)")
        if fileName == "":
            return # cancelled
        index = fileName.rfind('.')
        if index == -1:
            extension = selectedFilter[selectedFilter.rfind('.'):selectedFilter.rfind(')')]
            fileName += extension
            print(extension)
            print(fileName)
        else:
            fileExtension = fileName[index:]
            if fileExtension not in acceptedExtensions:
                error_message = f"{fileExtension} is not a valid extension. Please select any of the following extensions: {' '.join(acceptedExtensions)}"
                qw.QMessageBox.critical(None, "Error saving file", error_message)
                return
        if fileName[fileName.rfind("."):] == ".csv":
            self.df.to_csv(fileName, sep = ";", index = False)
        else:
            self.canvas.figure.savefig(fileName)

class ClickableGraph(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, placeholderText = None, 
        left = 0.125, right = 0.9, top = 0.9, bottom = 0.11):
        """
        FigureCanvas widget capable of being clicked to show the graph in a popup window

        Args:
            parent: parent widget
            width: width of the figure
            height: height of the figure
            dpi: dpi of the figure
            placeholderText: text to be displayed in the canvas before determining the final figure
            left: size of the left margin
            right: size of the right margin
            top: size of the top margin
            bottom: size of the bottom margin
        """
        self.bool_var = True
        self.x_label = "Time"
        self.y_label = "Power (W)"
        self.clickable = False
        self.margins = (left, right, top, bottom)

        self.figure = Figure(figsize=(width, height), dpi=dpi)
        if placeholderText is not None:
            #text explaining the image is loading
            ax = self.figure.subplots()
            ax.text(0.5,0.5, placeholderText, fontsize = 18, ha = "center")
        
        #setting margins
        self.figure.subplots_adjust(left = self.margins[0], right = self.margins[1], top = self.margins[2], bottom = self.margins[3])
            

        super(ClickableGraph, self).__init__(self.figure)

        policy = qw.QSizePolicy()
        policy.setHorizontalPolicy(qw.QSizePolicy.MinimumExpanding)
        policy.setVerticalPolicy(qw.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(policy)

    def sizeHint(self):
        """
        Override of parent method
        """
        hint = qc.QSize()
        hint.setHeight(300)
        hint.setWidth(300)
        return hint

    def closeFigure(self):
        """
        Closes the matplotlib figure
        """
        plt.close(self.figure)

    def enableClicks(self):
        """
        Enables the graph to be clicked
        """
        self.clickable = True
        if self.underMouse(): # caso o rato já esteja sobre o widget quando é ligado
            self.setCursor(qc.Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        """
        Override of parent method to open popup on click
        """
        if not self.clickable:
            return
        if event.button() == qc.Qt.LeftButton:
            self.openCanvasWindow()
            self.figure.subplots_adjust(left = self.margins[0], right = self.margins[1], top = self.margins[2], bottom = self.margins[3])
            self.spoofResize()

    def spoofResize(self):
        """
        Simulates a resize event
        """
        #para contornar um erro onde a o gráfico desformata após abertura de nova janela 
        #força-se a redimensão o ecrã de modo a ele tornar a formatar
        resize_event = qg.QResizeEvent(self.size(),self.size())
        self.resizeEvent(resize_event)

    def enterEvent(self, event):
        """
        Override parent method to change mouse cursor
        """
        if not self.clickable:
            return
        self.setCursor(qc.Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """
        Override parent method to change mouse cursor
        """
        self.unsetCursor()

    def openCanvasWindow(self):
        """
        Shows the graph in a popup window
        """
        popup = PopupGraph(FigureCanvas(self.figure))
        geom = qg.QGuiApplication.primaryScreen().availableGeometry()
        side = min(geom.width(), geom.height())
        popup.resize(side,side)
        popup.exec()

    def showGraphFromDf(self, df):
        """
        Show a graph in the canvas from a dataframe

        Args:
            df: dataframe to use
        """
        self.figure.clear()
        self.ax = self.figure.add_subplot()

        df["Date"] = pd.to_datetime(df["Date"]).dt.time.apply(lambda x: x.strftime("%H:%M"))
        df.set_index("Date").plot(ax=self.ax, linewidth=1.5)
        #df.plot(ax=self.ax)

        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)

        self.draw()
        self.enableClicks()        

    def showGraphFromFigure(self, fig):
        """
        Show a graph in the canvas from a matplotlib figure

        Args:
            fig: figure to use
        """
        self.figure.clear()
        self.figure = fig
        #self.draw() # assim o gráfico não aparece com o tamanho correto => spoofResize funciona
        self.spoofResize()

        self.enableClicks()

    def change(self):
        """
        test method to change between two graphs
        """
        self.figure.clear()
        ax = self.figure.add_subplot()
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        if self.bool_var:
            self.showGraphFromDf(self.graf1())
        else:
            ax.plot([1,2,3], [2,7,6], color="green", label="_test")
        #grafico
        self.draw()
        self.bool_var = not self.bool_var

    def graf1(self): #gráfico aleatório retirado do Simulator.py
        """
        test method

        Returns:
            sample graph
        """
        df = pd.read_csv('output/minute/netload.csv', sep=';')
        df.columns = ['Date', 'Demand', 'PV_Production', 'Wind_Production', 'Production', 'Netload']
        df.drop('Netload', inplace=True, axis=1)
        df.set_index('Date')
        return df

class CustomGraph(ClickableGraph):
    def __init__(self):
        """
        Graph intended to receive dataframes and is able to show the totals of those dataframes' columns
        """
        super().__init__()
        
        self.dataframe = None
        self.totals = None
        self.isOnDataframe = False

    def mousePressEvent(self, event):
        """
        Check for opening the graph popup or to change to total bar graph
        """
        super().mousePressEvent(event)

        if event.button() == qc.Qt.RightButton:
            if self.dataframe is not None:
                if self.isOnDataframe:
                    self.dfToTotal()
                else:
                    self.showGraphFromDf(self.dataframe)

    def showGraphFromDf(self, df):
        """
        Overrides the superclass's function.
        Adds whiping of the prior graph from memory and saves values unique to this class
        """
        plt.close() #since the graph will cycle through multiple figures they should be closed

        self.dataframe = df
        self.isOnDataframe = True

        super().showGraphFromDf(df)

    def dfToTotal(self):
        """
        Show a bar graph in the canvas by summing the values of each column of the current dataframe
        """
        df = self.dataframe
        newCols = df.columns[1:] #'Date' column is to be ignored
        totals = [0]*len(newCols)
        for i, col in enumerate(newCols):
            totals[i] = df[col].sum()

        fig, ax = plt.subplots()
        barlist = ax.bar(newCols, totals, 0.4)

        for n, bar in enumerate(barlist):
            # CN -> default matplotlib colours, so the bars match the colour of the line they're representing
            bar.set_color(f"C{n}")

        ax.set_title("Total")
        ax.set_ylabel("Power (W)")

        self.showGraphFromFigure(fig)
        self.isOnDataframe = False

    def openCanvasWindow(self):
        """
        Overrides parent method.
        Shows the graph in a popup window with class dedicated to custom graphs
        """
        popup = CustomPopupGraph(FigureCanvas(self.figure), self.dataframe)
        geom = qg.QGuiApplication.primaryScreen().availableGeometry()
        side = min(geom.width(), geom.height())
        popup.resize(side,side)
        popup.exec()