# full demo with web control panel
# combines multi core and multi tasking
# https://randomnerdtutorials.com/micropython-raspberry-pi-pico-asynchronous-programming/
import sys
import os
import machine
from WebServer.RequestParser import RequestParser
import uasyncio
from WebServer.ResponseBuilder import ResponseBuilder
from Wifi.WiFiConnection import WiFiConnection
from IoHandler import IoHandler
from VoltageSensor.detect_voltage_pico import VoltageSensor
from PressureSensor.detect_pressure_pico import PressureSensor
from Bluetooth.Bluetooth import Bluetooth
from sys import path
import Email.umail as umail
import time
from machine import Pin
import bluetooth
from Bluetooth.bluetooth_peripheral import BLESimplePeripheral
from ucollections import deque

FLASK_TEMPLATE_DIR = "/WebServer/templates/"
GAUGE_HTML_FILE = "gauge1.html"
GAUGE_WEB_PAGE = FLASK_TEMPLATE_DIR + GAUGE_HTML_FILE
WEB_LINK = "http://192.168.1.8/"

# Email details
"""
sender_email = "rstrose1@yahoo.com"
sender_name = 'Raspberry Pi Pico'
sender_app_password = ''
recipient_email ="takeella@gmail.com"
"""

sender_email = "takeella@gmail.com"
sender_name = 'Raspberry Pi Pico'
sender_app_password = 'dlvk fxtg mdbr hngv'
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
            response_builder.serve_static_file(request.url, "WebServer/templates/gauge1.html")

        response_builder.build_response()
        writer.write(response_builder.response)
        await writer.drain()
        await writer.wait_closed()

    except OSError as e:
        print('connection error ' + str(e.errno) + " " + str(e))

async def detect_pressure(ble_deque, notify_deque):
    global max_psi
    global min_psi
    try:
        print('Starting pressure sensor')

        """ Monitor the output from the pressure sensor attached to the pump """
        """ Use the second channel on the ADC chip """

        MCP3008_CHAN = 1
        voltage_ref = 3.3

        max_psi = 80
        min_psi = 20
        pressure = PressureSensor(min_psi, max_psi, MCP3008_CHAN, voltage_ref, notify_deque)
        await pressure.monitor_pressure_sensor()

    except KeyboardInterrupt:
        print("\nExiting the program..")
        pass

    except:
        print("Some error/exception occurred")


async def setup_bluetooth(ble_deque, notify_deque):
    try:
        print('Setting up  bluetooth')
        bluetooth = Bluetooth(ble_deque, notify_deque)
        await bluetooth.start_bluetooth()

    except KeyboardInterrupt:
        print("\nExiting the program..")
        pass

    except:
        print("Some error/exception occurred")

async def blink_led():

    while True:
        # just pulse the on board led for sanity check that the code is running
        try:
            IoHandler.blink_onboard_led()
            await uasyncio.sleep(5)

        except KeyboardInterrupt:
            print("\nExiting the program..")
            break

        except:
            print("Some error/exception occurred")
            break


async def setup_web_server(ble_deque, notify_deque):
    #ip_address = wifi.ip

    try:

        msg_str = 'Setting up webserver...\n'
        ble_deque.append(msg_str)
        server = uasyncio.start_server(handle_request, "0.0.0.0", 80)
        uasyncio.create_task(server)

    except KeyboardInterrupt:
        print("\nExiting the program..")
        pass

    except:
        print("Some error/exception occurred")


async def setup_wifi_connection(ble_deque, notify_deque):
    global send_bluetooth_flag

    print("Starting WiFi")
    wifi = WiFiConnection()
    while True:
        try:
            if not wifi.start_station_mode(True):
                if send_bluetooth_flag == False:
                    str = "Enter your wifi credentials now\n"
                    ble_deque.append(str)
                    send_bluetooth_flag = True
                    await uasyncio.sleep(1)

                # ssid and pwd obtained via bluetooth communication from user
                if ssid is not '' and pwd is not '':
                    str = "Updating wifi credentials from BLE...\n"
                    credentials = {"ssid": ssid, "password": pwd }
                    wifi.update_credentials("Wifi/NetworkCredentials.py", credentials)
                    ble_deque.append(str)
            else:
                ble_deque.append(f"Wifi IP address: {wifi.ip}")
                break

            await uasyncio.sleep(5)

        except KeyboardInterrupt:
            print("\nExiting the program..")
            break

        except:
            break

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


