from Tkinter import *
from classes import EmotivHeadset
from threading import Thread
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

    def __init__(self, emotivHeadsetTasks):
        self.emotivHeadsetTasks = emotivHeadsetTasks
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
            self.emotivHeadsetTasks.emotiv.engineDisconnect()
            sys.exit(0)


class EmotivHeadsetThreadedTasks:
    def __init__(self):
        self.emotiv = EmotivHeadset.EmotivHeadsetInformation()
        self.emotiv.engineConnect()

    @threaded
    def checkDonglePresent(self, result):
        result.put(self.emotiv.checkDonglePresent())

    @threaded
    def checkHeadsetPresent(self, result):
        result.put(self.emotiv.checkHeadsetPresent())

    @threaded
    def getWirelessSignalStrength(self, result):
        result.put(self.emotiv.getWirelessSignalStrength())


class GUI:
    def __init__(self, tk, threadedTasks):

        self.tk = tk
        self.threadedTasks = threadedTasks
        self.keepCheckingWirelessStrength = False
        self.goFrameBuilt = False

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
        self.wirelessStrengthCanvas = Canvas(wirelessStrengthFrame, width=60, height=30)
        self.wirelessStrengthCanvas.pack(side=LEFT)
        self.wirelessStrengthRectangle = self.wirelessStrengthCanvas.create_rectangle(0, 0, 100, 50, fill="red")
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
        self.threadedTasks.getWirelessSignalStrength(resultQueue).join()
        result = resultQueue.get()
        if result == 0:
            fill = "red"
        elif result == 1:
            fill = "yellow"
        elif result == 2:
            fill = "green"
        else:
            fill = "red"
        self.wirelessStrengthCanvas.itemconfig(self.wirelessStrengthRectangle, fill=fill)
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

    def isImageDirectoryValid(self):
        noFiles = self.folderInfoNoFilesVar.get()
        return int(noFiles) > 0

    def isImageIntervalValid(self):
        imageInterval = self.imageIntervalVar.get()
        return self.representsInt(imageInterval) and int(imageInterval) > 0

    def isSubjectNameValid(self):
        subjectName = self.subjectNameVar.get()
        return len(subjectName) > 0

    def showHideGoFrame(self):
        if not self.goFrameBuilt and self.isImageDirectoryValid() and self.isImageIntervalValid() and self.isSubjectNameValid():
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

    def go(self):
        dir = self.browseDirectoryVar.get()
        images = os.listDir(dir)
        self.displayImage(images[0])

    def displayImage(self, path):
        print path

emotivHeadsetTasks = EmotivHeadsetThreadedTasks()

w = FullScreenWindow(emotivHeadsetTasks)
w.tk.title("EEG Unified Logger a.k.a. The Experiment Machine")
# w.toggle_fullscreen()
gui = GUI(w.tk, emotivHeadsetTasks)
