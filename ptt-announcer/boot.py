# install as boot.py on micropython device so it's run on boot
# monitors the analog input to see when the ptt button is pressed

import uos, machine
import gc
gc.collect()

from machine import Pin, ADC
from time import sleep

led = machine.Pin(2, Pin.OUT)
ptt = machine.ADC(0)

led(1)

transmitting = False

while True:
    ptt_value = ptt.read()
    if ptt_value < 30:
        if not transmitting:
            transmitting = True
            led(0)
            print("-talking")
    else:
        if transmitting:
            transmitting = False
            led(1)
            print("+talking")
      
    sleep(0.2)
