# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Use PWM to fade an LED up and down using the potentiometer value as the duty cycle.

REQUIRED HARDWARE:
* potentiometer on pin GP26.
* LED on pin GP14.
"""
import time
from random import randint

import board
import digitalio
import pwmio

pir = digitalio.DigitalInOut(board.GP21)
pir.direction = digitalio.Direction.INPUT

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

red_led = pwmio.PWMOut(board.GP20, frequency=1000)
grn_led = pwmio.PWMOut(board.GP19, frequency=1000)
blu_led = pwmio.PWMOut(board.GP18, frequency=1000)

old_pir_value = pir.value
print(f"pir value: {pir.value}")
while True:
    #     red_led.duty_cycle = randint(0, 65535)
    #     grn_led.duty_cycle = randint(0, 65535)
    #     blu_led.duty_cycle = randint(0, 65535)

    pir_value = pir.value
    if pir_value:
        led.value = True
        if not old_pir_value:
            print("motion detected")
    else:
        led.value = False
        if old_pir_value:
            print("motion ended")
    old_pir_value = pir_value
#    time.sleep(0.5)
