from Tkinter import *
from classes import EmotivHeadset
from threading import Thread
import tkMessageBox
import sys
import Queue


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

        Label(self.tk, text="Supported headsets: Emotiv Insight").pack(anchor=W)

        donglePresentFrame = Frame()
        donglePresentLabel = Label(donglePresentFrame, text="Dongle present: ")
        donglePresentLabel.pack(side=LEFT)
        self.donglePresentCanvas = Canvas(donglePresentFrame, width=60, height=30)
        self.donglePresentCanvas.pack(side=RIGHT)
        self.donglePresentRectangle = self.donglePresentCanvas.create_rectangle(0, 0, 100, 50, fill="red")
        donglePresentFrame.pack(anchor=W)

        headsetPresentFrame = Frame()
        headsetPresentLabel = Label(headsetPresentFrame, text="Headset present: ")
        headsetPresentLabel.pack(side=LEFT)
        self.headsetPresentCanvas = Canvas(headsetPresentFrame, width=60, height=30)
        self.headsetPresentCanvas.pack(side=LEFT)
        self.headsetPresentRectangle = self.headsetPresentCanvas.create_rectangle(0, 0, 100, 50, fill="red")
        headsetPresentFrame.pack(anchor=W)

        wirelessStrengthFrame = Frame()
        wirelessStrengthLabel = Label(wirelessStrengthFrame, text="Wireless strength: ")
        wirelessStrengthLabel.pack(side=LEFT)
        self.wirelessStrengthCanvas = Canvas(wirelessStrengthFrame, width=60, height=30)
        self.wirelessStrengthCanvas.pack(side=LEFT)
        self.wirelessStrengthRectangle = self.wirelessStrengthCanvas.create_rectangle(0, 0, 100, 50, fill="red")
        wirelessStrengthFrame.pack(anchor=W)

        self.startThreads()

        w.tk.mainloop()

    def startThreads(self):
        self.tk.after(100, self.updateDongleThread)

    def updateDongleThread(self):
        resultQueue = Queue.Queue()
        self.threadedTasks.checkDonglePresent(resultQueue).join()
        result = resultQueue.get()
        self.donglePresentCanvas.itemconfig(self.donglePresentRectangle, fill="red" if result == 0 else "green")
        if result:
            self.tk.after(100, self.updateHeadsetThread)
    
    def updateHeadsetThread(self):
        resultQueue = Queue.Queue()
        self.threadedTasks.checkHeadsetPresent(resultQueue).join()
        result = resultQueue.get()
        self.headsetPresentCanvas.itemconfig(self.headsetPresentRectangle, fill="red" if result == 0 else "green")
        if result:
            self.keepCheckingWirelessStrength = True
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


emotivHeadsetTasks = EmotivHeadsetThreadedTasks()

w = FullScreenWindow(emotivHeadsetTasks)
w.tk.title("EEG Unified Logger a.k.a. The Experiment Machine")
# w.toggle_fullscreen()
gui = GUI(w.tk, emotivHeadsetTasks)
