import urllib2, urllib, json, time, sys, socket, subprocess
from cookielib import CookieJar

#debug
dbgFile = open("/LINK", "w")
printOk = True
if len(sys.argv) > 1: printOk = False

def record(data):
    if printOk: print("<LINK>" + data)
    dbgFile.write(data + "\n")
    dbgFile.flush()


#constants
loginPostUrl = "https://wifilogin.xfinity.com/user_login.php"
loginForm = """
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

loginPageUrl = "https://wifilogin.xfinity.com/start.php"
hashStartStr = "<input type=\"hidden\" name=\"hash\" value=\""

#xfinitywifi login functions
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

#base connector functions
def attemptConnection(soc):
    try:
        soc.connect(("67.184.6.29", 8000))
        return True
    except Exception, e:
        print "Error:"+str(e)
        return False

#vpn functions
def killVPN():
    vpnProcesses = subprocess.check_output("ps -A | grep vpn").split("\n")
    record("[i] ps returned: %s" % repr(vpnProcesses))
    vpnProcesses.remove("")
    for proc in vpnProcesses:
        id = proc.split(" ")[1]
        record("[i] Killing vpn process (%s)" % id)
        subprocess.Popen("kill -2 %s" % id, shell=True)

def startVPN():
    vpnProcesses = subprocess.check_output("ps -A | grep vpn").split("\n")
    if not vpnProcesses:
        record("[+] VPN is already running")
        return False
    p = subprocess.Popen("openvpn /etc/openvpn/vpngate_japan.ovpn", shell=True)  # start vpn
    record("[i] Starting VPN")
    return p

#main
#   check if connected to an xfinitywifi
#       check if connected to internet (get google)
#           check if connected to 67.184.6.29
def main():
    while True:
        essidData = subprocess.check_output("iwgetid")
        record("[i] iwgetid returned: %s" % repr(essidData))

        while essidData != "": #if connected to some wifi
            record("[+] Connected to wifi")
            loginResult = loginIfNeeded()
            record("[i] loginResult = %d" % loginResult)

            while loginResult: #if can access internet
                record("[++] Can access internet")
                vpnProc = startVPN()
                if vpnProc: #if started the vpn for the 1st time
                    while True: #wait till vpn is done starting
                        line = vpnProc.stdout.readline()
                        if line.count("Sequence Complete"):
                            break

                #try to connect to home
                record("[i] Trying to connect to home...")
                s = socket.socket()
                s.settimeout(15)
                try:
                    s.connect(("67.184.6.29", 8000))
                except Exception, e:
                    record("[-] Home connection error: %s" % str(e))
                    time.sleep(2) #wait 2s to retry home connection
                    continue

                # if can access home
                record("[+++] Connected to home base!")
                s.settimeout(15)
                while True:
                    try:
                        now = time.localtime()
                        s.send(("%d:%d" % (now.tm_min, now.tm_sec)).encode())
                    except Exception, e:
                        record("[-] Home sending error: %s" % str(e))
                        break
                    time.sleep(2)

                record("[i] Killing VPN")
                killVPN()
                loginResult = loginIfNeeded()

            essidData = subprocess.check_output("iwgetid")
        time.sleep(2) #wait 2s for wifi connection

main()