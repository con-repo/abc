#!/usr/bin/python

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import httplib
import urllib2
import urllib

GOOGLEID="UA-60343498-1"

# Get Location of Current IP address
def getIP2Location():
    ip2location = ""
    req = urllib2.Request(url='http://dialerxn.purevpn.net/dialer/select-location/Dialer_XMLS/ip_location.php')
    f = urllib2.urlopen(req)
    ip2xml = f.read()

    for item in ip2xml.split("</iso>"):
        if "<iso>" in item:
            ip2location = item [ item.find("<iso>")+len("<iso>") : ]

    return ip2location

# Send Event to Google Analytics
def sendGoogleAnalyticsEventNow(userName, title, action, label):
    params = urllib.urlencode({
            'v': 1,
            'tid': GOOGLEID,
            'cid': userName,
            't': 'event',
            'ec': title,
            'ea': action,
            'el': label
            })

    connection = httplib.HTTPSConnection('www.google-analytics.com')
    connection.request('POST', '/collect', params)

def sendGoogleAnalyticsPageViewToGoogle(userName, pageViewed, title):
    params = urllib.urlencode({
            'v': 1,
            'tid': GOOGLEID,
            'cid': userName,
            't': 'pageview',
            'dp': pageViewed,
            'dt': title
            })

    connection = httplib.HTTPSConnection('www.google-analytics.com')
    connection.request('POST', '/collect', params)


# Send Connected Event Login
def sendGoogleAnalytics(userName, countryCode):
    sendGoogleAnalyticsEventNow(userName, 'LOGIN FROM KODI', 'KODI VPN service started', countryCode)


#Send Connected Event Connected Country
def sendGoogleAnalyticsConnectedCountry(userName):
    countryCode = getIP2Location()
    sendGoogleAnalyticsEventNow(userName, 'KODI Connected Country', 'KODI VPN service connected country', countryCode)


# Send Page View
def sendGoogleAnalyticsPageView(pageView, addon):
    userName = addon.getSetting("vpn_username")
    sendGoogleAnalyticsPageViewToGoogle(userName, pageView, 'KODI VPN service')

