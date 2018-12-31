import urllib2, urllib, json, time, sys
from cookielib import CookieJar

dbgFile = open("/LOGIN", "w")
printOk = True
if len(sys.argv) > 1: printOk = False

def record(stri):
    if printOk: print("<RPiLogin>" +  stri)
    dbgFile.write(stri + "\n")
    dbgFile.flush()

loginPostUrl = "https://wifilogin.xfinity.com/user_login.php"
loginForm = \
"""
method=authenticate
&username=jeffnkarajacobs%%40yahoo.com
&password=Luke5wim5fa5t
&client_mac=%s
&get_url=%s
&agree_standard=
&friendlyname=LJ
&hash=%s
&devicetype=Windows+10+Chrome+-+Windows
&javascript=true
""".replace("\n", "")

#need to get hash and geturl (path and h) and cookies
loginPageUrl = "https://wifilogin.xfinity.com/start.php"
hashStartStr = "<input type=\"hidden\" name=\"hash\" value=\""

def getBetween(startStr, endStr, haystackStr):
    startLoc = haystackStr.find(startStr) + len(startStr)
    endLoc = haystackStr[startLoc:].find(endStr) + startLoc
    return haystackStr[startLoc:endLoc]

def getRedirectPage(opener):
    try:
        page = opener.open("http://google.com")
    except urllib2.URLError:
        record("URLError visiting google.com")
        return -1
    if page.geturl() == 'http://www.google.com/':
        return 1 #no redirect
    else:
        return page

def login(startPage, opener, mac):
    """
    Get info needed to login to user_login and then login
    :param startPage:
    :return:
    """
    url = startPage.geturl()
    pathIndex = url.find("/start.php?")
    if pathIndex == -1:
        return False
    get_url = url[pathIndex:]
    record("get_url = %s" % get_url)
    get_url = urllib.quote_plus(get_url)

    data = startPage.read()
    hashIndex = data.find(hashStartStr)
    if hashIndex == -1:
        return False
    hashValue = getBetween(hashStartStr, "\"", data)
    record("hash = %s" % hashValue)
    hashValue = urllib.quote_plus(hashValue)

    mac = urllib.quote_plus(mac)

    loginFormFilled = loginForm % (mac, get_url, hashValue)
    record("loginForm = %s" % loginFormFilled)

    resp = opener.open(loginPostUrl, data=loginFormFilled)
    resp = json.loads(resp.read())
    if resp['response'] == 'Success':
        return True
    else:
        return False


def loginIfNeeded():
    cj = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    pg = getRedirectPage(opener)
    if pg == 1:
        #record("Connected!")
        return True
    elif pg == -1:
        #record("Error!")
        return False
    else:
        #record("Redirected to: %s" % pg.geturl())
        return login(pg, opener, "02:9D:E0:90:55:17")

while True:
    result = loginIfNeeded()
    if result:
        record("[+] Successfully connected to router!")
        time.sleep(30)
    else:
        record("[-] Failed to connect!")
        time.sleep(10)
