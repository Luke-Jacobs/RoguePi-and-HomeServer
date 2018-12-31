import socket, time

def attemptConnection(soc):
    try:
        soc.connect(("67.184.6.29", 1101))
        return True
    except:
        return False


s = socket.socket()
while True:
    if not attemptConnection(s):
        time.sleep(2)
        print("Attempting connection...")
        continue
    print("Connected!")
    while True:
        try:
            s.send(str(time.time()).encode())
        except Exception as e:
            print("Error: ", str(e))
            break
        time.sleep(2)
