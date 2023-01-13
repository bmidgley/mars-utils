# mars-utils
Code and documentation for MDRS projects

# Setup
pip3 install -r requirements.txt

export MHOST=mqtt.hostname.x

export MUSER=user

export MPASS=secret

# Make gpx tracks from meshtastic logs
`mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J >log.txt`

`./mq2gpx.py <log.txt`

# Send gpx tracks back to mqtt
The logs are sent back with the same relative timing they had originally. Reads sample.gpx.

`./gpx2mq.py`

