# Code obtained from: https://www.tomshardware.com/how-to/buzzer-music-raspberry-pi-pico
# Connect ground pin of buzzer to a GND pin on the Pico
# and the positive buzzer pin to a standard GPIO pin on the pico. Ex GP15
# Note: There is a difference between an active and passive piezo buzzer.
# Active will make noise if just hooked up to power. Passive will not.
# Passive are preferred for better range of sound, but both should work
# Some Passive buzzers may not have positive or negative labels so should work in
# any pin configuration.
import uasyncio
from machine import Pin, PWM
from utime import sleep

class Buzzer(object):
    def __init__(self):
        self.song = ["E5","G5","A5","P","E5","G5","B5","A5","P","E5","G5","A5","P","G5","E5"]

        self.tones = {
        "B0": 31,
        "C1": 33,
        "CS1": 35,
        "D1": 37,
        "DS1": 39,
        "E1": 41,
        "F1": 44,
        "FS1": 46,
        "G1": 49,
        "GS1": 52,
        "A1": 55,
        "AS1": 58,
        "B1": 62,
        "C2": 65,
        "CS2": 69,
        "D2": 73,
        "DS2": 78,
        "E2": 82,
        "F2": 87,
        "FS2": 93,
        "G2": 98,
        "GS2": 104,
        "A2": 110,
        "AS2": 117,
        "B2": 123,
        "C3": 131,
        "CS3": 139,
        "D3": 147,
        "DS3": 156,
        "E3": 165,
        "F3": 175,
        "FS3": 185,
        "G3": 196,
        "GS3": 208,
        "A3": 220,
        "AS3": 233,
        "B3": 247,
        "C4": 262,
        "CS4": 277,
        "D4": 294,
        "DS4": 311,
        "E4": 330,
        "F4": 349,
        "FS4": 370,
        "G4": 392,
        "GS4": 415,
        "A4": 440,
        "AS4": 466,
        "B4": 494,
        "C5": 523,
        "CS5": 554,
        "D5": 587,
        "DS5": 622,
        "E5": 659,
        "F5": 698,
        "FS5": 740,
        "G5": 784,
        "GS5": 831,
        "A5": 880,
        "AS5": 932,
        "B5": 988,
        "C6": 1047,
        "CS6": 1109,
        "D6": 1175,
        "DS6": 1245,
        "E6": 1319,
        "F6": 1397,
        "FS6": 1480,
        "G6": 1568,
        "GS6": 1661,
        "A6": 1760,
        "AS6": 1865,
        "B6": 1976,
        "C7": 2093,
        "CS7": 2217,
        "D7": 2349,
        "DS7": 2489,
        "E7": 2637,
        "F7": 2794,
        "FS7": 2960,
        "G7": 3136,
        "GS7": 3322,
        "A7": 3520,
        "AS7": 3729,
        "B7": 3951,
        "C8": 4186,
        "CS8": 4435,
        "D8": 4699,
        "DS8": 4978
        }

    def playsong(self, mysong, tones):
        for i in range(len(mysong)):
            if (mysong[i] == "P"):
                self.bequiet()
            else:
                self.playtone(tones[mysong[i]])
            sleep(0.3)
        self.bequiet()


    def playtone(self, frequency):
        buzzer = PWM(Pin(15))
        buzzer.duty_u16(1000)
        buzzer.freq(frequency)

    def bequiet(self):
        buzzer = PWM(Pin(15))
        buzzer.duty_u16(0)

    async def set_alarm(self, frequency):
        sound = PWM(Pin(15))
        sound.freq(frequency)
        for i in range(10):
            sound.duty_u16(1000)  # Set duty cycle to 1000 (out of 65535)
            await uasyncio.sleep(0.1)  # Wait for 100ms
            sound.duty_u16(0)  # Set duty cycle to 0
            await uasyncio.sleep(0.1)  # Wait for 100ms
            sound.duty_u16(1000)
        self.bequiet()


# Main function
"""
async def speaker():
    buzzer = Buzzer()

    #buzzer.playsong(buzzer.song, buzzer.tones)
    await buzzer.set_alarm(1000)  # Set alarm frequency to 1000Hz
    return
"""

#if __name__ == "__main__":
#    uasyncio.run(speaker())

