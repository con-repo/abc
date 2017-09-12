#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2016 Zomboided
#    modified Copyright (C) 2016 IvacyLtd
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#    Platform specific calls used by VPN Manager for OpenVPN add-on.

import os
import sys
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
from libs.utility import debugTrace, errorTrace, infoTrace, enum
from sys import platform


# **** ADD MORE PLATFORMS HERE ****
platforms = enum(UNKNOWN=0, WINDOWS=1, LINUX=2, RPI=3, ANDROID=4, MAC=5)  
platforms_str = ("Unknown", "Windows", "Linux, openvpn installed", "Linux, openvpn plugin", "Android", "Apple")

use_sudo = False


def fakeConnection():
    # Return True to fake out any calls to openVPN to change the network
    if getPlatform() == platforms.WINDOWS: return True
    return False

    
def getPlatform():
    # Work out which platform is being used.
    build = xbmc.getInfoLabel('System.BuildVersion')
    build_number = int(build[0:2])
    if sys.platform == "win32": return platforms.WINDOWS
    if sys.platform == "linux" or sys.platform == "linux2":
        if build_number == 15 and getAddonPath(True, "").startswith("/storage/.kodi/"):
            # For OE 6.0.0 (Kodi 15), openvpn is a separate install             
            return platforms.RPI
        else:
            # Other OE versions and other Linux installs use the openvpn installed in usr/sbin
            return platforms.LINUX
            
    # **** ADD MORE PLATFORMS HERE ****
    
    #if sys.platform == "?": return platforms.ANDROID
    #if sys.platform == "darwin": return platforms.MAC
    return platforms.UNKNOWN    
        

def getPlatformString():
    p = getPlatform()
    return platforms_str[p]


def getVPNLogFilePath():
    # Return the full filename for the VPN log file
    p = getPlatform()
    if p == platforms.LINUX or p == platforms.RPI:
        return "/run/openvpn.log"
        
    # **** ADD MORE PLATFORMS HERE ****
    
    return ""
    

def stopVPN():
    # Stop the platform VPN task.
    if not fakeConnection():
        p = getPlatform()
        if p == platforms.LINUX or p == platforms.RPI:
            command="killall -9 openvpn"            
            #if p == platforms.LINUX and use_sudo : command = "sudo " + command
            debugTrace("Stopping VPN with " + command)
            os.system(command)
            
        # **** ADD MORE PLATFORMS HERE ****
        
    return
        
    
def startVPN(vpn_profile):
    # Call the platform VPN to start the VPN
    if not fakeConnection():
        p = getPlatform()
        if p == platforms.RPI or p == platforms.LINUX:
            command=getOpenVPNPath() + " \"" + vpn_profile + "\" > " + getVPNLogFilePath() + " &"           
            debugTrace("Starting VPN with " + command)
            os.system(command)
            
        # **** ADD MORE PLATFORMS HERE ****
        
    else:
        # This bit is just to help with debug during development.
        command=getOpenVPNPath() + " \"" + vpn_profile + "\" > " + getVPNLogFilePath() + " &"
        debugTrace("Starting VPN with " + command)
    return


def getOpenVPNPath():
    # Call the platform VPN to start the VPN
    if fakeConnection():
        p = platforms.RPI
    else:
        p = getPlatform()
        
    if p == platforms.RPI:
        return getAddonPath(False, "service.purevpn.monitor/bin/openvpn")
    #    return getAddonPath(False, "network.openvpn/bin/openvpn")
    if p == platforms.LINUX:            
    #    return getAddonPath(False, "service.purevpn.monitor/bin/openvpn")
        return "/usr/sbin/openvpn"
    
    
    # **** ADD MORE PLATFORMS HERE ****
    
    return

    
def checkVPNInstall(addon):
    # Check that openvpn is available otherwise generate an error message    
    if not fakeConnection():
        p = getPlatform()
        dialog_msg = ""
        if p == platforms.RPI:
            #command_path = getAddonPath(False, "network.openvpn/bin/openvpn")
            command_path = getAddonPath(False, "service.purevpn.monitor/bin/openvpn")
            if xbmcvfs.exists(command_path):
                # Check the version that's installed
                #vpn_addon = xbmcaddon.Addon("network.openvpn")
                vpn_addon = xbmcaddon.Addon("service.purevpn.monitor")
                version =  vpn_addon.getAddonInfo("version")
                version = version.replace(".", "")
                if int(version) >= 125: return True
            dialog_msg = "OpenVPN executable not available. Update plugin to version 1.2.5 or greater."
        if p == platforms.LINUX:
            return True
        
        # **** ADD MORE PLATFORMS HERE ****

        # Display error message
        xbmcgui.Dialog().ok(addon.getAddonInfo("name"), dialog_msg)
        return False        
    else: return True
    
    return True

    
