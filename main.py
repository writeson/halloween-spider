# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Use PWM to fade an LED up and down using the potentiometer value as the duty cycle.

REQUIRED HARDWARE:
* potentiometer on pin GP26.
* LED on pin GP14.
"""

try:
    import uasyncio as asyncio
except:
    import asyncio


class TaskBase:
    def __init__(self):
        self._pause_event = asyncio.Event()

    @property
    def pause_event(self):
        return self._pause_event


class LedTask(TaskBase):

    async def run(self):
        while True:
            await self._pause_event.wait()
            print("Led task ran")
            self._pause_event.clear()


class SpeakerTask(TaskBase):

    async def run(self):
        while True:
            await self._pause_event.wait()
            print("Speaker task ran")
            self._pause_event.clear()


class Controller:
    def __init__(self):
        self._tasks = []

    def add_task(self, task: TaskBase):
        self._tasks.append(task)

    async def run(self):
        while True:
            print("print running controller")
            await asyncio.sleep(1)
            for task in self._tasks:
                task.pause_event.set()
            print("done running tasks")


async def main():
    led_task = LedTask()
    speaker_task = SpeakerTask()
    controller_task = Controller()
    controller_task.add_task(led_task)
    controller_task.add_task(speaker_task)

    await asyncio.gather(
        asyncio.create_task(led_task.run()),
        asyncio.create_task(speaker_task.run()),
        asyncio.create_task(controller_task.run())
    )



if __name__ == "__main__":
    asyncio.run(main())


