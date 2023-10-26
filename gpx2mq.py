#!/usr/bin/env python3

# invokes mosquitto_pub with messages that represent re-running sample.gpx file as if it is happening now
# requires environment variables MHOST, MUSER, MPASS

send_cmd = 'mosquitto_pub -h $MHOST -t "msh/2/json/LongFast/!faker" -u $MUSER -P $MPASS'

import xmltodict
import pytz
import time
import json
import os
import sys
from datetime import datetime
from dateutil import parser

def inject_file(filename):
    with open(filename, 'r') as gpx_file:
        data = xmltodict.parse(gpx_file.read())

    # todo: send waypoints to bus
    waypoints = data['gpx']['wpt']

    trk = data['gpx']['trk']
    name = f'@{trk["name"]}'

    points = trk['trkseg']['trkpt']

    start_time = parser.parse(points[0]['time'])
    adjustment = datetime.now(pytz.utc) - start_time

    for point in points:
        timestamp = parser.parse(point['time']) + adjustment
        seconds = int(timestamp.timestamp())
        nodeinfo = {'from': '1', 'type': 'nodeinfo', 'timestamp': seconds, 'payload': {'longname': name, 'hardware': 7}}
        position = {'from': '1', 'type': 'position', 'timestamp': seconds, 'payload': {'hardware': 7,
            'latitude_i': int(float(point['@lat'])*10000000),
            'longitude_i': int(float(point['@lon'])*10000000),
            'elevation': int(float(point['ele']))}
        }
        while(timestamp > datetime.now(pytz.utc)): time.sleep(1)
        for message in [nodeinfo, position]:
            os.system(f'{send_cmd} -m {json.dumps(json.dumps(message))}')

if __name__ == "__main__":
    filenames = 'sample.gpx'
    if len(sys.argv) > 1:
        filenames = sys.argv[1:]
    for filename in filenames:
        inject_file(filename)