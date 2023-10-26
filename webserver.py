#!/usr/bin/env python3

# reads from stdin a log from or output piped from:
# mosquitto_sub -p 8883 -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS --tls-use-os-certs -F %J
# -or- mosquitto_sub -h $MHOST -t 'msh/+/json/#' -u $MUSER -P $MPASS -F %J
# http://evalink01.westus3.cloudapp.azure.com/ce45fa11-fc6e-47b7-a7fb-ac3b3979b2b7.json
# http://evalink01.westus3.cloudapp.azure.com/57f451ba-95c0-4d17-9c0f-22670042f212.json

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from datetime import datetime
import pytz
import sys
import json
import geopy.distance
import os, pwd, grp, glob, tempfile, re

ignore_points = [{"@lat": 38.405744, "@lon": -110.792172}, {"@lat": 38.4064465, "@lon": -110.791946}]
stations = {1439117596: 'RadGateWay', -1951726776: 'Astro2-MDRS', -240061613: 'Astro1-MDRS'}
hardware_type = {}
response = {}
hab = ignore_points[1]
hostName = "0.0.0.0"
serverPortString = os.environ.get("SERVER_PORT") or "80"
new_uid_name = os.environ.get("MUID_NAME") or "pi"
start_day = datetime.now().day
start_minute = datetime.now().minute

def merge(a: dict, b: dict, path=[]):
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

