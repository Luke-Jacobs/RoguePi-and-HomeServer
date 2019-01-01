# RoguePi

### Inspiration

![Monkey Bars](Pictures/Monkey%20Bars.jpg)

These monkey bars are where I do pullups for exercise. The problem that I ran into was that sometimes kids would show up the park and would climb on the monkey bars like they were intended to be used. (I know, crazy right!) When kids were on the monkey bars, I could not do my pullups. This was totally fine, but I didn't want to trek out to the park only to have to turn around and walk back to my house. This inconvenience inspired my RoguePi project.

### Device

![Device Overview](Pictures/Device%20Overview.jpg)

The core of the device is the Raspberry Pi with a wifi adapter. For debugging purposes, I added a few GPIO lights. The first three lights indicate connection status, and the last light turns on when the device is waiting on my home server. I can use this last light to position the device in a place with good reception of wifi. The Pi is powered by a USB battery pack and enclosed by a pencil box (cheap waterproofing).

The Pi runs a Python script I wrote ([Here](RoguePi/RoguePi.py)) to continuously check if it is connected to an xfinitywifi. If it is, it automatically logs in to the hotspot and then connects to my Python server at home. It continuously checks to see if the connection is valid by sending pings and expecting a server response. Whenever the server gives a command (like a picture request), the Pi responds. The end result is that I can place this device within range of any free xfinitywifi hotspot, and it will work.

![RoguePi on the hill](Pictures/RoguePi%20on%20the%20hill.jpg)

I placed the RoguePi on a hill overlooking the park. It is far enough away so that I don't know who is at the park, but close enough so that I can see if there are people at the park. I did this because I didn't want to spy on the kids, but only wanted to know if they were present. There is a home nearby with a free XfinityWifi hotspot, so the device automatically engages its connection procedure as I move it to the location.

![](Pictures/Device%20Image.jpg)

This is an image I received from the device. I edited the picture to zoom in on the monkey bars.