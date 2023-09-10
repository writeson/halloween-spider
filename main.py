# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Use PWM to fade an LED up and down using the potentiometer value as the duty cycle.

REQUIRED HARDWARE:
* potentiometer on pin GP26.
* LED on pin GP14.
"""

from random import randint, choice

import board
import digitalio
import asyncio
import time
import pwmio
import adafruit_rgbled
import audiomp3
import audiobusio
from adafruit_motor import motor


class TaskBase:
    def __init__(self, name):
        self._name = name
        self._pause_event = asyncio.Event()

    @property
    def pause_event(self):
        return self._pause_event

    @property
    def name(self):
        return self._name


class LedTask(TaskBase):
    def __init__(self, name):
        super().__init__(name)
        self._led = adafruit_rgbled.RGBLED(
            board.GP20, board.GP19, board.GP18
        )

    async def run(self):
        while True:
            await self._pause_event.wait()
            print("Led task running")
            for _ in range(20):
                self._led.color = (randint(0, 255), randint(0, 255), randint(0, 255))
                await asyncio.sleep(0.5)
            self._led.color = (255, 0, 0)
            await asyncio.sleep(1.0)
            self._led.color = (0, 0, 0)
            self._pause_event.clear()
            print("Led task ran")


class SpeakerTask(TaskBase):
    def __init__(self, name):
        super().__init__(name)
        self._audio = audiobusio.I2SOut(board.GP11, board.GP12, board.GP13)
        self._sounds = [
            "sounds/spider_one.mp3",
            "sounds/spider_two.mp3",
            "sounds/spider_three.mp3",
            "sounds/spider_four.mp3",
        ]

    async def run(self):
        while True:
            await self._pause_event.wait()
            print("Speaker task running")
            sound = choice(self._sounds)
            mp3 = audiomp3.MP3Decoder(open(sound, "rb"))
            self._audio.play(mp3)
            self._pause_event.clear()
            print("Speaker task ran")


class MotorTask(TaskBase):
    def __init__(self, name):
        super().__init__(name)
        self._pwm_freq = 25
        self._decay_mode = motor.SLOW_DECAY
        self._throttle_hold = 1

        self._pwm_a = pwmio.PWMOut(board.GP14, frequency=self._pwm_freq)
        self._pwm_b = pwmio.PWMOut(board.GP15, frequency=self._pwm_freq)
        self._motor = motor.DCMotor(self._pwm_a, self._pwm_b)
        self._motor.decay_mode = self._decay_mode
        self._motor.throttle = 0

    async def run(self):
        while True:
            await self._pause_event.wait()
            print("Motor task running")
            for duty_cycle in range(16, 100, 4):
                throttle = duty_cycle / 100
                self._motor.throttle = throttle
                await asyncio.sleep(0.3)
            for duty_cycle in range(100, 16, -4):
                throttle = duty_cycle / 100
                self._motor.throttle = throttle
                await asyncio.sleep(0.3)
            self._motor.throttle = 0
            self._pause_event.clear()
            print("Motor task ran")


class Pir:
    def __init__(self):
        self._tasks = {}
        self._pir = digitalio.DigitalInOut(board.GP21)
        self._pir.direction = digitalio.Direction.INPUT

    def add_task(self, task: TaskBase):
        self._tasks[task.name] = task

    async def run(self):
        old_value = self._pir.value
        while True:
            pir_value = self._pir.value
            if pir_value:
                # is movement detected?
                if not old_value:

                    # always start with flashing the eyes
                    led_task = self._tasks.get("led")
                    led_task.pause_event.set()

                    await asyncio.sleep(randint(1, 2))

                    # run the sound first and then the motor after a delay
                    speaker_task = self._tasks.get("speaker")
                    speaker_task.pause_event.set()
                    await asyncio.sleep(3, 4)
                    motor_task = self._tasks.get("motor")
                    motor_task.pause_event.set()

            old_value = pir_value
            await asyncio.sleep(0.2)


async def main():
    led_task = LedTask("led")
    speaker_task = SpeakerTask("speaker")
    motor_task = MotorTask("motor")
    pir_task = Pir()
    pir_task.add_task(led_task)
    pir_task.add_task(speaker_task)
    pir_task.add_task(motor_task)

    await asyncio.gather(
        asyncio.create_task(led_task.run()),
        asyncio.create_task(speaker_task.run()),
        asyncio.create_task(motor_task.run()),
        asyncio.create_task(pir_task.run())
    )


if __name__ == "__main__":
    asyncio.run(main())


