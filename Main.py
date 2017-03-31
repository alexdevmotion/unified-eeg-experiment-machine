from Tkinter import *
from classes import EmotivHeadset
from threading import Thread
from PIL import ImageTk, Image
import tkMessageBox
import sys
import Queue
import tkFileDialog
import os


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


class FullScreenWindow:

    def __init__(self, closingCallback):
        self.closingCallback = closingCallback

        self.tk = Tk()
        self.frame = Frame(self.tk)
        self.frame.pack()
        self.state = False
        self.tk.bind("<F11>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        self.tk.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.tk.iconbitmap("misc/favicon.ico")
        self.tk.minsize(width=600, height=400)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

    def on_closing(self):
        if tkMessageBox.askokcancel("Quit", "Are you sure you want to exit?"):
            self.tk.destroy()
            if self.closingCallback:
                self.closingCallback()
            sys.exit(0)


class EmotivHeadsetThreadedTasks:
    def __init__(self):
        self.emotiv = EmotivHeadset.EmotivHeadsetInformation()
        self.emotiv.engineConnect()

    @threaded
    def checkDonglePresent(self, result):
        result.put(self.emotiv.checkDonglePresent())

    @threaded
    def getWirelessStrengthBatteryLevelContactQuality(self, result):
        result.put(self.emotiv.getWirelessStrengthBatteryLevelContactQuality())


class GUI:
    def __init__(self, tk, threadedTasks):

        self.tk = tk
        self.threadedTasks = threadedTasks
        self.keepCheckingWirelessStrength = False
        self.goFrameBuilt = False
        self.imageWindowDestroyed = True
        self.lastWirelessCheck = 0

        Label(self.tk, text="Supported headsets: Emotiv Insight").pack(anchor=W)

        donglePresentFrame = Frame()
        donglePresentLabel = Label(donglePresentFrame, text="Dongle present: ")
        donglePresentLabel.pack(side=LEFT)
        self.donglePresentCanvas = Canvas(donglePresentFrame, width=60, height=30)
        self.donglePresentCanvas.pack(side=RIGHT)
        self.donglePresentRectangle = self.donglePresentCanvas.create_rectangle(0, 0, 100, 50, fill="red")
        donglePresentFrame.pack(anchor=W)

        wirelessStrengthFrame = Frame()

        wirelessStrengthLabel = Label(wirelessStrengthFrame, text="Wireless strength: ")
        wirelessStrengthLabel.pack(side=LEFT)
        self.wirelessStrengthCanvas = Canvas(wirelessStrengthFrame, width=40, height=20)
        self.wirelessStrengthCanvas.pack(side=LEFT)
        self.wirelessStrengthRectangle = self.wirelessStrengthCanvas.create_rectangle(0, 0, 100, 50, fill="red")

        batteryLevelLabel = Label(wirelessStrengthFrame, text="Battery level: ")
        batteryLevelLabel.pack(side=LEFT)
        self.batteryLevelVar = StringVar(self.tk)
        batteryLevel = Label(wirelessStrengthFrame, textvariable=self.batteryLevelVar)
        batteryLevel.pack(side=LEFT)

        wirelessStrengthFrame.pack(anchor=W)

        self.tk.after(100, self.updateDongleThread)

        w.tk.mainloop()

    def updateDongleThread(self):
        resultQueue = Queue.Queue()
        self.threadedTasks.checkDonglePresent(resultQueue).join()
        result = resultQueue.get()
        self.donglePresentCanvas.itemconfig(self.donglePresentRectangle, fill="red" if result == 0 else "green")
        if result:
            self.keepCheckingWirelessStrength = True
            self.buildBrowseButtonFrame()
            self.buildFolderInfoFrame()
            self.buildImageIntervalFrame()
            self.buildSubjectNameFrame()
            self.tk.after(100, self.updateWirelessThread)
    
    def updateWirelessThread(self):
        resultQueue = Queue.Queue()
        self.threadedTasks.getWirelessStrengthBatteryLevelContactQuality(resultQueue).join()
        result = resultQueue.get()
        wirelessStrength = result[0]
        batteryLevel = result[1]
        self.batteryLevelVar.set(batteryLevel)
        self.lastWirelessCheck = wirelessStrength
        if wirelessStrength == 0:
            fill = "red"
        elif wirelessStrength == 1:
            fill = "yellow"
        elif wirelessStrength == 2:
            fill = "green"
        else:
            fill = "red"
        self.wirelessStrengthCanvas.itemconfig(self.wirelessStrengthRectangle, fill=fill)
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
        folderInfoLabel = Label(folderInfoFrame, text="Number of files in folder: ")
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
        imageIntervalEntry.insert(0, "1")
        self.imageIntervalVar.trace('w', self.onChange)

    def buildSubjectNameFrame(self):
        subjectNameFrame = Frame()
        subjectNameLabel = Label(subjectNameFrame, text="Subject name: ")
        subjectNameLabel.pack(side=LEFT)
        self.subjectNameVar = StringVar(self.tk)
        subjectNameEntry = Entry(subjectNameFrame, textvariable=self.subjectNameVar)
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
        return self.lastWirelessCheck > 0

    def isImageDirectoryValid(self):
        noFiles = self.folderInfoNoFilesVar.get()
        return noFiles and int(noFiles) > 0

    def isImageIntervalValid(self):
        imageInterval = self.imageIntervalVar.get()
        return self.representsInt(imageInterval) and int(imageInterval) > 0

    def isSubjectNameValid(self):
        subjectName = self.subjectNameVar.get()
        return len(subjectName) > 0

    def showHideGoFrame(self):
        if self.isWirelessStrengthValid() and self.isImageDirectoryValid() and self.isImageIntervalValid() and self.isSubjectNameValid():
            if not self.goFrameBuilt:
                self.buildGoFrame()
        else:
            self.destroyGoFrame()

    def onChange(self, a, b, c):
        self.showHideGoFrame()

    def onBrowseDirectory(self):
        dir = tkFileDialog.askdirectory()
        self.browseDirectoryVar.set(dir)
        noFiles = self.getNoFilesInDirectory(dir)
        self.folderInfoNoFilesVar.set(noFiles)
        self.showHideGoFrame()

    def getNoFilesInDirectory(self, dir):
        return len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])

    def representsInt(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def experimentStoppedByUser(self, event=None):
        self.imageWindow.destroy()
        self.imageWindowDestroyed = True

    def go(self):
        self.dir = self.browseDirectoryVar.get()
        self.images = os.listdir(self.dir)
        self.curImageIndex = 0
        self.imageInterval = int(self.imageIntervalVar.get())

        self.imageWindow = Toplevel(self.tk)
        self.imageWindow.attributes("-fullscreen", True)
        self.imageWindow.focus_force()
        self.imageWindow.bind("<Escape>", self.experimentStoppedByUser)
        self.imageWindowDestroyed = False

        screen_width = self.imageWindow.winfo_screenwidth()
        screen_height = self.imageWindow.winfo_screenheight()
        self.screenSize = screen_width, screen_height

        self.imagePanel = Label(self.imageWindow, image=None)
        self.imagePanel.pack(side="bottom", fill="both", expand="yes")

        self.handleNextImage()
        self.imageWindow.mainloop()

    def handleNextImage(self):
        if not self.imageWindowDestroyed:
            self.displayImage(self.dir + "/" + str(self.images[self.curImageIndex]))
            self.curImageIndex = self.curImageIndex + 1
            self.imageWindow.after(self.imageInterval * 1000, self.handleNextImage)

    def displayImage(self, path):
        print path
        img = Image.open(path)
        img.thumbnail(self.screenSize, Image.ANTIALIAS)

        photoimg = ImageTk.PhotoImage(img)

        self.imagePanel.configure(image=photoimg)
        self.imagePanel.image = photoimg



emotivHeadsetTasks = EmotivHeadsetThreadedTasks()


def onMainWindowClose():
    emotivHeadsetTasks.emotiv.engineDisconnect()

w = FullScreenWindow(onMainWindowClose)
w.tk.title("EEG Unified Logger a.k.a. The Experiment Machine")
# w.toggle_fullscreen()
gui = GUI(w.tk, emotivHeadsetTasks)
