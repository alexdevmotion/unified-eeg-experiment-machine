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

        self.startThreads()

        self.donglePresentLabel = StringVar()
        Label(self.tk, textvariable=self.donglePresentLabel).pack()

        w.tk.mainloop()

    def startThreads(self):
        self.tk.after(100, self.updateDongleThread)

    def updateDongleThread(self):
        resultQueue = Queue.Queue()
        self.threadedTasks.checkDonglePresent(resultQueue).join()
        self.updateDonglePresent("No" if resultQueue.get() == 0 else "Yes")
        self.tk.after(100, self.updateDongleThread)

    def updateDonglePresent(self, status):
        self.donglePresentLabel.set(status)


emotivHeadsetTasks = EmotivHeadsetThreadedTasks()

w = FullScreenWindow(emotivHeadsetTasks)
w.tk.title("EEG Unified Logger a.k.a. The Experiment Machine")
# w.toggle_fullscreen()
gui = GUI(w.tk, emotivHeadsetTasks)
