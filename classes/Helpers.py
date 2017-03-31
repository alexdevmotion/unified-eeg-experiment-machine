from Tkinter import *
from PIL import ImageTk, Image
import tkMessageBox
import sys
import os


def getNoImagesInDirectory(dir):
    return len(getImagesInDirectory(dir))


def getImagesInDirectory(dir):
    files = os.listdir(dir)
    images = []
    for file in files:
        if file.lower().endswith((".jpg", ".png", ".jpeg", ".gif")):
            images.append(file)
    return images


def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class FullScreenWindow:

    def __init__(self, closingCallback):
        self.closingCallback = closingCallback

        self.tk = Tk()
        self.frame = Frame(self.tk)
        self.frame.pack()
        self.state = False
        self.tk.iconbitmap("misc/favicon.ico")
        self.tk.title("EEG Unified Logger a.k.a. The Experiment Machine")
        self.tk.minsize(width=600, height=400)

        self.tk.bind("<F11>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)

        self.tk.protocol("WM_DELETE_WINDOW", self.on_closing)

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


class ImageWindow:

    def __init__(self, tk, dir, images, imageInterval, threadedTasks):
        self.tk = tk
        self.dir = dir
        self.images = images
        self.imageInterval = imageInterval
        self.threadedTasks = threadedTasks

        self.curImageIndex = 0

        self.window = Toplevel(self.tk)
        self.window.attributes("-fullscreen", True)
        self.window.focus_force()
        self.window.bind("<Escape>", self.experimentStoppedByUser)
        self.windowDestroyed = False

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.screenSize = screen_width, screen_height

        self.imagePanel = Label(self.window, image=None)
        self.imagePanel.pack(side="bottom", fill="both", expand="yes")

    def experimentStoppedByUser(self, event=None):
        self.window.destroy()
        self.windowDestroyed = True
        self.threadedTasks.stopLoggingToFile()

    def handleNextImage(self):
        if not self.windowDestroyed:
            try:
                curImage = str(self.images[self.curImageIndex])
                self.threadedTasks.setCurrentFileName(curImage)
                self.displayImage(self.dir + "/" + curImage)
                self.curImageIndex += 1
                self.window.after(self.imageInterval * 1000, self.handleNextImage)
            except IndexError:
                self.experimentStoppedByUser()


    def displayImage(self, path):
        img = Image.open(path)
        img.thumbnail(self.screenSize, Image.ANTIALIAS)

        photoimg = ImageTk.PhotoImage(img)

        self.imagePanel.configure(image=photoimg)
        self.imagePanel.image = photoimg
