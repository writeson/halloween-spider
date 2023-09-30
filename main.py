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
import asyncio
import alarm
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
        self._clear_event = asyncio.Event()

    @property
    def pause_event(self):
        return self._pause_event

    @property
    def clear_event(self):
        return self._clear_event

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
            self._pause_event.clear()
            old_red, old_grn, old_blu = 0, 0, 0

            # home in on random color
            for i in range(20):
                new_red, new_grn, new_blu = (randint(0, 255), randint(0, 255), randint(0, 255))
                delta_red = (new_red - old_red) // 20
                delta_grn = (new_grn - old_grn) // 20
                delta_blu = (new_blu - old_blu) // 20
                for _ in range(20):
                    old_red, old_grn, old_blu = ((old_red + delta_red), (old_grn + delta_grn), (old_blu + delta_blu))
                    self._led.color = (old_red, old_grn, old_blu)
                    await asyncio.sleep(0.025)
                await asyncio.sleep(1)

            # home in on red
            new_red, new_grn, new_blu = (255, 0, 0)
            delta_red = (new_red - old_red) // 20
            delta_grn = (new_grn - old_grn) // 20
            delta_blu = (new_blu - old_blu) // 20
            for _ in range(20):
                old_red, old_grn, old_blu = ((old_red + delta_red), (old_grn + delta_grn), (old_blu + delta_blu))
                self._led.color = (old_red, old_grn, old_blu)
                await asyncio.sleep(0.025)
            await asyncio.sleep(1)
            self._led.color = (255, 0, 0)
            await asyncio.sleep(1.0)
            self._led.color = (0, 0, 0)
            self._clear_event.set()


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
            self._pause_event.clear()
            sound = choice(self._sounds)
            mp3 = audiomp3.MP3Decoder(open(sound, "rb"))
            self._audio.play(mp3)
            self._clear_event.set()


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
            self._pause_event.clear()
            for duty_cycle in range(16, 50, 4):
                throttle = duty_cycle / 100
                self._motor.throttle = throttle
                await asyncio.sleep(0.3)

            await asyncio.sleep(2.0)

            for duty_cycle in range(50, 16, -4):
                throttle = duty_cycle / 100
                self._motor.throttle = throttle
                await asyncio.sleep(0.3)
            self._motor.throttle = 0
            self._clear_event.set()


class Controller:
    def __init__(self):
        self._tasks = {}

    def add_task(self, task: TaskBase):
        self._tasks[task.name] = task

    async def run(self):
        # give things time to settle down
        await asyncio.sleep(5)
        while True:
            # always start with flashing the eyes
            led_task = self._tasks.get("led")
            led_task.pause_event.set()

            await asyncio.sleep(randint(1, 2))

            # run the sound first and then the motor after a delay
            speaker_task = self._tasks.get("speaker")
            speaker_task.pause_event.set()
            await asyncio.sleep(3)
            motor_task = self._tasks.get("motor")
            motor_task.pause_event.set()

            # wait for the other tasks to finish
            await asyncio.gather(
                led_task.clear_event.wait(),
                speaker_task.clear_event.wait(),
                motor_task.clear_event.wait(),
            )
            led_task.clear_event.clear()
            speaker_task.clear_event.clear()
            motor_task.clear_event.clear()

            # got to light sleep to save power
            interval_sleep = randint(60, 120)
            time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + interval_sleep)
            alarm.light_sleep_until_alarms(time_alarm)
            await asyncio.sleep(interval_sleep)


async def main():
    led_task = LedTask("led")
    speaker_task = SpeakerTask("speaker")
    motor_task = MotorTask("motor")
    controller = Controller()
    controller.add_task(led_task)
    controller.add_task(speaker_task)
    controller.add_task(motor_task)

    await asyncio.gather(
        asyncio.create_task(led_task.run()),
        asyncio.create_task(speaker_task.run()),
        asyncio.create_task(motor_task.run()),
        asyncio.create_task(controller.run())
    )


if __name__ == "__main__":
    asyncio.run(main())


