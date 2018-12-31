from sys import path
path.append('Modules')  # For importing modules from another folder
from CameraModule import Camera
from TimelapseModule import Timelapse

# Global Constants
services = {"CAMERA": Camera(),
            "TIMELAPSE": Timelapse()}
TXT = "TXT----"


def PiExecute(cmd):
    """
    This function receives raw commands and sends them out to the right module (service)
    :param cmd: raw command
    :return: response of a service
    """

    global services
    cmd = cmd.split(" ")  # cmd and args

    # Start a specific thread
    if cmd[0] == "START":
        services[cmd[1]].start()
        return TXT + "[i] Starting %s..." % cmd[1]

    #Stop a specific module
    elif cmd[0] == "STOP":
        services[cmd[1]].stop()
        return TXT + "[i] Stopping %s..." % cmd[1]

    # Kill all the running modules
    elif cmd[0] == "KILLALL":
        for s in services:
            services[s].stop()
        return TXT + "[+] Killed all services"

    # Check on a thread
    elif cmd[0] == "STATUS":
        return services[cmd[1]].status()

    # Send commands straight to a specific thread
    elif cmd[0] in services:
        if not services[cmd[0]].isAlive():  # If that service is not alive
            return TXT + "[-] That service (%s) is not alive!" % cmd[0]
        else:  # If the service is alive and will respond to us
            return services[cmd[0]][cmd[1]]  # Execute a special command in a specific module

    # If the function received an unknown command
    else:
        return TXT + "[-] Unknown command to give to service"
