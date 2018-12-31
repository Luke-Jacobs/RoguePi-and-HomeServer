import socket, time, sys

dbgFile = open("/CONNECTIONS", "w")
printOk = True
if len(sys.argv) > 1: printOk = False

def record(stri):
    dbgFile.write(stri + "\n")
    dbgFile.flush()
    if printOk: print("<HBC>" + stri)

def attemptConnection(soc):
    try:
        soc.connect(("67.184.6.29", 8000))
        return True
    except Exception, e:
        print "Error:"+str(e)
        return False


while True:
    s = socket.socket()
    s.settimeout(20)
    try:
        s.connect(("67.184.6.29", 8000))
    except Exception, e:
        record("Error: %s" % str(e))
        time.sleep(1)
        continue
    record("Connected!")
    s.settimeout(15)

    while True:
        try:
            now = time.localtime()
            s.send(("%d:%d" % (now.tm_min, now.tm_sec)).encode())
        except Exception, e:
            record("Error: %s" % str(e))
            break
        time.sleep(2)
