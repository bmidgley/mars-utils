#!/usr/bin/env python3

# reads from stdin a log captured using:
# mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J

import sys
import json
import xmltodict

stations = {}
points = {}

for line in sys.stdin:
    full_message = json.loads(line)
    message = full_message['payload']
    if message['type'] == 'nodeinfo':
        stations[message['from']] = message['payload']['longname']
    if message['type'] == 'position' and message['from'] in stations:
        station_name = stations[message['from']]
        if not station_name in points: points[station_name] = []
        entry = {
            '@lat': message['payload']['latitude_i'] / 10000000,
            '@lon': message['payload']['longitude_i']  / 10000000,
            'time': full_message['tst'],
        }
        if 'altitude' in message['payload']:
            entry['ele'] = message['payload']['altitude']
        points[station_name].append(entry)

for station_name in points:
    gpx = {
        'gpx': {
            '@xmlns': "http://www.topografix.com/GPX/1/1", 
            '@xmlns:gpxx': "http://www.garmin.com/xmlschemas/GpxExtensions/v3", 
            '@xmlns:gpxtpx': "http://www.garmin.com/xmlschemas/TrackPointExtension/v1", 
            '@creator': "Oregon 400t", 
            '@version': "1.1", 
            '@xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance", 
            '@xsi:schemaLocation': "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd",
            'trk': {
                'name': station_name,
                'trkseg': {
                    'trkpt': 
                        points[station_name]
                }
            }
        }
    }
    with open(f'{station_name}.gpx', 'w') as gpx_file:
        gpx_file.write(xmltodict.unparse(gpx, pretty=True))