def drop_privileges(uid_name='pi', gid_name='nogroup'):
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
        secret = '57f451ba-95c0-4d17-9c0f-22670042f212'
        if 'MSECRET' in os.environ: secret = os.environ['MSECRET']
        splits = self.path.split('?')
        if self.path == f'/{secret}.html':
            with open('index.html', 'r') as file: payload = bytes(file.read(), 'utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header('Content-Length', len(payload))
            self.end_headers()
            self.wfile.write(payload)
        elif splits[0] == f'/{secret}.json':
            if len(splits) == 2:
                date = splits[1].split('&')[0].split('=')[1]
                if not re.fullmatch("[-0-9]+", date): return
                with open(f'{sys.argv[1]}/{date}.json', 'r') as file: payload = bytes(file.read(), 'utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header('Content-Length', len(payload))
                self.end_headers()
                self.wfile.write(payload)
                return
            payload = bytes(json.dumps(response, indent = 4), "utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header('Content-length', len(payload))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == f'/{secret}/logs':
            dates = [os.path.basename(x) for x in sorted(glob.glob(sys.argv[1] + '/????-??-??'))]
            payload = bytes(json.dumps(dates), "utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header('Content-length', len(payload))
            self.end_headers()
            self.wfile.write(payload)
        elif splits[0] == f'/{secret}.zip':
            params = []
            if len(splits) > 1:
                values = splits[1].split('&')
                for value in values:
                    params.append(value.split('=')[1])
            dates = [os.path.basename(x) for x in sorted(glob.glob(sys.argv[1] + '/????-??-??'))]
            included = []
            for date in dates:
                if date >= params[0] and date <= params[1]: included.append(sys.argv[1] + '/' + date)
            print(f'produce zipfile from {included}')
            with tempfile.TemporaryDirectory() as path:
                print(f'writing to {path}')
                os.system(f'cat {" ".join(included)} | ./mq2gpx.py {path}')
                os.system(f'zip -j {path}/gpx {path}/*.gpx {path}/*.csv')
                if not os.path.exists(f'{path}/gpx.zip'):
                    self.respond404(message='No tracks found in the date range')
                    return
                with open(f'{path}/gpx.zip', 'rb') as file: payload = file.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header('Content-Length', len(payload))
                self.end_headers()
                self.wfile.write(payload)
        else:
            self.respond404(message='404')

    def respond404(self, message):
        payload = bytes(f'<html><body>{message}</body></html>', 'utf-8')
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.send_header('Content-length', len(payload))
        self.end_headers()
        self.wfile.write(payload)

def distance(p1, p2):
    tup1 = (p1["@lat"], p1["@lon"])
    tup2 = (p2["@lat"], p2["@lon"])
    try:
        return geopy.distance.geodesic(tup1, tup2).meters
    except:
        return -1

def add_time(station_name, seconds):
    tm = datetime.fromtimestamp(seconds)
    tm = tm.astimezone(pytz.utc)
    if station_name not in response: response[station_name] = {}
    response[station_name].update({"time": tm.isoformat()})

def merge_previous_days(folder):
    today = str(datetime.today().date())
    combined = {}
    dates = [os.path.basename(x) for x in sorted(glob.glob(folder + '/????-??-??'))]
    for date in dates:
        if date == today or date == '0000-00-00': continue
        with open(f'{folder}/{date}.json', 'r') as file:
            try:
                data = json.load(file)
                merge(combined, data)
            except:
                print(f'skipping {date}')
    with open(f'{folder}/0000-00-00.json', 'w') as file:
        file.write(json.dumps(combined, indent = 4))
    return(combined)

def main(line):
    try:
        full_message = json.loads(line)
        message = full_message['payload']
        iso = datetime.fromtimestamp(message['timestamp']).isoformat()
    except Exception as exc:
        print(f"{exc} on {line}")
        return
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
            add_time(station_name, message['timestamp'])
        elif message['type'] == 'position' and station_name:
            lat = message['payload']['latitude_i'] / 10000000
            lon = message['payload']['longitude_i']  / 10000000
            if 'altitude' in message['payload']:
                alt = message['payload']['altitude']
            else:
                alt = None
            if 'ground_speed' in message['payload']:
                ground_speed = message['payload']['ground_speed']
            else:
                ground_speed = None
            if 'ground_track' in message['payload']:
                ground_track = message['payload']['ground_track'] / 100000
            else:
                ground_track = None
            dist = distance(hab, {"@lat": lat, "@lon": lon})
            print(f'{tst.ljust(15)}{station_name.ljust(16)}{"".ljust(45)}{int(dist)} http://maps.google.com/maps?z=12&t=k&q=loc:{lat}+{lon}')
            if lat != 0 and lon != 0:
                hw = -1
                if message['from'] in hardware_type: hw = hardware_type[message['from']]
                node_type = 'infrastructure'
                if hw == 7: node_type = 'person'
                response[station_name].update({"position": [lat, lon], "distance": round(dist), 'hardware': hw, 'node_type': node_type})
                add_time(station_name, message['timestamp'])
            if alt:
                response[station_name].update({"altitude": alt})
            if ground_speed:
                response[station_name].update({"ground_speed": ground_speed})
            if ground_track:
                response[station_name].update({"ground_track": ground_track})
        elif message['type'] == 'telemetry' and station_name:
            if 'battery_level' in message['payload']:
                battery = message['payload']['battery_level']
                print(f'{tst.ljust(15)}{station_name.ljust(16)}{battery}%')
                response[station_name].update({"battery": battery})
            if 'relative_humidity' in message['payload'] and 'temperature' in message['payload']:
                temperature = round(message['payload']['temperature'] or -1)
                temperature_string = f'{temperature}c'
                relative_humidity = round(message['payload']['relative_humidity'] or -1)
                relative_humidity_string = f'{relative_humidity}%'
                print(f'{tst.ljust(15)}{station_name.ljust(16)}{"".ljust(15)}{temperature_string.ljust(15)}{relative_humidity_string.ljust(15)}')
                if temperature != -1: response[station_name].update({"temperature": temperature, "humidity": relative_humidity})
            if message['payload'].get('current'):
                current = round(message['payload']['current'])
                response[station_name].update({"current": current})
            if message['payload'].get('voltage'):
                voltage = round(message['payload']['voltage'], 3)
                response[station_name].update({"voltage": voltage})
            add_time(station_name, message['timestamp'])
        elif message['type'] == 'text' and station_name:
            text = message['payload']['text']
            position = []
            if "position" in response[station_name]:
                position = response[station_name]['position']
            print(f'{tst.ljust(15)}{station_name.ljust(16)}{"".ljust(45)}{text}')
            if 'points' not in response[station_name]:
                response[station_name]['points'] = {}
            add_time(station_name, message['timestamp'])
            neighbors = response[station_name]['neighbors'] if ('neighbors' in response[station_name]) else []
            response[station_name]['points'].update({iso: {"text": text, "position": position, "neighbors": neighbors}})
        elif message['type'] == 'neighborinfo' and station_name:
            response[station_name]['neighbors'] = message['payload']['neighbors']
            for remote in response[station_name]['neighbors']:
                remote['name'] = stations[remote['node_id']] if remote['node_id'] in stations else 'unknown'
        else:
            print(message)

if __name__ == "__main__":
    webServer = ThreadingHTTPServer((hostName, int(serverPortString)), MyServer)
    endstate = open(sys.argv[2] + '.json', 'w')
    merge_previous_days(sys.argv[1])
    drop_privileges(uid_name=new_uid_name)
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

    print(f'{"time".ljust(15)}{"name".ljust(16)}{"battery".ljust(15)}{"temperature".ljust(15)}{"humidity".ljust(15)}{"extra"}')
    for line in sys.stdin:
        if datetime.now().day != start_day:
            payload = json.dumps(response, indent = 4)
            endstate.write(payload)
            endstate.close()
            exit(0)
        main(line)
