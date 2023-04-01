#!/usr/bin/env python3

# reads from stdin a log from or output piped from:
# mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J

import sys
import json

stations = {}

print(f'{"name".ljust(15)}{"time".ljust(15)}{"battery".ljust(15)}{"temperature".ljust(15)}{"humidity".ljust(15)}{"location"}')
for line in sys.stdin:
    full_message = json.loads(line)
    message = full_message['payload']
    tst = full_message['tst'][11:19]
    if message['type'] == 'nodeinfo':
        stations[message['from']] = message['payload']['longname']
    if message['type'] == 'position' and message['from'] in stations:
        station_name = stations[message['from']]
        lat = message['payload']['latitude_i'] / 10000000
        lon = message['payload']['longitude_i']  / 10000000
        if 'altitude' in message['payload']:
            alt = message['payload']['altitude']
        else:
            alt = None
        print(f'{station_name.ljust(15)}{tst.ljust(15)}{"".ljust(45)}http://maps.google.com/maps?z=12&t=m&q=loc:{lat}+{lon}')
    if message['type'] == 'telemetry' and message['from'] in stations:
        station_name = stations[message['from']]
        if 'battery_level' in message['payload']:
            battery = message['payload']['battery_level']
            print(f'{station_name.ljust(15)}{tst.ljust(15)}{battery}%')
        if 'relative_humidity' in message['payload'] and 'temperature' in message['payload']:
            relative_humidity = round(message['payload']['relative_humidity'])
            temperature = round(message['payload']['temperature'])
            print(f'{station_name.ljust(15)}{tst.ljust(15)}{"".ljust(15)}{str(temperature).ljust(15)}{str(relative_humidity).ljust(15)}')

