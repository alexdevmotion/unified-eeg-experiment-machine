from Tkinter import *
from classes import Helpers
from time import time
import Queue
import tkFileDialog
import datetime


class GUI:
    def __init__(self, tk, threadedTasks):
        self.tk = tk
        self.threadedTasks = threadedTasks
        self.keepCheckingWirelessStrength = False
        self.goFrameBuilt = False
        self.imageWindowDestroyed = True
        self.wirelessStrength = -1

        Label(self.tk, text="Supported headsets: Emotiv Insight").pack(anchor=W)

        donglePresentFrame = Frame()
        donglePresentLabel = Label(donglePresentFrame, text="Dongle present: ")
        donglePresentLabel.pack(side=LEFT)
        self.donglePresentCanvas = Canvas(donglePresentFrame, width=60, height=30)
        self.donglePresentCanvas.pack(side=RIGHT)
        self.donglePresentRectangle = self.donglePresentCanvas.create_rectangle(0, 0, 100, 100, fill="black")
        donglePresentFrame.pack(anchor=W)

        wirelessStrengthFrame = Frame()

        wirelessStrengthLabel = Label(wirelessStrengthFrame, text="Wireless strength: ")
        wirelessStrengthLabel.pack(side=LEFT)
        self.wirelessStrengthCanvas = Canvas(wirelessStrengthFrame, width=40, height=20)
        self.wirelessStrengthCanvas.pack(side=LEFT)
        self.wirelessStrengthRectangle = self.wirelessStrengthCanvas.create_rectangle(0, 0, 100, 100, fill="black")

        batteryLevelLabel = Label(wirelessStrengthFrame, text="Battery level: ")
        batteryLevelLabel.pack(side=LEFT)
        self.batteryLevelVar = StringVar(self.tk)
        batteryLevel = Label(wirelessStrengthFrame, textvariable=self.batteryLevelVar)
        batteryLevel.pack(side=LEFT)

        wirelessStrengthFrame.pack(anchor=W)

        contactQualityFrame = Frame()
        # AF3, T7, Pz, T8, AF4
        af3Label = Label(contactQualityFrame, text="AF3: ")
        af3Label.pack(side=LEFT)
        self.af3Canvas = Canvas(contactQualityFrame, width=20, height=20)
        self.af3Canvas.pack(side=LEFT)
        self.af3Circle = self.af3Canvas.create_oval(2, 2, 20, 20, fill="black")
        t7Label = Label(contactQualityFrame, text="  T7: ")
        t7Label.pack(side=LEFT)
        self.t7Canvas = Canvas(contactQualityFrame, width=20, height=20)
        self.t7Canvas.pack(side=LEFT)
        self.t7Circle = self.t7Canvas.create_oval(2, 2, 20, 20, fill="black")
        pzLabel = Label(contactQualityFrame, text="  Pz: ")
        pzLabel.pack(side=LEFT)
        self.pzCanvas = Canvas(contactQualityFrame, width=20, height=20)
        self.pzCanvas.pack(side=LEFT)
        self.pzCircle = self.pzCanvas.create_oval(2, 2, 20, 20, fill="black")
        t8Label = Label(contactQualityFrame, text="  T8: ")
        t8Label.pack(side=LEFT)
        self.t8Canvas = Canvas(contactQualityFrame, width=20, height=20)
        self.t8Canvas.pack(side=LEFT)
        self.t8Circle = self.t8Canvas.create_oval(2, 2, 20, 20, fill="black")
        af4Label = Label(contactQualityFrame, text="  AF4: ")
        af4Label.pack(side=LEFT)
        self.af4Canvas = Canvas(contactQualityFrame, width=20, height=20)
        self.af4Canvas.pack(side=LEFT)
        self.af4Circle = self.af4Canvas.create_oval(2, 2, 20, 20, fill="black")
        contactQualityFrame.pack(anchor=W)

        self.updateDongleThread()

        self.tk.mainloop()

    def updateDongleThread(self):
        resultQueue = Queue.Queue()
        self.threadedTasks.checkDonglePresent(resultQueue).join()
        result = resultQueue.get()
        self.donglePresentCanvas.itemconfig(self.donglePresentRectangle, fill="black" if result == 0 else "green")
        if result:
            self.keepCheckingWirelessStrength = True
            self.buildBrowseButtonFrame()
            self.buildFolderInfoFrame()
            self.buildImageIntervalFrame()
            self.buildTotalTimeFrame()
            self.buildCropImagesFrame()
            self.buildSubjectNameFrame()
            self.tk.after(100, self.updateWirelessThread)

    def getFillForWirelessStrength(self, wirelessStrength):
        if wirelessStrength == 1:
            return "orange"
        elif wirelessStrength == 2:
            return "green"
        return "black"

    def getFillForContactQuality(self, contactQuality):
        if contactQuality == 1:
            return "red"
        elif contactQuality == 2:
            return "yellow"
        elif contactQuality == 3:
            return "orange"
        elif contactQuality == 4:
            return "green"
        return "black"

    def updateWirelessThread(self):
        resultQueue = Queue.Queue()
        self.threadedTasks.getWirelessStrengthBatteryLevelContactQuality(resultQueue).join()
        result = resultQueue.get()

        self.wirelessStrength = result[0]
        self.wirelessStrengthCanvas.itemconfig(self.wirelessStrengthRectangle, fill=self.getFillForWirelessStrength(self.wirelessStrength))

        self.batteryLevelVar.set(result[1])

        self.af3Canvas.itemconfig(self.af3Circle, fill=self.getFillForContactQuality(result[2]))
        self.t7Canvas.itemconfig(self.t7Circle, fill=self.getFillForContactQuality(result[3]))
        self.pzCanvas.itemconfig(self.pzCircle, fill=self.getFillForContactQuality(result[4]))
        self.t8Canvas.itemconfig(self.t8Circle, fill=self.getFillForContactQuality(result[5]))
        self.af4Canvas.itemconfig(self.af4Circle, fill=self.getFillForContactQuality(result[6]))

        self.showHideGoFrame()
        if self.keepCheckingWirelessStrength:
            self.tk.after(100, self.updateWirelessThread)

    def buildBrowseButtonFrame(self):
        browseButtonFrame = Frame()
        browseButton = Button(browseButtonFrame, text="Choose experiment folder", command=self.onBrowseDirectory)
        browseButton.pack(side=LEFT)
        self.browseDirectoryVar = StringVar(self.tk)
        browseDirectoryLabel = Label(browseButtonFrame, textvariable=self.browseDirectoryVar)
        browseDirectoryLabel.pack(side=LEFT)
        browseButtonFrame.pack(anchor=W)

    def buildFolderInfoFrame(self):
        folderInfoFrame = Frame()
        folderInfoLabel = Label(folderInfoFrame, text="Number of images in folder: ")
        folderInfoLabel.pack(side=LEFT)
        self.folderInfoNoFilesVar = StringVar(self.tk)
        folderInfoNoFiles = Label(folderInfoFrame, textvariable=self.folderInfoNoFilesVar)
        folderInfoNoFiles.pack(side=LEFT)
        folderInfoFrame.pack(anchor=W)

    def buildImageIntervalFrame(self):
        imageIntervalFrame = Frame()
        imageIntervalLabel = Label(imageIntervalFrame, text="Image display interval (s): ")
        imageIntervalLabel.pack(side=LEFT)
        self.imageIntervalVar = StringVar(self.tk)
        imageIntervalEntry = Entry(imageIntervalFrame, textvariable=self.imageIntervalVar)
        imageIntervalEntry.pack(side=LEFT)
        imageIntervalFrame.pack(anchor=W)
        imageIntervalEntry.insert(0, "5")
        self.imageIntervalVar.trace('w', self.onChange)

    def buildTotalTimeFrame(self):
        totalTimeFrame = Frame()
        totalTimeLabel = Label(totalTimeFrame, text="Experiment duration: ")
        totalTimeLabel.pack(side=LEFT)
        self.totalTimeVar = StringVar(self.tk)
        totalTime = Label(totalTimeFrame, textvariable=self.totalTimeVar)
        totalTime.pack(side=LEFT)
        totalTimeFrame.pack(anchor=W)

    def buildCropImagesFrame(self):
        cropImagesFrame = Frame()
        self.cropImagesVar = IntVar(self.tk)
        cropImages = Checkbutton(cropImagesFrame, text="Crop and resize images to fill screen", variable=self.cropImagesVar)
        self.cropImagesVar.set(1)
        cropImages.pack(side=LEFT)
        cropImagesFrame.pack(anchor=W)

    def buildSubjectNameFrame(self):
        subjectNameFrame = Frame()
        subjectNameLabel = Label(subjectNameFrame, text="Subject name: ")
        subjectNameLabel.pack(side=LEFT)
        self.subjectNameVar = StringVar(self.tk)
        subjectNameEntry = Entry(subjectNameFrame, textvariable=self.subjectNameVar, width=50)
        subjectNameEntry.pack(side=LEFT)
        subjectNameFrame.pack(anchor=W)
        self.subjectNameVar.trace('w', self.onChange)

    def buildGoFrame(self):
        self.goFrame = Frame()
        goButton = Button(self.goFrame, text="GO", command=self.go)
        goButton.config(height=3, width=25)
        goButton.pack(side=LEFT)
        self.goFrame.pack(anchor=W)
        self.goFrameBuilt = True

    def destroyGoFrame(self):
        if self.goFrameBuilt:
            self.goFrame.pack_forget()
            self.goFrameBuilt = False

    def isWirelessStrengthValid(self):
        return self.wirelessStrength > 0

    def isImageDirectoryValid(self):
        noFiles = self.folderInfoNoFilesVar.get()
        return noFiles and int(noFiles) > 0

    def isImageIntervalValid(self):
        imageInterval = self.imageIntervalVar.get()
        return Helpers.representsInt(imageInterval) and int(imageInterval) > 0

    def isSubjectNameValid(self):
        subjectName = self.subjectNameVar.get()
        return len(subjectName) > 0

    def showHideGoFrame(self):
        if self.isWirelessStrengthValid() and self.isImageDirectoryValid() and self.isImageIntervalValid() and self.isSubjectNameValid():
            if not self.goFrameBuilt:
                self.buildGoFrame()
        else:
            self.destroyGoFrame()

    def updateTotalTime(self):
        if self.isImageDirectoryValid() and self.isImageIntervalValid():
            imageInterval = int(self.imageIntervalVar.get())
            noFiles = int(self.folderInfoNoFilesVar.get())
            seconds = imageInterval * noFiles
            if seconds < 60:
                self.totalTimeVar.set(str(seconds) + "s")
            else:
                self.totalTimeVar.set(str(seconds/60) + "m" + str(seconds % 60) + "s")
        else:
            self.totalTimeVar.set("")

    def onChange(self, a, b, c):
        self.showHideGoFrame()
        self.updateTotalTime()

    def onBrowseDirectory(self):
        dir = tkFileDialog.askdirectory()
        self.browseDirectoryVar.set(dir)
        noFiles = Helpers.getNoImagesInDirectory(dir)
        self.folderInfoNoFilesVar.set(noFiles)
        self.onChange(None, None, None)

    def go(self):
        dir = self.browseDirectoryVar.get()
        images = Helpers.getImagesInDirectory(dir)
        imageInterval = int(self.imageIntervalVar.get())
        crop = int(self.cropImagesVar.get())

        self.imageWindow = Helpers.ImageWindow(self.tk, dir, images, imageInterval, self.threadedTasks, crop)

        self.tk.after(100, self.startDisplayingImagesAndLoggingToFileSimultaneously)

        self.imageWindow.window.mainloop()

    def startDisplayingImagesAndLoggingToFileSimultaneously(self):
        dir = str(self.browseDirectoryVar.get())
        subjectName = self.subjectNameVar.get()
        dayHourStr = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
        imageInterval = int(self.imageIntervalVar.get())
        csvOutputFilePath = dir + "/_" + subjectName + "_" + str(imageInterval) + "s_" + dir[dir.rfind("/")+1:] + "_" + dayHourStr + ".csv"
        initialTime = time()

        self.imageWindow.handleNextImage()
        self.threadedTasks.startEEGLoggingToFile(csvOutputFilePath, initialTime)
