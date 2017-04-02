import sys
import os
import platform
import ctypes
from ctypes import *
from time import sleep
from time import time
from array import *
if sys.platform.startswith('win32'):
    import msvcrt
elif sys.platform.startswith('linux'):
    import atexit
    from select import select
import struct
import csv

if struct.calcsize("P") * 8 == 32:
    EDK_PATH_WIN = "bin/win32/edk.dll"
else:
    EDK_PATH_WIN = "bin/win64/edk.dll"
LIBEDK_PATH_ARMHF = "bin/armhf/libedk.so"
LIBEDK_PATH_LIN64 = "bin/linux64/libedk.so"


class EmotivHeadsetInformation:
    def __init__(self):
        try:
            if sys.platform.startswith('win32'):
                self.libEDK = cdll.LoadLibrary(EDK_PATH_WIN)
            elif sys.platform.startswith('linux'):
                srcDir = os.getcwd()
                if platform.machine().startswith('arm'):
                    libPath = srcDir + LIBEDK_PATH_ARMHF
                else:
                    libPath = srcDir + LIBEDK_PATH_LIN64
                self.libEDK = CDLL(libPath)
            else:
                raise Exception('System not supported.')
        except Exception as e:
            print 'Error: cannot load EDK lib:', e
            exit()

        IEE_EmoEngineEventCreate = self.libEDK.IEE_EmoEngineEventCreate
        IEE_EmoEngineEventCreate.restype = c_void_p
        self.eEvent = IEE_EmoEngineEventCreate()
        
        IS_GetTimeFromStart = self.libEDK.IS_GetTimeFromStart
        IS_GetTimeFromStart.argtypes = [ctypes.c_void_p]
        IS_GetTimeFromStart.restype = c_float

        IS_GetWirelessSignalStatus = self.libEDK.IS_GetWirelessSignalStatus
        IS_GetWirelessSignalStatus.restype = c_int
        IS_GetWirelessSignalStatus.argtypes = [c_void_p]

        IS_GetContactQuality = self.libEDK.IS_GetContactQuality
        IS_GetContactQuality.restype = c_int
        IS_GetContactQuality.argtypes = [c_void_p, c_int]

        IEE_EmoEngineEventGetEmoState = self.libEDK.IEE_EmoEngineEventGetEmoState
        IEE_EmoEngineEventGetEmoState.argtypes = [c_void_p, c_void_p]
        IEE_EmoEngineEventGetEmoState.restype = c_int
        
        IEE_EmoStateCreate = self.libEDK.IEE_EmoStateCreate
        IEE_EmoStateCreate.restype = c_void_p
        self.eState = IEE_EmoStateCreate()

        self.ready = 0

    def engineConnect(self):
        if self.libEDK.IEE_EngineConnect("Emotiv Systems-5") != 0:
            print "Emotiv Engine start up failed."
            return False
        return True

    def engineDisconnect(self):
        self.libEDK.IEE_EngineDisconnect()
        self.libEDK.IEE_EmoStateFree(self.eState)
        self.libEDK.IEE_EmoEngineEventFree(self.eEvent)

    def checkDonglePresent(self):
        userID = c_uint(0)
        user = pointer(userID)
        for i in range(0, 4):
            state = self.libEDK.IEE_EngineGetNextEvent(self.eEvent)
            if state == 0:
                eventType = self.libEDK.IEE_EmoEngineEventGetType(self.eEvent)
                self.libEDK.IEE_EmoEngineEventGetUserId(self.eEvent, user)
                if eventType == 16:
                    self.ready = 1
                    self.libEDK.IEE_FFTSetWindowingType(userID, 1)
                return True
            sleep(0.1)
        return False

    def getWirelessSignalStrength(self):
        wirelessStrength = -1
        userID = c_uint(0)
        user = pointer(userID)
        for i in range(0, 10):

            self.libEDK.IEE_EngineGetNextEvent(self.eEvent)

            eventType = self.libEDK.IEE_EmoEngineEventGetType(self.eEvent)
            self.libEDK.IEE_EmoEngineEventGetUserId(self.eEvent, user)

            if eventType == 16:
                self.ready = 1
                self.libEDK.IEE_FFTSetWindowingType(userID, 1)
            if eventType == 64:
                self.libEDK.IEE_EmoEngineEventGetEmoState(self.eEvent, self.eState)
                wirelessStrength = self.libEDK.IS_GetWirelessSignalStatus(self.eState)

            sleep(0.1)
        return wirelessStrength

    def getWirelessStrengthBatteryLevelContactQuality(self):
        userID = c_uint(0)
        user = pointer(userID)
        batteryLevel     = c_long(0)
        batteryLevelP    = pointer(batteryLevel)
        maxBatteryLevel  = c_int(0)
        maxBatteryLevelP = pointer(maxBatteryLevel)
        for i in range(0, 10):

            self.libEDK.IEE_EngineGetNextEvent(self.eEvent)

            eventType = self.libEDK.IEE_EmoEngineEventGetType(self.eEvent)
            self.libEDK.IEE_EmoEngineEventGetUserId(self.eEvent, user)

            if eventType == 16:
                self.ready = 1
                self.libEDK.IEE_FFTSetWindowingType(userID, 1)
            if eventType == 64:
                self.libEDK.IEE_EmoEngineEventGetEmoState(self.eEvent, self.eState)
                wirelessStrength = self.libEDK.IS_GetWirelessSignalStatus(self.eState)

                if wirelessStrength == 0:
                    return [0] * 7

                self.libEDK.IS_GetBatteryChargeLevel(self.eState, batteryLevelP, maxBatteryLevelP)

                return [
                    wirelessStrength,
                    batteryLevel.value,
                    self.libEDK.IS_GetContactQuality(self.eState, 3),
                    self.libEDK.IS_GetContactQuality(self.eState, 7),
                    self.libEDK.IS_GetContactQuality(self.eState, 9),
                    self.libEDK.IS_GetContactQuality(self.eState, 12),
                    self.libEDK.IS_GetContactQuality(self.eState, 16),
                ]
            sleep(0.1)

        return [-1] * 7

    def startEEGLoggingToFile(self, filePath, initialTime):
        self.keepLogging = True
        userID = c_uint(0)
        user = pointer(userID)
        state = c_int(0)

        alphaValue = c_double(0)
        low_betaValue = c_double(0)
        high_betaValue = c_double(0)
        gammaValue = c_double(0)
        thetaValue = c_double(0)

        alpha = pointer(alphaValue)
        low_beta = pointer(low_betaValue)
        high_beta = pointer(high_betaValue)
        gamma = pointer(gammaValue)
        theta = pointer(thetaValue)

        channelList = array('I', [3, 7, 9, 12, 16])  # IED_AF3, IED_AF4, IED_T7, IED_T8, IED_Pz

        channels = ["AF3", "AF4", "T7", "T8", "Pz"]
        bands = ["Theta", "Alpha", "LBeta", "HBeta", "Gamma"]
        header = ["Timestamp", "Filename"]
        for channel in channels:
            for band in bands:
                header.append(channel + " " + band)

        csvfile = open(filePath, "wb")
        csvwriter = csv.writer(csvfile, delimiter=",")
        csvwriter.writerow(header)

        previousFirstSensorValues = [0, 0, 0, 0, 0]

        while self.keepLogging:
            state = self.libEDK.IEE_EngineGetNextEvent(self.eEvent)

            if state == 0:
                eventType = self.libEDK.IEE_EmoEngineEventGetType(self.eEvent)
                self.libEDK.IEE_EmoEngineEventGetUserId(self.eEvent, user)
                if eventType == 16:
                    self.ready = 1
                    self.libEDK.IEE_FFTSetWindowingType(userID, 1)

                if self.ready == 1:
                    row = [(time() - initialTime), self.currentFileName]
                    writerow = True
                    for i in channelList:
                        self.libEDK.IEE_GetAverageBandPowers(userID, i, theta, alpha, low_beta, high_beta, gamma)
                        values = [thetaValue.value, alphaValue.value, low_betaValue.value, high_betaValue.value, gammaValue.value]
                        if i == 3:
                            if values == previousFirstSensorValues:  # prevent duplicate consecutive values
                                writerow = False
                                break
                            previousFirstSensorValues = values
                        row.extend(values)
                    if writerow:
                        csvwriter.writerow(row)
            sleep(0.1)

    def stopLoggingToFile(self):
        self.keepLogging = False

    def setCurrentFileName(self, fileName):
        self.currentFileName = fileName

    def startStateLogging(self):
        userID       = c_uint(0)
        user         = pointer(userID)
        ready        = 0
        state        = c_int(0)
        systemUpTime = c_float(0.0)
        
        batteryLevel     = c_long(0)
        batteryLevelP    = pointer(batteryLevel)
        maxBatteryLevel  = c_int(0)
        maxBatteryLevelP = pointer(maxBatteryLevel)
        
        systemUpTime     = c_float(0.0)
        wirelessStrength = c_int(0)
        
        # -------------------------------------------------------------------------
        print "==================================================================="
        print "This example allows getting headset info: contactquality, wireless strength, battery level."
        print "==================================================================="
        print "Time, Wireless Strength, Battery Level, AF3, T7, Pz, T8, AF4"

        while True:

            state = self.libEDK.IEE_EngineGetNextEvent(self.eEvent)

            if state == 0:
                eventType = self.libEDK.IEE_EmoEngineEventGetType(self.eEvent)
                self.libEDK.IEE_EmoEngineEventGetUserId(self.eEvent, user)
                
                if eventType == 16:  # self.libEDK.IEE_Event_enum.IEE_UserAdded
                    print "User added"
                    ready = 1
                    
                if eventType == 64:  # self.libEDK.IEE_Event_enum.IEE_EmoStateUpdated
                                
                    self.libEDK.IEE_EmoEngineEventGetEmoState(self.eEvent, self.eState);
                    
                    systemUpTime = self.libEDK.IS_GetTimeFromStart(self.eState);
                    wirelessStrength = self.libEDK.IS_GetWirelessSignalStatus(self.eState);
                    
                    if wirelessStrength > 0:
                        print (systemUpTime)
                                        
                        self.libEDK.IS_GetBatteryChargeLevel(self.eState, batteryLevelP, maxBatteryLevelP);
                        
                        print systemUpTime, ",",
                        print wirelessStrength, ",",
                        print batteryLevel.value, ",",
                        print self.libEDK.IS_GetContactQuality(self.eState, 3), ",",
                        print self.libEDK.IS_GetContactQuality(self.eState, 7), ",",
                        print self.libEDK.IS_GetContactQuality(self.eState, 9), ",",
                        print self.libEDK.IS_GetContactQuality(self.eState, 12), ",",
                        print self.libEDK.IS_GetContactQuality(self.eState, 16), ",",
                        print '\n'
                                     
            elif state != 0x0600:
                print "Internal error in Emotiv Engine ! "
        # -------------------------------------------------------------------------
        self.libEDK.IEE_EngineDisconnect()
        self.libEDK.IEE_EmoStateFree(self.eState)
        self.libEDK.IEE_EmoEngineEventFree(self.eEvent)

    def startEEGLogging(self):
        userID = c_uint(0)
        user = pointer(userID)
        ready = 0
        state = c_int(0)
        
        alphaValue = c_double(0)
        low_betaValue = c_double(0)
        high_betaValue = c_double(0)
        gammaValue = c_double(0)
        thetaValue = c_double(0)
        
        alpha = pointer(alphaValue)
        low_beta = pointer(low_betaValue)
        high_beta = pointer(high_betaValue)
        gamma = pointer(gammaValue)
        theta = pointer(thetaValue)
        
        channelList = array('I', [3, 7, 9, 12, 16])  # IED_AF3, IED_AF4, IED_T7, IED_T8, IED_Pz
        
        # -------------------------------------------------------------------------
        print "==================================================================="
        print "Example to get the average band power for a specific channel from the latest epoch."
        print "==================================================================="
        print "Theta, Alpha, Low_beta, High_beta, Gamma \n"
        
        while True:
            state = self.libEDK.IEE_EngineGetNextEvent(self.eEvent)
        
            if state == 0:
                eventType = self.libEDK.IEE_EmoEngineEventGetType(self.eEvent)
                self.libEDK.IEE_EmoEngineEventGetUserId(self.eEvent, user)
                if eventType == 16:  # self.libEDK.IEE_Event_enum.IEE_UserAdded
                    ready = 1
                    self.libEDK.IEE_FFTSetWindowingType(userID, 1)  # 1: self.libEDK.IEE_WindowingTypes_enum.IEE_HAMMING
                    print "User added"
        
                if ready == 1:
                    for i in channelList:
                        result = c_int(0)
                        result = self.libEDK.IEE_GetAverageBandPowers(userID, i, theta, alpha, low_beta, high_beta, gamma)
        
                        if result == 0:  # EDK_OK
                            print "%.6f, %.6f, %.6f, %.6f, %.6f \n" % (thetaValue.value, alphaValue.value, low_betaValue.value, high_betaValue.value, gammaValue.value)
        
            elif state != 0x0600:
                print "Internal error in Emotiv Engine!"
            sleep(0.1)
        # -------------------------------------------------------------------------
        self.libEDK.IEE_EngineDisconnect()
        self.libEDK.IEE_EmoStateFree(self.eState)
        self.libEDK.IEE_EmoEnginself.eEventFree(self.eEvent)
