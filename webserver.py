#!/usr/bin/env python3

# reads from stdin a log from or output piped from:
# mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J
# http://evalink01.westus3.cloudapp.azure.com/ce45fa11-fc6e-47b7-a7fb-ac3b3979b2b7.json
# http://evalink01.westus3.cloudapp.azure.com/57f451ba-95c0-4d17-9c0f-22670042f212.json

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from datetime import datetime
import sys
import json
import geopy.distance
import os, pwd, grp

ignore_points = [{"@lat": 38.405744, "@lon": -110.792172}, {"@lat": 38.4064465, "@lon": -110.791946}]
stations = {1439117596: 'RadGateWay', -1951726776: 'Astro2-MDRS', -240061613: 'Astro1-MDRS'}
hardware_type = {}
response = {}
hab = ignore_points[1]
hostName = "0.0.0.0"
serverPortString = os.environ.get("SERVER_PORT") or "80"

def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    old_umask = os.umask(0o077)

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = bytes(json.dumps(response, indent = 4), "utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header('Content-length', len(payload))
        self.end_headers()
        self.wfile.write(payload)

def distance(p1, p2):
    tup1 = (p1["@lat"], p1["@lon"])
    tup2 = (p2["@lat"], p2["@lon"])
    return geopy.distance.geodesic(tup1, tup2).meters

def main(line):
    full_message = json.loads(line)
    message = full_message['payload']
    iso = datetime.fromtimestamp(message['timestamp']).astimezone().isoformat()
    tst = iso[11:19]
    if message['from'] in stations:
        station_name = stations[message['from']]
        if not station_name in response: response[station_name] = {}
    else:
        station_name = None
    if 'type' in message:
        if message['type'] == 'nodeinfo':
            stations[message['from']] = message['payload']['longname']
            if 'hardware' in message['payload']: hardware_type[message['from']] = message['payload']['hardware']
            station_name = message['payload']['longname']
            print(f'{tst.ljust(15)}{station_name.ljust(16)}')
        if message['type'] == 'position' and station_name:
            lat = message['payload']['latitude_i'] / 10000000
            lon = message['payload']['longitude_i']  / 10000000
            if 'altitude' in message['payload']:
                alt = message['payload']['altitude']
            else:
                alt = None
            dist = distance(hab, {"@lat": lat, "@lon": lon})
            print(f'{tst.ljust(15)}{station_name.ljust(16)}{"".ljust(45)}{int(dist)} http://maps.google.com/maps?z=12&t=k&q=loc:{lat}+{lon}')
            if lat != 0 and lon != 0:
                hw = -1
                if message['from'] in hardware_type: hw = hardware_type[message['from']]
                node_type = 'infrastructure'
                if hw == 7: node_type = 'person'
                response[station_name].update({"position": [lat, lon], "time": iso, "distance": round(dist), 'hardware': hw, 'node_type': node_type})
        if message['type'] == 'telemetry' and station_name:
            if 'battery_level' in message['payload']:
                battery = message['payload']['battery_level']
                print(f'{tst.ljust(15)}{station_name.ljust(16)}{battery}%')
                response[station_name].update({"battery": battery})
            if 'relative_humidity' in message['payload'] and 'temperature' in message['payload']:
                temperature = round(message['payload']['temperature'])
                temperature_string = f'{temperature}c'
                relative_humidity = round(message['payload']['relative_humidity'])
                relative_humidity_string = f'{relative_humidity}%'
                print(f'{tst.ljust(15)}{station_name.ljust(16)}{"".ljust(15)}{temperature_string.ljust(15)}{relative_humidity_string.ljust(15)}')
                response[station_name].update({"temperature": temperature, "humidity": relative_humidity})
        if message['type'] == 'text' and station_name:
            text = message['payload']['text']
            print(f'{tst.ljust(15)}{station_name.ljust(16)}{"".ljust(45)}{text}')
            if 'text' not in response[station_name]:
                response[station_name]['text'] = {}
            response[station_name]['text'].update({iso: text})

if __name__ == "__main__":
    webServer = ThreadingHTTPServer((hostName, int(serverPortString)), MyServer)
    drop_privileges()
    print("Server started http://%s:%s" % (hostName, serverPortString))

    def service():
        try:
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass

        webServer.server_close()
        print("Server stopped.")

    thread = Thread(target=service)
    thread.daemon = True
    thread.start()

    print(f'{"time".ljust(15)}{"name".ljust(16)}{"battery".ljust(15)}{"temperature".ljust(15)}{"humidity".ljust(15)}{"location"}')
    for line in sys.stdin: main(line)
