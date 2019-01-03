from sys import path
path.append('/home/pi/RoguePi/Modules')  # For importing modules from another folder
from CameraModule import Camera
from TimelapseModule import Timelapse

# Global Constants
services = {"camera": Camera(),
            "timelapse": Timelapse()}
TXT = "TXT----"  # To tag our response to the HomeServer so that it knows it can display it. (ie. It's not an image)


def PiExecute(cmd):
    """
    This function receives raw commands and sends them out to the right module (service). It manages the threads of the services.
    :param str cmd: raw command
    :return bytes: response of a service
    """

    global services
    cmd = cmd.split(" ")  # cmd and args

    # Start a specific thread
    if cmd[0] == "start":
        if services[cmd[1]].is_alive():
            return TXT + "[-] Service is already running!"
        try:
            services[cmd[1]].start()
            return TXT + "[i] Starting %s..." % cmd[1]
        except RuntimeError, e:  # If the Thread has been already started, restart it
            print 'RuntimeError: %s' % str(e)
            serviceClass = type(services[cmd[1]])  # Grab the class that made the object
            services[cmd[1]] = serviceClass()  # Re-init our object so that we can restart the thread
            return TXT + "[i] Restarted object"

    # Stop a specific module
    elif cmd[0] == "stop":
        services[cmd[1]].stop()
        return TXT + "[i] Stopping %s..." % cmd[1]

    # Kill all the running modules
    elif cmd[0] == "killall":
        for s in services:
            services[s].stop()
        return TXT + "[+] Killed all services"

    # Finish program - it will not start again
    elif cmd[0] == "sleep":
        exit(0)

    # Check on a thread
    elif cmd[0] == "status":
        return services[cmd[1]].status()

    # Send commands straight to a specific thread
    elif cmd[0] in services:
        return services[cmd[0]][cmd[1:]]  # Execute a special command in a specific module

    # If the function received an unknown command
    else:
        return TXT + "[-] Unknown command to give to device"
