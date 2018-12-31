import urllib2, urllib, json, time, sys, socket, subprocess, signal, select
import RPi.GPIO as GPIO
from cookielib import CookieJar
from PiExecute import PiExecute

# Debug
dbgFile = open("/LINK", "w")
printOk = True
if len(sys.argv) > 1:
    printOk = False


def record(data):
    if printOk:
        print("<LINK>" + data)
    dbgFile.write(data + "\n")
    dbgFile.flush()


# Constants
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

HOMEPORT = 8554
TXT = "TXT----"


# Xfinitywifi login functions
def getBetween(startStr, endStr, haystackStr):
    startLoc = haystackStr.find(startStr) + len(startStr)
    endLoc = haystackStr[startLoc:].find(endStr) + startLoc
    return haystackStr[startLoc:endLoc]


def getRedirectPage(opener):
    try:
        page = opener.open("http://google.com", timeout=4)
    except urllib2.URLError, e:
        record("[-] URLError visiting google.com: %s" % str(e))
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
        record("Redirected to: %s" % pg.geturl())
        return login(pg, opener, "02:9D:E0:90:55:17")


#base connector functions
def attemptConnection(soc):
    try:
        soc.connect(("67.184.6.29", HOMEPORT))
        return True
    except Exception, e:
        print "Error:"+str(e)
        return False


# VPN functions
def killVPN():
    try:
        vpnProcesses = subprocess.check_output("ps -A | grep vpn", shell=True).split("\n")
    except subprocess.CalledProcessError:
        return True
    record("[i] ps returned: %s" % repr(vpnProcesses))
    vpnProcesses.remove("")
    for proc in vpnProcesses:
        id = proc.split(" ")[1]
        record("[i] Killing vpn process (%s)" % id)
        subprocess.Popen("sudo kill -9 %s" % id, shell=True)

def startVPN():
    try:    
        vpnProcesses = subprocess.check_output("ps -A | grep vpn", shell=True)
    except subprocess.CalledProcessError:
        vpnProcesses = None

    if not vpnProcesses or vpnProcesses.count("defunct"): #if not running
        record("[i] Starting VPN...")
        p = subprocess.Popen("openvpn /etc/openvpn/vpngate_japan.ovpn", shell=True, stdout=subprocess.PIPE)  # start vpn
        if p:
            while True:  # wait till vpn is done starting
                line = p.stdout.readline()
                if line.count("Sequence Complete"):
                    break
            record("[+] VPN Connected!")
        return True
    else:
        record("[i] VPN is already running")
        return False

#GPIO functions
pin1 = 7
pin2 = 10
pin3 = 12

def setupPins():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pin1, GPIO.OUT)
    GPIO.setup(pin2, GPIO.OUT)
    GPIO.setup(pin3, GPIO.OUT)

def pinsOff():
    GPIO.output(pin1, 0)
    GPIO.output(pin2, 0)
    GPIO.output(pin3, 0)


#signal handler
def ctrlc(signal, frame):
    print("Exiting...")
    pinsOff()
    killVPN()
    PiExecute("KILLALL")
    sys.exit(0)

#colored text
RED = "\033[0;31m"
GREEN = "\033[0;32m"
NC = "\033[0m"

def red(txt): return RED+txt+NC
def green(txt): return GREEN+txt+NC

#functions to check status of connections
def checkWifi():
    try:
        essidData = subprocess.check_output("iwgetid")
        return True
    except subprocess.CalledProcessError: #if not connected
        return False


#main
#   check if connected to an xfinitywifi
#       check if connected to internet (get google)
#           check if connected to 67.184.6.29
def main():
    # Setup
    setupPins()
    pinsOff()
    signal.signal(signal.SIGINT, ctrlc)
    killVPN()

    # Checks
    hasWifi = False
    hasInternet = False
    hasConnection = False

    while True:

        hasWifi = checkWifi()

        while hasWifi:  # If connected to some wifi
            record(green("[+] Connected to wifi"))
            GPIO.output(pin1, 1)

            hasInternet = loginIfNeeded()

            while hasInternet:  # If can access internet
                record(green("[++] Can access internet"))
                GPIO.output(pin2, 1)

                startVPN()

                # Try to connect to home
                record("[i] Trying to connect to home...")
                s = socket.socket()
                s.settimeout(8)  # Timeout for initial connection
                nFails = 0
                for i in range(2):  # 2 trys for connection before checking wifi
                    try:
                        s.connect(("67.184.6.29", HOMEPORT))
                        break
                    except Exception, e:
                        nFails += 1
                if nFails == 2: #if both attempts failed
                    killVPN()
                    hasInternet = loginIfNeeded()
                    continue

                # if can access home
                record(green("[+++] Connected to home base!"))
                GPIO.output(pin3, 1)
                s.settimeout(20) #timeout for losing connection

                while True:
                    try:
                        # send ping and wait for pong
                        record("[i] Sending PING...")
                        s.send(b"PING")
                        resp = s.recv(4)
                        if resp != b"PONG":
                            record("[-] Unusual response from home: %s" % resp)
                        else:
                            record("[+] Received PONG!")

                        # receive and execute commands
                        ready = select.select([s], [], [], 3)
                        if ready[0]: #if command ready
                            cmd = s.recv(2048)
                            record("[+] Got data: %s" % cmd)
                            response = PiExecute(cmd)
                            if not response: response = TXT + "[-] Run CMD returned None"
                            #record("[i] Server response: %s" % response)
                            s.sendall(response)
                            if len(response) > 2048: #extra time
                                time.sleep(5)
                            time.sleep(1) #sleep a little before pinging

                    except Exception, e:
                        record("[-] Home sending/receiving error: %s" % str(e))
                        break
                    time.sleep(2)

                #if home connection broken
                record(red("[---] Home connection broken...killing VPN"))
                GPIO.output(pin3, 0)
                killVPN()
                hasInternet = loginIfNeeded()
            #if internet connection broke
            record(red("[--] Internet connection broken"))
            GPIO.output(pin2, 0)
            hasWifi = checkWifi()
        #if no wifi connection
        GPIO.output(pin1, 0)
        record(red("[-] Wifi connection broken")) 
        time.sleep(2) #wait 2s for wifi connection


main()
