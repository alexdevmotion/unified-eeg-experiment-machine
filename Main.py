from Tkinter import *
from classes import HeadsetInformationLogger;

class FullScreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.frame = Frame(self.tk)
        self.frame.pack()
        self.state = False
        self.tk.bind("<F11>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

w = FullScreenWindow()

ehi = HeadsetInformationLogger.EmotivHeadsetInformation()
ehi.startLogging()

# Create a list
li = 'Carl Patrick Lindsay Helmut Chris Gwen'.split()
listb = Listbox(w.tk)           # Create a listbox widget
for item in li:                 # Insert each item within li into the listbox
    listb.insert(0, item)

listb.pack()                    # Pack listbox widget
w.tk.mainloop()
