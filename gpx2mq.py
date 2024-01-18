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
import random
from datetime import datetime
from dateutil import parser

def get_position(point, adjustment):
  timestamp = parser.parse(point['time']) + adjustment
  seconds = int(timestamp.timestamp())
  return timestamp, seconds, {'from': '1', 'type': 'position', 'timestamp': seconds, 'payload': {'hardware': 7,
          'latitude_i': int(float(point['@lat'])*10000000),
          'longitude_i': int(float(point['@lon'])*10000000),
          'elevation': int(float(point['ele']))}}

def inject_file(filename):
    with open(filename, 'r') as gpx_file:
        data = xmltodict.parse(gpx_file.read())

    trk = data['gpx']['trk']
    code = random.randint(10, 30)
    name = f'@{code}-{trk["name"]}'

    points = trk['trkseg']['trkpt']

    start_time = parser.parse(points[0]['time'])
    adjustment = datetime.now(pytz.utc) - start_time

    # send waypoints to bus as location and text
    waypoints = []
    if 'wpt' in data['gpx']:
      for point in data['gpx']['wpt']:
        timestamp, seconds, position = get_position(point, adjustment)
        waypoints.append(position)
        waypoints.append({'from': '1', 'type': 'text', 'timestamp': seconds, 'payload': {'text': point['name'], 'hardware': 0}})
    print(f'waypoints: {waypoints}')

    for point in points:
        print(point)
        timestamp, seconds, position = get_position(point, adjustment)
        nodeinfo = {'from': '1', 'type': 'nodeinfo', 'timestamp': seconds, 'payload': {'longname': name, 'hardware': 7}}
        while len(waypoints) > 0 and waypoints[0]['timestamp'] < seconds:
          message = waypoints.pop(0)
          while(message['timestamp'] > datetime.now(pytz.utc)): time.sleep(1)
          print(message)
          os.system(f'{send_cmd} -m {json.dumps(json.dumps(message))}')
        while(timestamp > datetime.now(pytz.utc)): time.sleep(1)
        for message in [nodeinfo, position]:
            print(message)
            os.system(f'{send_cmd} -m {json.dumps(json.dumps(message))}')

if __name__ == "__main__":
    filenames = 'sample.gpx'
    if len(sys.argv) > 1:
        filenames = sys.argv[1:]
    for filename in filenames:
        inject_file(filename)
