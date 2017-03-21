import sys
import os
import platform
import ctypes
from ctypes import *
if sys.platform.startswith('win32'):
    import msvcrt
elif sys.platform.startswith('linux'):
    import atexit
    from select import select

EDK_PATH_WIN32 = "bin/win32/edk.dll"
LIBEDK_PATH_ARMHF = "bin/armhf/libedk.so"
LIBEDK_PATH_LIN64 = "bin/linux64/libedk.so"


class EmotivHeadsetInformation:

    def __init__(self):
        try:
            if sys.platform.startswith('win32'):
                self.libEDK = cdll.LoadLibrary(EDK_PATH_WIN32)
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


    def kbhit(self):
        # Returns True if keyboard character was hit, False otherwise.
        if sys.platform.startswith('win32'):
            return msvcrt.kbhit()   
        else:
            dr, dw, de = select([sys.stdin], [], [], 0)
            return dr != []
    
    def startLogging(self):
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
        
        header = "Time, Wireless Strength, Battery Level, AF3, T7, Pz, T8, AF4"
        # -------------------------------------------------------------------------
        
        print "==================================================================="
        print "This example allows getting headset infor: contactquality, wireless strength, battery level."
        print "==================================================================="
        
        # -------------------------------------------------------------------------
        
        if self.libEDK.IEE_EngineConnect("Emotiv Systems-5") != 0:
            print "Emotiv Engine start up failed."
        
        print "Press any key to stop logging...\n"
        
        print header, "\n",
        
        while True:    
            
            if self.kbhit():
                break
            
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