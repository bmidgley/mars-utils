#!/usr/bin/env python3

import pyaudio
import wave
from array import array
import datetime
import sys

FORMAT=pyaudio.paInt16
CHANNELS=1
RATE=48000
CHUNK=1024
RECORD_SECONDS=15

def save_audio(frames):
    filename = f'{datetime.datetime.now().isoformat()}-{sys.argv[1]}.wav'
    wavfile=wave.open(filename, 'wb')
    wavfile.setnchannels(CHANNELS)
    wavfile.setsampwidth(audio.get_sample_size(FORMAT))
    wavfile.setframerate(RATE)
    wavfile.writeframes(b''.join(frames))#append frames recorded to file
    wavfile.close()
    print(f'wrote {filename} with {len(frames)} frames')

audio=pyaudio.PyAudio()
stream=audio.open(format=FORMAT,channels=CHANNELS,
                  rate=RATE,
                  input=True,
                  frames_per_buffer=CHUNK,
                  input_device_index=1)

while True:
    frames = []
    heard = False

    while len(frames) == 0:
        for i in range(0,int(RATE/CHUNK*RECORD_SECONDS)):
            data=stream.read(CHUNK, exception_on_overflow = False)
            data_chunk=array('h',data)
            vol=max(data_chunk)
            if vol > int(sys.argv[1]) or heard:
                if not heard: print("heard")
                heard = True
                frames.append(data)

    save_audio(frames)

stream.stop_stream()
stream.close()
audio.terminate()

