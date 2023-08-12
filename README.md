# mars-utils
Code and documentation for MDRS projects. Requires the json option be turned on in the meshtastic node that publishes to mqtt.

Written for mac/linux, calling the mosquitto_pub command-line app directly.

# Demo

* https://www.youtube.com/watch?v=gMkGpYlth6w

# Setup

```
pip3 install -r requirements.txt
sudo apt install -y mosquitto
export MHOST=mqtt.hostname.x
export MUSER=user
export MPASS=secret
export MSERVERUSER=pi
sudo -E ./webserver-logger.sh
```

# Make gpx tracks from meshtastic logs

This will make one gpx file for each station reporting positions. It writes to stationlongname.gpx.

`mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J >log.txt`

`./mq2gpx.py <log.txt`

# Send gpx tracks back to mqtt
The logs are sent back with the same relative timing they had originally. It reads coordinates and labels the character using the name in sample.gpx: "Astronaut1".

`./gpx2mq.py`

The sample is this little jaunt around MDRS. Note this is privately leased land and I only went on it with permission.

<img width="359" alt="image" src="https://user-images.githubusercontent.com/63477/212521491-2eae3173-de6e-4d23-b437-d4b4afd9fbe5.png">

# Serve json with data on latest positions

Uses localhost and no encryption, so it must run on the mosquitto host and have SSL added via proxy. Reads and stores ~/mqlog.txt:

`./webserver-logger.sh`
