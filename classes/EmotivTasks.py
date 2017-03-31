from classes import EmotivHeadset
from threading import Thread


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


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

    @threaded
    def startEEGLoggingToFile(self, filePath, initialTime):
        self.emotiv.startEEGLoggingToFile(filePath, initialTime)

    def stopLoggingToFile(self):
        self.emotiv.stopLoggingToFile()

    def setCurrentFileName(self, fileName):
        self.emotiv.setCurrentFileName(fileName)
