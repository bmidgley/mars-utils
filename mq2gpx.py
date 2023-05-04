#!/usr/bin/env python3

# reads from stdin a log captured using:
# mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J

import sys
import json
import xmltodict
import dateutil.parser

stations = {}
points = {}
samples = -1

def write_points(station_name, points):
    if points == []: return
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
                        points
                }
            }
        }
    }
    with open(f'{station_name}-{points[0]["time"]}.gpx', 'w') as gpx_file:
        gpx_file.write(xmltodict.unparse(gpx, pretty=True))

def seconds_apart(t1, t2):
    d1=dateutil.parser.isoparse(t1.replace('Z',''))
    d2=dateutil.parser.isoparse(t2.replace('Z',''))
    return((d2 - d1).total_seconds())

for line in sys.stdin:
    full_message = json.loads(line)
    message = full_message['payload']
    if 'type' in message:
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

            if samples != 0:
                samples -= 1
                points[station_name].append(entry)

for station_name in points:
    spoints = points[station_name]

    # break points for the station up by clusters with no more than one hour between samples
    while len(spoints) > 0:
        pslice = []
        pslice.append(spoints.pop(0))

        while len(spoints) > 0 and seconds_apart(pslice[-1]['time'], spoints[0]['time']) < 60 * 60:
            pslice.append(spoints.pop(0))

        write_points(station_name, pslice)
