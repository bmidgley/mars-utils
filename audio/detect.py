#!/usr/bin/env python3

import pyaudio
import wave
from array import array
import datetime
import sys
from pydub import AudioSegment

FORMAT=pyaudio.paInt16
CHANNELS=1
RATE=48000
CHUNK=1024
RECORD_SECONDS=15

def save_audio(frames):
    filename = f'/home/pi/audio/{datetime.datetime.now().isoformat()}.mp3'
    segment = AudioSegment(b''.join(frames), sample_width=2, frame_rate=48000, channels=1)
    segment.export(filename, format="mp3")
    print(f"encoded {filename}")

audio=pyaudio.PyAudio()

info = audio.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
input_index = -1

for i in range(0, numdevices):
    if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) == 1:
        input_index = i
        print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i))

if input_index == -1:
    print("no audio found")
    exit(1)

stream=audio.open(format=FORMAT,channels=CHANNELS,
                  rate=RATE,
                  input=True,
                  frames_per_buffer=CHUNK,
                  input_device_index=input_index)

threshold = int(sys.argv[1]) if len(sys.argv) == 2 else 1000

while True:
    frames = []
    heard = False

    while len(frames) == 0:
        for i in range(0,int(RATE/CHUNK*RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow = False)
            data_chunk = array('h', data)
            vol = max(data_chunk)
            if vol > threshold or heard:
                if not heard: print("heard")
                heard = True
                frames.append(data)

    save_audio(frames)

stream.stop_stream()
stream.close()
audio.terminate()

