#!/usr/bin/env python3

# invokes mosquitto_pub with messages that represent re-running sample.gpx file as if it is happening now
# requires environment variables MHOST, MUSER, MPASS

send_cmd = 'mosquitto_pub -p 8883 -h $MHOST -t "msh/2/json/LongFast/!faker" -u $MUSER -P $MPASS --tls-use-os-certs'

import xmltodict
import pytz
import time
import json
import os
from datetime import datetime
from dateutil import parser

with open(f'sample.gpx', 'r') as gpx_file:
    data = xmltodict.parse(gpx_file.read())

trk = data['gpx']['trk']
name = trk['name']

points = trk['trkseg'][1]['trkpt']

start_time = parser.parse(points[0]['time'])
adjustment = datetime.now(pytz.utc) - start_time

for point in points:
    nodeinfo = {'from': '1', 'payload': {'type': 'nodeinfo', 'longname': name}}
    position = {'from': '1', 'payload': {
        'latitude_i': int(float(point['@lat'])*10000000),
        'longitude_i': int(float(point['@lon'])*10000000),
        'elevation': int(float(point['ele']))}
    }
    timestamp = parser.parse(point['time']) + adjustment
    while(timestamp > datetime.now(pytz.utc)): time.sleep(1)
    for message in [nodeinfo, position]:
        os.system(f'{send_cmd} -m {json.dumps(json.dumps(message))}')