def alert_user_via_email(msg):
    global email_flag
    if email_flag == False:
        body = prepare_email(msg)
        # TODO: enable email sending
        #send_email(body)
        email_flag = True
    return

async def notifications(ble_deque, notify_deque):
    """ Start an infinite loop to check the message deque """
    global email_flag
    global ssid
    global pwd
    global ip_address
    email_flag = False
    global max_psi
    global min_psi
    while True:
        if len(notify_deque) > 0:
            get_notify_msg = notify_deque.popleft()
            if get_notify_msg is not None:
                if 'ssid' in get_notify_msg:
                    print(f"SSID: {get_notify_msg}")
                    data_list = get_notify_msg.split()
                    ssid = data_list[1]

                elif 'pwd' in get_notify_msg or 'password' in get_notify_msg:
                    print(f"Password: {get_notify_msg}")
                    ip_address = machine.unique_id()
                    data_list = get_notify_msg.split()
                    pwd = data_list[1]

                elif 'max' in get_notify_msg:
                    data_list = get_notify_msg.split()
                    max_psi = int(data_list[1])

                elif 'min' in get_notify_msg:
                    data_list = get_notify_msg.split()
                    min_psi = int(data_list[1])

                elif 'ip' in get_notify_msg:
                    print(f"Ip Address: {ip_address}")
                    str = f"IP Address: http://{ip_address}/\n"
                    ble_deque.append(str)

                elif 'volt' in get_notify_msg:
                    average_voltage = await get_voltage_reading()
                    if average_voltage < 2.6:
                        status = "pump is ON"
                    else:
                        status = "pump is OFF"
                    str = f"Voltage sensor: {average_voltage:.2f} V - {status} \n"
                    ble_deque.append(str)

                elif 'psi' in get_notify_msg:
                    psi = IoHandler.get_pressure_reading()
                    str = f"Pump pressure: {psi:.1f} PSI\n"
                    ble_deque.append(str)

                else:
                    print("unknown data\n")

                #need to handle cases for turning on external led and/or buzzer


        pressure = IoHandler.get_pressure_reading()
        if pressure < 20:
            if email_flag == False:
                warning_str = f"PUMP PRESSURE LOW! - {pressure:.1f} PSI"
                alert_user_via_email(warning_str)
                ble_deque.append(warning_str)
                email_flag = True

        if pressure > 80:
            if email_flag == False:
                warning_str = f"PUMP PRESSURE HIGH! - {pressure:.1f} PSI"
                alert_user_via_email(warning_str)
                ble_deque.append(warning_str)
            email_flag = True

        await uasyncio.sleep(2)


#We create coroutine called main() that serves as a central point to coordinate the execution of the tasks.
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
    global ip_address
    global max_psi
    global min_psi

    print("Starting notifications")
    uasyncio.create_task(notifications(ble_deque, notify_deque))
    print("Starting voltage sensor")
    uasyncio.create_task(detect_voltage(ble_deque, notify_deque))
    print("Starting pressure sensor")
    uasyncio.create_task(detect_pressure(ble_deque, notify_deque))
    print("Starting BlueTooth")
    uasyncio.create_task(setup_bluetooth(ble_deque, notify_deque))
    print("Starting Wifi connection")
    uasyncio.create_task(setup_wifi_connection(ble_deque, notify_deque))
    print("Starting Web Server")
    uasyncio.create_task(setup_web_server(ble_deque, notify_deque))
    print("Starting Led Blinking")
    uasyncio.create_task(blink_led())


try:
    # start asyncio tasks on first core
    loop = uasyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()

finally:
    print("running finally block")

