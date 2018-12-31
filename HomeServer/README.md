# HomeServer

This file is run on my home desktop. It is a server that receives connections from the RoguePi. In order for it to work with non-local connections, the network router needs to have the receiving port forwarded to the server device. (My Xfinity-Router-Interface code can automatically do this.)

### Structure 

- `waitForConnections` - Waits for connections from the Raspberry Pi. If it receives a connection, it calls manageConnection.
- `manageConnection` - Receives an open socket and an InputHandler instance. Handles PING/PONGs and displays or saves data received from the RoguePi.
- `InputHandler` - A thread that receives and asks for user input while the other functions handle the time-sensitive socket interactions.

