#!/usr/bin/env python3

# reads from stdin a log from or output piped from:
# mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J

import sys
import json

stations = {1439117596: 'RadGateWay', -1951726776: 'Astro2-MDRS', -240061613: 'Astro1-MDRS'}
heard = {}

for line in sys.stdin:
    full_message = json.loads(line)
    message = full_message['payload']
    tst = full_message['tst'][11:19]
    if message['from'] in stations:
        station_name = stations[message['from']]
        heard[station_name] = heard.get(station_name, {'lat': None, 'lng': None, 'alt': None, 'temperature': None, 'relative_humidity': None, 'battery': None})
    else:
        station_name = None
    if message['type'] == 'nodeinfo':
        stations[message['from']] = message['payload']['longname']
        station_name = message['payload']['longname']
        heard[station_name] = heard.get(station_name, {'lat': None, 'lng': None, 'alt': None, 'temperature': None, 'relative_humidity': None, 'battery': None})
    if message['type'] == 'position' and station_name:
        heard[station_name]['lat'] = message['payload']['latitude_i'] / 10000000
        heard[station_name]['lng'] = message['payload']['longitude_i']  / 10000000
        if 'altitude' in message['payload']:
            heard[station_name]['alt'] = message['payload']['altitude']
    if message['type'] == 'telemetry' and station_name:
        if 'battery_level' in message['payload']:
            heard[station_name]['battery'] = message['payload']['battery_level']
        if 'relative_humidity' in message['payload'] and 'temperature' in message['payload']:
            heard[station_name]['temperature'] = round(message['payload']['temperature'], 1)
            heard[station_name]['relative_humidity'] = round(message['payload']['relative_humidity'], 1)
    print(json.dumps({station_name: heard[station_name]}))
    print(f'{station_name}: {list(heard[station_name].values())}')