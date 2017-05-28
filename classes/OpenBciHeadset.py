import json
import time
import zmq
import subprocess
import csv

verbose = False
withSync = False

class OpenBciHeadset:
    def __init__(self):
        self.interface = Interface(verbose=verbose)
        self.startNode()
        self.keepLogging = True
        # if self.isDongleReady():
        #     print 'Node is ready'
        #     print 'Headset: ', self.checkHeadsetPresent()
        #     self.startLoggingToFile('caca.csv', time.time())
        # else:
        #     print 'Node is shit'

    def startNode(self):
        subprocess.Popen('start-node.bat', shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)

    def isDongleReady(self):
        while True:
            msg = self.interface.recv()
            try:
                dicty = json.loads(msg)
                command = dicty.get('command')
                message = dicty.get('message')

                if command == 'ready':
                    return message

            except BaseException as e:
                print e
        return False

    def waitStreamReady(self):
        while True:
            msg = self.interface.recv()
            try:
                dicty = json.loads(msg)
                command = dicty.get('command')

                if command == 'stream':
                    return True

            except BaseException as e:
                print e
        return False

    def checkHeadsetPresent(self):
        self.interface.send(json.dumps({
            'command': 'headset'
        }))
        while True:
            msg = self.interface.recv()
            try:
                dicty = json.loads(msg)
                command = dicty.get('command')
                message = dicty.get('message')

                if command == 'headset':
                    return message

            except BaseException as e:
                print e
        return False

    def stopLoggingToFile(self):
        self.keepLogging = False

    def stop(self):
        self.interface.send(json.dumps({
            'command': 'stop'
        }))

    def startLoggingToFile(self, filePath, initialTime):
        self.interface.send(json.dumps({
            'command': 'start'
        }))

        header = ["Full timestamp"] if withSync else []
        header = header + ["Timestamp", "Filename",
                           "1/Fp1", "2/Fp2", "3/Cz", "4/Pz", "5/P7", "6/P8", "7/O1", "8/O2",
                           "9/CP5", "10/CP6", "11/CP1", "12/CP2", "13/PO3", "14/PO4", "15/P3", "16/P4"]
        #default: "1/Fp1", "2/Fp2", "3/C3", "4/C4", "5/P7", "6/P8", "7/O1", "8/O2",
        #"9/F7", "10/F8", "11/F3", "12/F4", "13/T7", "14/T8", "15/P3", "16/P4"]


        csvfile = open(filePath, "wb")
        csvwriter = csv.writer(csvfile, delimiter=",")
        csvwriter.writerow(header)

        while 1:
            msg = self.interface.recv()
            if not self.keepLogging:
                continue
            try:
                dicty = json.loads(msg)
                command = dicty.get('command')
                message = dicty.get('message')

                if command == 'sample' and self.checkMessage(message):
                    row = [message.get('timeStamp')] if withSync else []
                    row = row + [(time.time() - initialTime), self.currentFileName] + message.get('channelData')
                    if verbose:
                        print "Writing row ", row
                    csvwriter.writerow(row)
            except BaseException as e:
                print e

    def setCurrentFileName(self, fileName):
        self.currentFileName = fileName

    def checkMessage(self, message):
        try:
            if type(message) is not dict:
                print "sample is not a dict", message
                return False
        except ValueError as e:
            print e
        return True


class Interface:
    def __init__(self, verbose=False):
        context = zmq.Context()
        self._socket = context.socket(zmq.PAIR)
        self._socket.connect("tcp://localhost:3004")

        self.verbose = verbose

        if self.verbose:
            print "Client Ready!"

        # Send a quick message to tell node process we are up and running
        self.send(json.dumps({
            'action': 'started',
            'command': 'status',
            'message': time.time() * 1000.0
        }))

    def send(self, msg):
        """
        Sends a message to TCP server
        :param msg: str
            A string to send to node TCP server, could be a JSON dumps...
        :return: None
        """
        if self.verbose:
            print '<- out ' + msg
        self._socket.send(msg)
        return

    def recv(self):
        """
        Checks the ZeroMQ for data
        :return: str
            String of data
        """
        return self._socket.recv()