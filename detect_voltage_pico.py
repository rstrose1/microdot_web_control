import machine
import utime
import time
from time import sleep
import sys
from collections import deque
conversion_factor = 3.3 / (65535)
from machine import Pin
import uasyncio
import _thread



class VoltageSensor(object):
    def __init__(self, channel, ADC, out_q=None, threshold_volt_ref=2.8, sampling_rate=120):
        self.channel = channel
        self.ADC = ADC
        self.out_q = out_q
        self.pump_on_off_status = "UNKNOWN"
        self.threshold_volt_ref = threshold_volt_ref
        self.samples = []
        self.sampling_rate = sampling_rate  # Hz
        self.sampling_period = round(1.0 / self.sampling_rate, 4)

    def get_pump_on_off_status(self):
        return self.pump_on_off_status

    async def monitor_voltage_sensor(self,  timeout=10):
        # Set up the spinner
        spinner = "|/-\\"
        spinner_index = 0

        self.samples.clear()

        led = machine.Pin("LED", machine.Pin.OUT)

        end_time = time.time() + timeout
        while True:

            #print("Reading ADC...")
            voltage = self.ADC.read_u16() * conversion_factor

            # Add the voltage to a list for sampling
            self.samples.append(voltage)

            # Calculate the average voltage from the sample readings
            if (len(self.samples) >= self.sampling_rate):
                voltage = sum(self.samples) / len(self.samples)
                max_value = max(self.samples)
                min_value = min(self.samples)
                if voltage < self.threshold_volt_ref:
                    msg = "ON  "
                    led.on()  # Turn LED on (set pin high)
                else:
                    msg = "OFF "
                    led.off()  # Turn LED off (set pin low)

                #print(f"Voltage:{voltage:.2f} Max:{max_value:.2f} Min:{min_value:.2f} PUMP {msg} {spinner[spinner_index]} ")
                #print("\33[2A")
                self.samples.clear()
                spinner_index = (spinner_index + 1) % len(spinner)
                if self.pump_on_off_status != msg:
                    self.pump_on_off_status = msg
                    """
                    try:
                        self.out_q.put_nowait(self.pump_on_off_status)
                    except Full:
                        pass
                    except Empty:
                        pass
                    """

            await uasyncio.sleep(0)  # Sleep for a short time to allow other tasks to run

async def detect_voltage(threshold_volt_ref, sampling_rate, timeout):
    ADC_CHANNEL = 0
   # voltage_q = deque()
    voltage_q = "placeHolder"

    print("Setting up MCP3008 ADC for voltage sensor..")
    try:
        vs = machine.ADC(ADC_CHANNEL)

        mv = VoltageSensor(ADC_CHANNEL, vs, voltage_q, threshold_volt_ref, sampling_rate)
        print("Start the voltage sensor monitoring")

        await mv.monitor_voltage_sensor(timeout)

        # Wait for a keyboard input to exit
    except KeyboardInterrupt:
        pass

    except:
        print("Some error/exception occurred")


# Main function
async def main():

    threshold_volt_ref = 2.6
    sampling_rate = 120  # Hz
    timeout = 2200


    print(f"Using threshold voltage reference of {threshold_volt_ref}V.")
    print(f"Using sampling rate of {sampling_rate}Hz.")
    print("Starting voltage sensor monitoring...")
    print("Press Ctrl+C to exit")
    await detect_voltage(threshold_volt_ref, sampling_rate, timeout)
    print("Exiting voltage sensor monitoring...")
    print("Goodbye!")

if __name__ == '__main__':
    try:
        # start asyncio tasks on first core
        uasyncio.run(main())
    finally:
        print("running finally block")
        uasyncio.new_event_loop()