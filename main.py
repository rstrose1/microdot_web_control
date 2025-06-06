# full demo with web control panel
# combines multi core and multi tasking
import sys
import os
import machine
from RequestParser import RequestParser
import uasyncio
from ResponseBuilder import ResponseBuilder
from Wifi.WiFiConnection import WiFiConnection
from IoHandler import IoHandler
from detect_voltage_pico import VoltageSensor
from detect_pressure_pico import PressureSensor
from sys import path
import Email.umail as umail
import time
from machine import Pin
import bluetooth
from Bluetooth.bluetooth_peripheral import BLESimplePeripheral
from ucollections import deque

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
ip_flag = False
psi_flag = False
volt_flag = False
email = ''
send_bluetooth_flag = False
email_subject ='Hello from RPi Pico W'

def prepare_email(msg):
    """
    Prepare the body of the email based on the pump status.
    """
    body = msg

    return body

def send_email(body):
    """
    Sends an email using the provided body content.

    Args:
        body (str): The content of the email to be sent.
    """
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

async def get_voltage_reading():
    samples = []
    sampling_rate = 120  # Hz
    while (len(samples) < sampling_rate):
        voltage = IoHandler.get_voltage_reading()
        samples.append(voltage)
        await uasyncio.sleep(0)

    return sum(samples) / len(samples)

async def handle_request(reader, writer):
    """
    Handles incoming HTTP requests, parses them, and sends appropriate responses.

    Args:
        reader (StreamReader): The input stream to read the request data.
        writer (StreamWriter): The output stream to send the response data.
    """
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
                average_voltage = await get_voltage_reading()
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

async def detect_pressure(ble_deque, notify_deque):
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


async def detect_voltage(ble_deque, notify_deque):
    """
    Monitors the voltage sensor using the MCP3008 ADC and updates a message deque with status messages.

    Args:
        msg_deque (collections.deque): A deque to store status messages for Bluetooth communication.
    """
    ADC_CHANNEL = 0
    voltage_q = "placeHolder"
    threshold_volt_ref = 2.6
    sampling_rate = 120  # Hz

    str = "Setting up MCP3008 ADC for voltage sensor..\n"
    ble_deque.append(str)

    try:
        vs = machine.ADC(ADC_CHANNEL)
        mv = VoltageSensor(ADC_CHANNEL, vs, notify_deque, threshold_volt_ref, sampling_rate)

        str = "Start the voltage sensor monitoring \n"
        ble_deque.append(str)
        await mv.monitor_voltage_sensor()

    except KeyboardInterrupt:
        pass

    except:
        print("Some error/exception occurred")


def extract_data_from_ble(data):
    """ Extracts specific data from a byte string received over Bluetooth."""
    print(len(data))
    data_list = data.split()
    print(data_list)

    return data_list[1].decode('utf-8')


def on_rx(data):
    """
    Callback function to handle data received via Bluetooth.

    Args:
        data (bytes): The data received from the Bluetooth connection.
    """
    print("Pico Data received: ", data)  # Print the received data
    global led_state  # Access the global variable led_state
    global ssid
    global pwd
    global ip_flag
    global email
    global psi_flag
    global volt_flag
    # get wifi SSID over bluetooth connection
    if 'ip' in data:
        ip_flag = True

    elif 'psi' in data:
        psi_flag = True

    elif 'volt' in data:
        volt_flag = True

    elif 'ssid' in data:
#        led.value(not led_state)  # Toggle the LED state (on/off)
#       led_state = 1 - led_state  # Update the LED state
        ssid = extract_data_from_ble(data)
        print(ssid)

    elif 'email' in data:
        email = extract_data_from_ble(data)
        print(email)

    # get wifi password over bluetooth connection
    elif 'pwd' in data:
#        led.value(not led_state)  # Toggle the LED state (on/off)
#        led_state = 1 - led_state  # Update the LED state
        pwd = extract_data_from_ble(data)
        print(pwd)

    elif 'password' in data:
#        led.value(not led_state)  # Toggle the LED state (on/off)
#        led_state = 1 - led_state  # Update the LED state
        pwd = extract_data_from_ble(data)
        print(pwd)

    else:
        print("unknown data\n")

    return

