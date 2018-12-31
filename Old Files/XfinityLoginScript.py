import urllib2, urllib
from cookielib import CookieJar

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
    page = opener.open("http://google.com")
    if page.geturl() == 'http://www.google.com/':
        return False #no redirect
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
        return -1
    get_url = url[pathIndex:]
    print("get_url = %s" % get_url)
    get_url = urllib.quote_plus(get_url)

    data = startPage.read()
    hashIndex = data.find(hashStartStr)
    if hashIndex == -1:
        return -2
    hashValue = getBetween(hashStartStr, "\"", data)
    print("hash = %s" % hashValue)
    hashValue = urllib.quote_plus(hashValue)

    mac = urllib.quote_plus(mac)

    loginFormFilled = loginForm % (mac, get_url, hashValue)
    print("loginForm = %s" % loginFormFilled)

    resp = opener.open(loginPostUrl, data=loginFormFilled)
    return resp

def main():
    cj = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    pg = getRedirectPage(opener)
    if pg:
        print("Redirected to: %s" % pg.geturl())
        login(pg, opener, "02:9D:E0:90:55:17")
    else:
        print("Connected!")

main()
