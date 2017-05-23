from classes import EmotivTasks
from classes import OpenBciTasks
from classes import Helpers
from classes import Gui
from Tkinter import *

isEmotiv = False
isOpenbci = False
emotivHeadsetTasks = ''
openbciTasks = ''

def onWindowClose():
    if isEmotiv:
        emotivHeadsetTasks.emotiv.engineDisconnect()
    if isOpenbci:
        openbciTasks.openbci.stop()

def startEmotiv():
    isEmotiv = True
    emotivHeadsetTasks = EmotivTasks.EmotivHeadsetThreadedTasks()
    gui = Gui.GUI(w.tk, emotivHeadsetTasks, isEmotiv)

def startOpenbci():
    isOpenbci = True
    openbciTasks = OpenBciTasks.OpenBciThreadedTasks()
    gui = Gui.GUI(w.tk, openbciTasks, isEmotiv)

w = Helpers.FullScreenWindow(onWindowClose)

chooseHeadsetFrame = Frame()
chooseHeadsetLabel = Label(chooseHeadsetFrame, text="Choose headset:")
chooseHeadsetLabel.pack(side=LEFT)
chosenHeadsetVar = IntVar()
Radiobutton(chooseHeadsetFrame, text="Emotiv Insight", variable=chosenHeadsetVar, value=1, indicatoron=0, command=startEmotiv).pack(anchor=W)
Radiobutton(chooseHeadsetFrame, text="OpenBCI Mark 4", variable=chosenHeadsetVar, value=2, indicatoron=0, command=startOpenbci).pack(anchor=W)
chooseHeadsetFrame.pack(anchor=W)

w.tk.mainloop()