async def notifications(ble_deque, notify_deque):
    """ Start an infinite loop to check the message deque """
    global psi_flag
    global volt_flag

    while True:

        if len(notify_deque) > 0:
            get_notify_msg = notify_deque.popleft()
            if get_notify_msg is not None:
                print(get_notify_msg)
                #need to handle cases for turning on external led and/or buzzer

        # the following flags are set in the on_rx callback function
        # and are used to determine if the pressure or voltage sensor readings
        # should be sent to the bluetooth device
        if psi_flag == True:
            psi = IoHandler.get_pressure_reading()
            str = f"Pump pressure: {psi:.1f} PSI\n"
            ble_deque.append(str)
            psi_flag = False

        if volt_flag == True:
            average_voltage = await get_voltage_reading()
            if average_voltage < 2.6:
                status = "pump is ON"
            else:
                status = "pump is OFF"
            str = f"Voltage sensor: {average_voltage:.2f} V - {status} \n"
            ble_deque.append(str)
            volt_flag = False

        await uasyncio.sleep(0)


async def start_bluetooth(ble_deque):
    """
    Initializes and manages the Bluetooth Low Energy (BLE) connection.
    Sends messages from a deque to connected BLE devices and processes received data.
    """
    print("Starting bluetooth...")
    # Create a Bluetooth Low Energy (BLE) object
    ble = bluetooth.BLE()

    # Create an instance of the BLESimplePeripheral class with the BLE object
    sp = BLESimplePeripheral(ble)

    # Start an infinite loop to send ble messages to user
    while True:
        if sp.is_connected():  # Check if a BLE connection is established
            sp.on_write(on_rx)  # Set the callback function for data reception
            try:
                if len(ble_deque) > 0:
                    snd_msg = ble_deque.popleft()
                    sp.send(snd_msg)
            except Exception:
                pass

        await uasyncio.sleep(0)


async def main():
    """Main function to initialize the system, set up WiFi, Bluetooth, and start the web server."""
    ble_msg = []
    notify_msg = []
    max_ble_msg = 20
    max_notify_msg = 20
    ble_deque = deque(ble_msg, max_ble_msg)
    notify_deque = deque(notify_msg, max_notify_msg)
    global ip_flag
    global send_bluetooth_flag
    global ssid
    global pwd

    print("Starting BlueTooth")
    uasyncio.create_task(start_bluetooth(ble_deque))

    print("Starting WiFi")
    wifi = WiFiConnection()
    while True:
        if not wifi.start_station_mode(True):

            if send_bluetooth_flag == False:
                str = "Enter your wifi credentials now\n"
                ble_deque.append(str)
                send_bluetooth_flag = True
                await uasyncio.sleep(0)

            # ssid and pwd obtained via bluetooth communication from user
            if ssid is not '' and pwd is not '':
                str = "Updating wifi credentials from BLE...\n"
                print(str)
                credentials = {"ssid": ssid, "password": pwd }
                wifi.update_credentials("Wifi/NetworkCredentials.py", credentials)
                try:
                    ble_deque.append(str)
                except Exception:
                    pass

        else:
            break

        await uasyncio.sleep(0)
        #raise RuntimeError('network connection failed')

    msg_str = 'Setting up webserver...'
    ble_deque.append(msg_str)

    server = uasyncio.start_server(handle_request, "0.0.0.0", 80)
    uasyncio.create_task(server)
    uasyncio.create_task(detect_voltage(ble_deque, notify_deque))
    uasyncio.create_task(detect_pressure(ble_deque, notify_deque))
    uasyncio.create_task(notifications(ble_deque, notify_deque))

    # just pulse the on board led for sanity check that the code is running
    while True:

        if ip_flag == True:
            print(f"Ip Address: {wifi.ip}")
            str = f"IP Address: http://{wifi.ip}\n"
            ble_deque.append(str)
            ip_flag = False

        IoHandler.blink_onboard_led()
        await uasyncio.sleep(5)

try:
    # start asyncio tasks on first core
    uasyncio.run(main())
finally:
    print("running finally block")
    uasyncio.new_event_loop()
