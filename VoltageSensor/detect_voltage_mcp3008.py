"""
MicroPython Library for MCP3008 8-channel ADC with SPI

Datasheet for the MCP3008: https://www.microchip.com/datasheet/MCP3008

This code makes much use of Adafruit's CircuitPython code at
https://github.com/adafruit/Adafruit_CircuitPython_MCP3xxx
adapted for MicroPython.

Tested on the Raspberry Pi Pico.

Thanks, @Raspberry_Pi and @Adafruit, for all you've given us!
"""

from machine import Pin, SPI
from time import sleep, sleep_ms
import uasyncio




class MCP3008:

    def __init__(self, spi, cs, ref_voltage=3.3, sampling_rate=120):
        """
        Create MCP3008 instance

        Args:
            spi: configured SPI bus
            cs:  pin to use for chip select
            ref_voltage: r
        """
        self.cs = cs
        self.cs.value(1) # ncs on
        self._spi = spi
        self._out_buf = bytearray(3)
        self._out_buf[0] = 0x01
        self._in_buf = bytearray(3)
        self._ref_voltage = ref_voltage
        self.samples = []
        self.sampling_rate = sampling_rate  # Hz
        self.sampling_period = round(1.0 / self.sampling_rate, 4)

    def reference_voltage(self) -> float:
        """Returns the MCP3xxx's reference voltage as a float."""
        return self._ref_voltage

    def read(self, pin, is_differential=False):
        """
        read a voltage or voltage difference using the MCP3008.

        Args:
            pin: the pin to use
            is_differential: if true, return the potential difference between two pins,


        Returns:
            voltage in range [0, 1023] where 1023 = VREF (3V3)

        """

        self.cs.value(0) # select
        self._out_buf[1] = ((not is_differential) << 7) | (pin << 4)
        self._spi.write_readinto(self._out_buf, self._in_buf)
        self.cs.value(1) # turn off
        return ((self._in_buf[1] & 0x03) << 8) | self._in_buf[2]


async def detect_voltage(threshold_volt_ref, sampling_rate):
    spi = SPI(0, sck=Pin(2),mosi=Pin(3),miso=Pin(4), baudrate=100000)
    cs = Pin(22, Pin.OUT)
    #cs = Pin(17, Pin.OUT)
    cs.value(1) # disable chip at start

    square = Pin(21, Pin.OUT)

    chip = MCP3008(spi, cs)

    chip.samples.clear()

    spinner = "|/-\\"
    spinner_index = 0

    while True:
        #square.value(1)
        #square.on()
        actual = chip.read(0)
        # Add the voltage to a list for sampling
        chip.samples.append(actual)

    # Calculate the average voltage from the sample readings
        if (len(chip.samples) >= chip.sampling_rate):
            voltage = sum(chip.samples) / len(chip.samples)
            max_value = max(chip.samples)
            min_value = min(chip.samples)

            print(f"Actual:{voltage} Max:{max_value} Min:{min_value}  {spinner[spinner_index]} ")
            print("\33[2A")

            chip.samples.clear()
        #print(actual)
        #sleep(.25)
        #square.value(0)
        #square.off()
        #actual = chip.read(0)
        #print(actual)
        #sleep(.25)

        await uasyncio.sleep(0)  # Sleep for a short time to allow other tasks to run


async def main():

    threshold_volt_ref = 3.3
    sampling_rate = 120  # Hz

    print(f"Using threshold voltage reference of {threshold_volt_ref}V.")
    print(f"Using sampling rate of {sampling_rate}Hz.")
    print("Starting voltage sensor monitoring...")
    print("Press Ctrl+C to exit")
    await detect_voltage(threshold_volt_ref, sampling_rate)
    print("Exiting voltage sensor monitoring...")
    print("Goodbye!")

if __name__ == '__main__':
    try:
        # start asyncio tasks on first core
        uasyncio.run(main())
    finally:
        print("running finally block")
        uasyncio.new_event_loop()