def checkVPNCommand(addon):
    # Issue the openvpn command and see if the output is a bunch of commands
    if not fakeConnection():
        p = getPlatform()
        if p == platforms.RPI or p == platforms.LINUX:
            # Issue the openvpn command, expecting to get the options screen back
            command = getOpenVPNPath() + " > " + getVPNLogFilePath() + " &"
            infoTrace("platform.py", "Testing openvpn with : " + command)
            os.system(command)
            xbmc.sleep(1000)
            i = 0
            # Waiting for the log file to appear
            while not xbmcvfs.exists(getVPNLogFilePath()) and i < 10:
                xbmc.sleep(1000)
                i = i + 1
            # If the log file appears, check it's what we expect
            if xbmcvfs.exists(getVPNLogFilePath()):
                log_file = open(getVPNLogFilePath(), 'r')
                log_file_lines = log_file.readlines()
                log_file.close()
                i = 0
                # Look for a phrase we'd expect to see if the call
                # worked and the list of options was displayed
                for line in log_file_lines:
                    if "General Options" in line:
                        return True
                    i = i + 1
                # Write the log file in case there's something in it
                errorTrace("platform.py", "Ran openvpn command and it failed")
                writeVPNLog()
                
        # **** ADD MORE PLATFORMS HERE ****
        
        # Display an error message
        dialog_msg = "The OpenVPN executable isn't working.  Check the log, then from a command line prompt type 'openvpn' and fix any problems reported\n"
        xbmcgui.Dialog().ok(addon.getAddonInfo("name"), dialog_msg)
        return False
        
    else: return True

    
def isVPNTaskRunning():
    # Return True if the VPN task is still running, or the VPN connection is still active
    # Return False if the VPN task is no longer running and the connection is not active
    
    if fakeConnection(): return True
    
    p = getPlatform()
    if p == platforms.LINUX or p == platforms.RPI:
        try:
            command = "pidof openvpn"
            #if p == platforms.LINUX and use_sudo: command = "sudo " + command
            pid = os.system(command)
            # This horrible call returns 0 if it finds a process, it's not returning the PID number
            if pid == 0 : return True
            return False
        except:
            return False
            
    # **** ADD MORE PLATFORMS HERE ****
    
    return False


connection_status = enum(UNKNOWN=0, CONNECTED=1, AUTH_FAILED=2, NETWORK_FAILED=3, TIMEOUT=4, ERROR=5) 
    
def getVPNConnectionStatus():
    # Open the openvpn output file and parse it for known phrases
    # Return 'connected', 'auth failed', 'network failed', 'error' or ''

    if fakeConnection(): return connection_status.UNKNOWN

    # **** ADD MORE PLATFORMS HERE ****
    # Might not need to mess with this too much if the log output from openvpn is the same
    
    p = getPlatform()
    if p == platforms.LINUX or p == platforms.RPI:
        path = getVPNLogFilePath()
        state = connection_status.UNKNOWN
        if xbmcvfs.exists(path):
            debugTrace("Reading log file")
            log = open(path,'r')
            lines = log.readlines()
            for line in lines:
                if "Initialization Sequence Completed" in line:
                    state = connection_status.CONNECTED
                    break
                if "AUTH_FAILED" in line:
                    state = connection_status.AUTH_FAILED
                if "TLS Error" in line:
                    state = connection_status.NETWORK_FAILED
                if "Connection timed out" in line:
                    state = connection_status.TIMEOUT
            log.close()
            # Haven't found what's expected so return an empty stream
            if not state == connection_status.UNKNOWN: debugTrace("VPN connection status is " + str(state))
            return state
        else:
            errorTrace("platform.py", "Tried to get VPN connection status but log file didn't exist")
            return connection_status.ERROR

            
def writeVPNLog():
    # Write the openvpn output log to the error file
    try:
        log_file = open(getVPNLogFilePath(), 'r')
        log_output = log_file.readlines()
        log_file.close()
        infoTrace("platform.py", "VPN log file start >>>")
        for line in log_output:
            print line
        infoTrace("platform.py", "<<< VPN log file end")
    except:
        errorTrace("platform.py", "Couldn't write VPN error log")
                
                
def useSudo(option):
    # True or False...
    use_sudo = option


def getSeparator():
    if getPlatform() == platforms.WINDOWS:
        return "\\"
    else:
        return "/"
        
    
def getAddonPath(this_addon, path):
    # Return the URL of the addon directory, plus any addition path/file name.
    if this_addon:
        return xbmc.translatePath("special://home/addons/service.purevpn.monitor/" + path)
    else:
        return xbmc.translatePath("special://home/addons/" + path)
        

def getUserDataPath(path):
    return xbmc.translatePath("special://userdata/addon_data/service.purevpn.monitor/" + path)
    
    
def getLogPath():    
    return xbmc.translatePath("special://logpath/kodi.log")
        
        
        
