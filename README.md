# RoguePi

### Skills Developed

The skills I developed with this project were the following:

- How to program network functions to automate the wifi login procedure to an Xfinity hotspot.
- Designing my device to be persistent over wifi, even when its wifi access was constantly changing.
- Sending images over a TCP server.

### Inspiration

![Monkey Bars](Pictures/Monkey%20Bars.jpg)

These monkey bars are where I do pullups for exercise. The problem that I ran into was that sometimes kids would show up at the park and would climb on the monkey bars, which meant that I could not do my pullups. This was totally fine, but I didn't want to trek out to the park only to have to turn around and walk back to my house. This inconvenience inspired my RoguePi project.

### Device

![Device Overview](Pictures/Device%20Overview.jpg)

The core of the device is the Raspberry Pi with a wifi adapter. For debugging purposes, I added a few GPIO lights. The first three lights indicate connection status, and the last light turns on when the device is waiting on my home server. I can use this last light to position the device in a place with good reception of wifi. The Pi is powered by a USB battery pack and enclosed by a pencil box (cheap waterproofing).

The Pi runs a Python script I wrote ([RoguePi.py](RoguePi/RoguePi.py)) to continuously check if it is connected to an xfinitywifi hotspot. These hotspots are scattered about my neighborhood and are free for me to use after I login to the gateway with my Comcast account. Embedded in my program is a script that automates the login so that the Pi can hop from connection to connection as it is moving from one place to another. When it receives internet access, it then connects to my Python server at home. It continuously checks to see if the connection is valid by sending pings and expecting a server response. Whenever the server gives a command (like a picture request), the Pi responds. The end result is that I can place this device within range of any free xfinitywifi hotspot, and my home server will be able to control it.

![RoguePi on the hill](Pictures/RoguePi%20on%20the%20hill.jpg)

I placed the RoguePi on a hill overlooking the park. It is far enough away so that I don't know who is at the park, but close enough so that I can see if there are people at the park. I did this because I didn't want to spy on the kids, but just know if they were present. There is a home nearby with a free XfinityWifi hotspot, so the device automatically engages its connection procedure as I move it to the location.

![](Pictures/Device%20Image.jpg)

This is an image I received from the device. I edited the picture to zoom in on the monkey bars.
