from classes import OpenBciHeadset
from threading import Thread


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


class OpenBciThreadedTasks:
    def __init__(self):
        self.openbci = OpenBciHeadset.OpenBciHeadset()

    @threaded
    def checkDonglePresent(self, result):
        result.put(self.openbci.isDongleReady())

    @threaded
    def checkHeadsetPresent(self, result):
        result.put(self.openbci.checkHeadsetPresent())

    @threaded
    def waitStreamReady(self):
        self.openbci.waitStreamReady()

    @threaded
    def startEEGLoggingToFile(self, filePath, initialTime):
        self.openbci.startLoggingToFile(filePath, initialTime)

    @threaded
    def stopLoggingToFile(self):
        self.openbci.stopLoggingToFile()

    @threaded
    def kill(self):
        self.openbci.kill()

    def setCurrentFileName(self, fileName):
        self.openbci.setCurrentFileName(fileName)
