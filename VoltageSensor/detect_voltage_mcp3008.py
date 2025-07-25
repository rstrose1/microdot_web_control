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
        self.avg_actual_value = [0, 0, 0, 0, 0, 0, 0, 0]  # average actual value for each channel
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

    def get_adc_reading(self, zone=1):
        """Returns the MCP3xxx's actual value."""

        #print(f"avg actual val:{self.avg_actual_value}")
        if not self.avg_actual_value:
            return None

        return self.avg_actual_value[zone - 1]

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

    async def monitor_voltage_sensor(self, debug=False):
        """
        Monitor the voltage sensor and print the readings.
        This method will run indefinitely until stopped.
        """
        spinner = "|/-\\"
        spinner_index = 0

        self.samples.clear()

        lowest_avg_value=[0, 0, 0, 0, 0, 0, 0, 0]
        highest_avg_value = [0, 0, 0, 0, 0, 0, 0, 0]

        state_threshold = 175 # threshold for state change, adjust as needed

        state = "OFF"  # initial state
        state_rec = "OFF"  # record the last state to detect changes

        while True:
            for i in range(2):  # MCP3008 has 8 channels
                while len(self.samples) < self.sampling_rate:
                    actual = self.read(i)

                    # Add the voltage to a list for sampling
                    self.samples.append(actual)

                    await uasyncio.sleep(0)

                    # Calculate the average voltage from the sample readings

                self.avg_actual_value[i] = int(sum(self.samples) / len(self.samples))
                max_value = max(self.samples)
                min_value = min(self.samples)
                if debug:

                    if self.avg_actual_value[i] < state_threshold and self.avg_actual_value[i] > 100:
                        state = "ON"
                    else:
                        state = "OFF"

                    if state_rec is not state:
                        state_rec = state
                        # reset the lowest and highest values
                        highest_avg_value[i] = 0
                        lowest_avg_value[i] = 0

                    if lowest_avg_value[i] == 0 or self.avg_actual_value[i] < lowest_avg_value[i]:
                        lowest_avg_value[i] = self.avg_actual_value[i]
                    if highest_avg_value[i] == 0 or self.avg_actual_value[i] > highest_avg_value[i]:
                        highest_avg_value[i] = self.avg_actual_value[i]

                    #print(f"Actual:{self.avg_actual_value} Max:{max_value} Min:{min_value} {spinner[spinner_index]} ")
                    print(f"Actual {i}:{self.avg_actual_value[i]} Lowest avg:{lowest_avg_value[i]} Highest avg:{highest_avg_value[i]} State: {state} {spinner[spinner_index]} ")
                    spinner_index = (spinner_index + 1) % len(spinner)
                    print("\33[2A")

                self.samples.clear()

            await uasyncio.sleep(.01)  # Sleep for a short time to allow other tasks to run


async def detect_voltage(threshold_volt_ref, sampling_rate):
    spi = SPI(0, sck=Pin(2),mosi=Pin(3),miso=Pin(4), baudrate=100000)
    cs = Pin(22, Pin.OUT)
    cs.value(1) # disable chip at start

    mcp3008 = MCP3008(spi, cs)
    debug = True

    try:
        await mcp3008.monitor_voltage_sensor(True)

    except KeyboardInterrupt:
        pass

    except:
        print("Some error/exception occurred")


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


