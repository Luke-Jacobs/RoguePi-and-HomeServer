# RoguePi Code

I set this script to autostart whenever the device boots. 

### Core 

- The `searchForConnection` method continuously performs a self-check on the device's connection. 
  - It logs the status of the device and updates the debugging GPIO lights. 
  - If the device detects that it is associated with an XfinityWifi hotspot, it automatically logs in with my family's Comcast credentials.
  - It then repeatedly attempts to connect to the HomeServer.
- When we get a home connection, execution gets passed to `attendToConnection` . 
  - It continuously checks to see if the connection is valid by sending PINGs to the server. It expects a PONG response within a timeout period, or else it closes the connection. (This is to ensure that the device does not attend to a dead connection.)
  - It receives commands, executes them by calling `PiExecute`, and sends the command output back to the HomeServer.
-  `PiExecute` manages command modules that run as services.
  - It starts and stops threads.
  - It returns the statuses of threads.
  - It passes execution to an addon object (ex. Camera, Timelapse) and returns their output.

### Modules

- `Camera` - Returns a live image on request
- `Timelapse` - On request, it starts a timelapse with configurable options.