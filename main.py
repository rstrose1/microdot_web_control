# full demo with web control panel
# combines multi core and multi tasking
import machine
from RequestParser import RequestParser
import uasyncio
from ResponseBuilder import ResponseBuilder
from WiFiConnection import WiFiConnection
from IoHandler import IoHandler
from detect_voltage_pico import VoltageSensor
from detect_pressure_pico import PressureSensor
from sys import path

from collections import deque as Queue
FLASK_TEMPLATE_DIR = "/templates/"
GAUGE_HTML_FILE = "gauge1.html"
GAUGE_WEB_PAGE = FLASK_TEMPLATE_DIR + GAUGE_HTML_FILE

# connect to WiFi
# this will block until connected
if not WiFiConnection.start_station_mode(True):
    raise RuntimeError('network connection failed')


async def handle_request(reader, writer):
    try:
        raw_request = await reader.read(2048)
        request = RequestParser(raw_request)
        response_builder = ResponseBuilder()

        # filter out api request
        if request.url_match("/api"):
            action = request.get_action()
            if action == 'get_pump_status':
                psi = IoHandler.get_pressure_reading()
                samples = []
                sampling_rate = 120  # Hz
                while (len(samples) < sampling_rate):
                    voltage = IoHandler.get_voltage_reading()
                    samples.append(voltage)
                    await uasyncio.sleep(0)

                average_voltage = sum(samples) / len(samples)

                if average_voltage < 2.6:
                    pump_on_off = "PUMP ON"
                else:
                    pump_on_off = "PUMP OFF"

                if psi < 20:
                    warning_str = "PUMP PRESSURE LOW!"
                elif psi > 80:
                    warning_str = "PUMP PRESSURE HIGH!"
                else:
                    warning_str = ''

                data = {
                    'pressure': psi,
                    'pump_on_off': pump_on_off,
                    'warning': warning_str
                }

                response_builder.set_body_from_dict(data)
            else:
                # unknown action
                response_builder.set_status(404)

        # try to serve static file
        else:
            response_builder.serve_static_file(request.url, "/templates/gauge1.html")

        response_builder.build_response()
        writer.write(response_builder.response)
        await writer.drain()
        await writer.wait_closed()

    except OSError as e:
        print('connection error ' + str(e.errno) + " " + str(e))

async def main():

    print('Setting up webserver...')
    server = uasyncio.start_server(handle_request, "0.0.0.0", 80)
    uasyncio.create_task(server)
    uasyncio.create_task(detect_voltage())
    uasyncio.create_task(detect_pressure())

    # just pulse the on board led for sanity check that the code is running
    while True:
        IoHandler.blink_onboard_led()
        await uasyncio.sleep(5)

async def detect_pressure():
    try:
        print('Starting pressure sensor')

        """ Monitor the output from the pressure sensor attached to the pump """
        """ Use the second channel on the ADC chip """

        MCP3008_CHAN = 1
        voltage_ref = 3.3
        max_psi = 80
        min_psi = 20
        pressure = PressureSensor(min_psi, max_psi, MCP3008_CHAN, voltage_ref)
        await pressure.monitor_pressure_sensor()

    except KeyboardInterrupt:
        print("\nExiting the program..")
        pass

    except:
        print("Some error/exception occurred")

#
async def detect_voltage():
    ADC_CHANNEL = 0
    voltage_q = "placeHolder"
    threshold_volt_ref = 2.6
    sampling_rate = 120  # Hz
    timeout = 2200

    print("Setting up MCP3008 ADC for voltage sensor..")
    try:
        vs = machine.ADC(ADC_CHANNEL)
        mv = VoltageSensor(ADC_CHANNEL, vs, voltage_q, threshold_volt_ref, sampling_rate)

        print("Start the voltage sensor monitoring")
        await mv.monitor_voltage_sensor(timeout)

    except KeyboardInterrupt:
        pass

    except:
        print("Some error/exception occurred")

try:
    # start asyncio tasks on first core
    uasyncio.run(main())
finally:
    print("running finally block")
    uasyncio.new_event_loop()
