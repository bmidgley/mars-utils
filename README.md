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

The sample is this little jaunt. Note this is privately leased land and I only went on it with permission.

<img width="359" alt="image" src="https://user-images.githubusercontent.com/63477/212521491-2eae3173-de6e-4d23-b437-d4b4afd9fbe5.png">


