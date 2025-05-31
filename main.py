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
import umail
import time
from machine import Pin
import bluetooth
from bluetooth_peripheral import BLESimplePeripheral


from collections import deque as Queue
FLASK_TEMPLATE_DIR = "/templates/"
GAUGE_HTML_FILE = "gauge1.html"
GAUGE_WEB_PAGE = FLASK_TEMPLATE_DIR + GAUGE_HTML_FILE
WEB_LINK = "http://192.168.1.10/"

# Email details
"""
sender_email = "rstrose1@yahoo.com"
sender_name = 'Raspberry Pi Pico'
sender_app_password = ''
recipient_email ="takeella@gmail.com"
"""

sender_email = "takeella@gmail.com"
sender_name = 'Raspberry Pi Pico'
sender_app_password = ''
recipient_email = "rstrose1@yahoo.com"
email_flag = False
# Initialize the LED state to 0 (off)
led_state = 0
# Create a Pin object for the onboard LED, configure it as an output
led = Pin("LED", Pin.OUT)

ssid = ''
pwd = ''


email_subject ='Hello from RPi Pico W'

def prepare_email(msg):
    """
    Prepare the body of the email based on the pump status.
    """
    body = msg

    return body

def send_email(body):
# Send the email

    smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True) # Gmail's SSL port

    try:
        smtp.login(sender_email, sender_app_password)
        smtp.to(recipient_email)
        smtp.write("From:" + sender_name + "<"+ sender_email+">\n")
        smtp.write("Subject:" + email_subject + "\n")
        smtp.write(body)

        smtp.send()
        print("Email Sent Successfully")

    except Exception as e:
        print("Failed to send email:", e)
    finally:
        smtp.quit()

async def handle_request(reader, writer):
    try:
        raw_request = await reader.read(2048)
        request = RequestParser(raw_request)
        response_builder = ResponseBuilder()

        # filter out api request
        if request.url_match("/api"):
            action = request.get_action()
            if action == 'get_another_page':
                print("Hear we are from the About.html page!")
            elif action == 'get_pump_status':
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
                    global email_flag
                    if email_flag == False:
                        body = prepare_email(warning_str)
                        #send_email(body)
                        email_flag = True

                elif psi > 80:
                    warning_str = "PUMP PRESSURE HIGH!"
                    global email_flag
                    if email_flag == False:
                        body = prepare_email(warning_str)
                        #send_email(body)
                        email_flag = True
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


def extract_data_from_ble(data):
    data_list = data.split()
    return data_list[1].decode('utf-8')

# Define a callback function to handle received data
def on_rx(data):
    print("Data received: ", data)  # Print the received data
    global led_state  # Access the global variable led_state
    global ssid
    global pwd
    # get wifi SSID over bluetooth connection
    if 'ssid' in data:
        led.value(not led_state)  # Toggle the LED state (on/off)
        led_state = 1 - led_state  # Update the LED state
        ssid = extract_data_from_ble(data)
        print(ssid)

    # get wifi password over bluetooth connection
    elif 'pwd' or 'password' in data:
        led.value(not led_state)  # Toggle the LED state (on/off)
        led_state = 1 - led_state  # Update the LED state
        pwd = extract_data_from_ble(data)
        print(pwd)

    else:
        print("unknown data")


async def start_bluetooth():
    print("Starting bluetooth...")
    # Create a Bluetooth Low Energy (BLE) object
    ble = bluetooth.BLE()

    # Create an instance of the BLESimplePeripheral class with the BLE object
    sp = BLESimplePeripheral(ble)

    # Start an infinite loop
    while True:
        if sp.is_connected():  # Check if a BLE connection is established
            sp.on_write(on_rx)  # Set the callback function for data reception

        await uasyncio.sleep(0)


async def main():

    # connect to bluetooth
    print("Starting BlueTooth")
    uasyncio.create_task(start_bluetooth())

    print("Starting WiFi")
    wifi = WiFiConnection()
    while True:
        if not wifi.start_station_mode(True):
            if ssid is not '' and pwd is not '':
                print("Updating wifi credentials from BLE...")
                wifi.update_credentials(ssid, pwd)
        else:
            break

        await uasyncio.sleep(0)
        #raise RuntimeError('network connection failed')

    print('Setting up webserver...')
    server = uasyncio.start_server(handle_request, "0.0.0.0", 80)
    uasyncio.create_task(server)
    uasyncio.create_task(detect_voltage())
    uasyncio.create_task(detect_pressure())



    # just pulse the on board led for sanity check that the code is running
    while True:
        IoHandler.blink_onboard_led()
        await uasyncio.sleep(5)

try:
    # start asyncio tasks on first core
    uasyncio.run(main())
finally:
    print("running finally block")
    uasyncio.new_event_loop()
