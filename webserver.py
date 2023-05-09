#!/usr/bin/env python3

# reads from stdin a log from or output piped from:
# mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import sys
import json
import geopy.distance
import os, pwd, grp

ignore_points = [{"@lat": 38.405744, "@lon": -110.792172}, {"@lat": 38.4064465, "@lon": -110.791946}]
stations = {1439117596: 'RadGateWay', -1951726776: 'Astro2-MDRS', -240061613: 'Astro1-MDRS'}
response = {}
hab = ignore_points[1]
hostName = "0.0.0.0"
serverPort = 80

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
    tst = full_message['tst'][11:19]
    iso = full_message['tst'].replace('Z', '')
    if message['from'] in stations:
        station_name = stations[message['from']]
    else:
        station_name = None
    if 'type' in message:
        if message['type'] == 'nodeinfo':
            stations[message['from']] = message['payload']['longname']
            station_name = message['payload']['longname']
            print(f'{tst.ljust(15)}{station_name.ljust(15)}')
        if message['type'] == 'position' and station_name:
            lat = message['payload']['latitude_i'] / 10000000
            lon = message['payload']['longitude_i']  / 10000000
            if 'altitude' in message['payload']:
                alt = message['payload']['altitude']
            else:
                alt = None
            dist = distance(hab, {"@lat": lat, "@lon": lon})
            print(f'{tst.ljust(15)}{station_name.ljust(15)}{"".ljust(45)}{int(dist)} http://maps.google.com/maps?z=12&t=k&q=loc:{lat}+{lon}')
            if dist > 20 and lat != 0 and lon != 0:
                response[station_name] = {"position": [lat, lon], "time": iso, "distance": dist}
        if message['type'] == 'telemetry' and station_name:
            if 'battery_level' in message['payload']:
                battery = message['payload']['battery_level']
                print(f'{tst.ljust(15)}{station_name.ljust(15)}{battery}%')
            if 'relative_humidity' in message['payload'] and 'temperature' in message['payload']:
                temperature = str(round(message['payload']['temperature'])) + 'c'
                relative_humidity = str(round(message['payload']['relative_humidity'])) + '%'
                print(f'{tst.ljust(15)}{station_name.ljust(15)}{"".ljust(15)}{temperature.ljust(15)}{relative_humidity.ljust(15)}')

if __name__ == "__main__":
    webServer = ThreadingHTTPServer((hostName, serverPort), MyServer)
    drop_privileges()
    print("Server started http://%s:%s" % (hostName, serverPort))

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

    print(f'{"time".ljust(15)}{"name".ljust(15)}{"battery".ljust(15)}{"temperature".ljust(15)}{"humidity".ljust(15)}{"location"}')
    for line in sys.stdin: main(line)