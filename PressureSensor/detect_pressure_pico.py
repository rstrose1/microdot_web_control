import machine
import utime
import time
from time import sleep
import sys
import uasyncio
import _thread
from PressureSensor.pressure_setting import PressureSetting
from collections import deque
conversion_factor = 3.3 / (65535)
from machine import Pin

exitFlag = 0
PUMP_ON_FLAG = 1


class PressureSensor(object):
    def __init__(self, min_psi, max_psi, channel=1, voltage_ref=0.0, notify_deque=None):

        self.channel = channel
        self.channel_id = 1
        self.vRef = voltage_ref
        self.min_psi = min_psi
        self.max_psi = max_psi
        self.ADC_pressure = machine.ADC(channel)
        # Set up the spinner
        self.spinner = "|/-\\"
        self.spinner_index = 0
        self.send_email_flag = False

    def get_pump_pressure(self):
        adc_value = self.ADC_pressure.read_u16()
        voltage = adc_value * conversion_factor
        psi = round(((voltage * 95.48) - 34.81), 2)

        ##print(f"ADC value:{adc_value:.2f} Voltage:{voltage:.2f} Pressure:{psi:.2f} {self.spinner[self.spinner_index]} ")
        #print("\33[2A")
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner)

        return psi

    def modify_pressure_settings_file(self, filename, original, replacement):
        """Modify the content of a file by replacing original string with replacement string."""

        if not filename:
            print("Filename is empty, cannot modify file.")
            return

        if not original or not replacement:
            print("Original or replacement string is empty, cannot modify file.")
            return

        try:
            with open(filename, "r") as f:
                file_content = f.read()
            #Modify the content
            updated_content = file_content.replace(original, replacement)
            with open(filename, "w") as f:
                f.write(updated_content)
            f.close()

        except Exception as e:
            print(f"Error updating file: {filename}: {e}")

    def update_pressure_settings(self, filename, p_settings):
        max_psi_value = p_settings['max_psi']
        min_psi_value = p_settings['min_psi']

        # Save to file
        # Cant figure out a way as yet to update elements in file all at once
        # so will do one by one for now.
        # some how f.writelines doesn't appear to be woring in micropython --need to investigate further
        original_str = "max_psi = ''"
        replacement_str = f"max_psi = '{max_psi_value}'"
        self.modify_pressure_settings_file(filename, original_str, replacement_str)

        original_str = "min_psi = ''"
        replacement_str = f"min_psi = '{min_psi_value}'"
        self.modify_pressure_settings_file(filename, original_str, replacement_str)


    async def monitor_pressure_sensor(self):
        while True:
            if PUMP_ON_FLAG:
                pump_pressure = self.get_pump_pressure()

                if pump_pressure <= self.min_psi:
                    """ Pump pressure is too low! send alarm! """

                    #print("PUMP PRESSURE IS TOO LOW!")

                if pump_pressure >= self.max_psi:
                    """ Pump pressure is too high! send alarm! """
                    #print("PUMP PRESSURE IS TOO HIGH!")

                await uasyncio.sleep(2)
            else:
                await uasyncio.sleep(10)

async def detect_pressure(max_psi=80, min_psi=20):

    try:
        print('Starting pressure sensor')

        """ Monitor the output from the pressure sensor attached to the pump """
        """ Use the second channel on the ADC chip """

        MCP3008_CHAN = 1
        voltage_ref = 3.3
        pressure = PressureSensor(min_psi, max_psi, MCP3008_CHAN, voltage_ref)
        await pressure.monitor_pressure_sensor()

    except KeyboardInterrupt:
        print("\nExiting the program..")
        pass
    except:
        print("Some error/exception occurred")


# Main function
async def main():
   max_psi = 80
   min_psi = 20
   await detect_pressure(max_psi, min_psi)


if __name__ == '__main__':
    try:
        # start asyncio tasks on first core
        uasyncio.run(main())
    finally:
        print("running finally block")
        uasyncio.new_event_loop()


