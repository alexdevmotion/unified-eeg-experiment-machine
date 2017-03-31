from classes import EmotivTasks
from classes import Helpers
from classes import Gui

emotivHeadsetTasks = EmotivTasks.EmotivHeadsetThreadedTasks()

def onMainWindowClose():
    emotivHeadsetTasks.emotiv.engineDisconnect()

w = Helpers.FullScreenWindow(onMainWindowClose)

gui = Gui.GUI(w.tk, emotivHeadsetTasks)
