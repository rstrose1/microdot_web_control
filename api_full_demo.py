# full demo with web control panel
# combines multi core and multi tasking
import machine
import utime
from RequestParser import RequestParser
import json
import uasyncio
import _thread
from ResponseBuilder import ResponseBuilder
from WiFiConnection import WiFiConnection
from IoHandler import IoHandler
import random
from detect_voltage_pico import VoltageSensor
from detect_pressure_pico import PressureSensor
from microdot import Microdot as Flask
from microdot import redirect, Request, Response, abort, redirect, send_file, URLPattern, AsyncBytesIO, iscoroutine  # noqa: F401
from microdot.utemplate import Template
import urequests
import socket
import network
import os
import sys
from sys import path



from collections import deque as Queue
FLASK_TEMPLATE_DIR = "/templates/"
GAUGE_HTML_FILE = "gauge1.html"
GAUGE_WEB_PAGE = FLASK_TEMPLATE_DIR + GAUGE_HTML_FILE



# connect to WiFi
# this will block until connected
#if not WiFiConnection.start_station_mode(True):
#    raise RuntimeError('network connection failed')

# connect to WiFi
if not WiFiConnection.start_station_mode(True):
    raise RuntimeError('network connection failed')


class PumpWebServer:
    def __init__(self, name, q, config_q, voltage_q, max_psi, min_psi, user_info=None, index_web_page=None):
        self.app = Flask()
        self.app.secret_key = "Pumpkey"
        self.add_routes()
        self.q = q
        self.voltage_q = voltage_q
        self.config_q = config_q
        self.pressure_int = 0
        self.web_page = index_web_page
        self.warning_low = "PUMP PRESSURE LOW!"
        self.warning_high = "PUMP PRESSURE LOW!"
        self.pump_on_off = "UNKNOWN"
        self.max_psi = max_psi
        self.min_psi = min_psi
        self.pressure_str = f"{0:.2f}"
        self.pressure_val = 0
        self.email_address = "abc.com"
        self.password = "123."
        self.user_info = user_info
        Response.default_content_type = 'text/html'


    def global_var(self):
        @self.app.before_request
        def set_global_variables():
            g.site_title = "Pump Pressure"

    def check_warning_message(self):
        if self.pressure_val < self.min_psi:
            return(self.warning_low)

        if self.pressure_val > self.max_psi:
            return(self.warning_high)


    def add_routes(self):

        # A decorator used to tell the application which URL is associated function
        # https://www.geeksforgeeks.org/retrieving-html-from-data-using-flask/
        @self.app.route('/form', methods =["GET", "POST"])
        def pump_cfg():
            print("In pump_cfg")
            templateData = {
                'email_address': self.user_info.get("email"),
                'name': self.user_info.get("name"),
                'pwd': self.user_info.get("password"),
                'title': "Pump Configuration"
            }
            # Pre-populate the form with existing email and password
            if request.method == "GET":
                return render_template("form.html", **templateData)

            if request.method == "POST":
               # getting input with email_address = email in HTML form
               templateData["email_address"] = request.form.get("email")
               # getting input with passord = pwd in HTML form
               templateData["pwd"] = request.form.get("pwd")
               # getting input with name = name in HTML form
               templateData["name"] = request.form.get("name")

               # Put the data into the queue for processing
               # This is where you would save the data to a file or database
               self.config_q.put_nowait(templateData)

               # Flash a message to the user
               return "Your email is "+templateData["email_address"]



        @self.app.route('/', methods=['GET', 'POST'])
        async def index(request):
            print(f"In index: {self.web_page}")
            self.pressure_str = f"{self.pressure_val:.2f}"
            #return 'Pump Pressure: ' + self.pressure_str
            #return render_template(self.web_page, pressure_str=self.pressure_str)
            name = None
            if request.method == 'POST':
                # Handle form submission
                name = request.form.get('name')
                print(f"Received name: {name}")
                # You can process the name or save it as needed
            #return Template(self.web_page).render(name=name)
            return await Template('gauge1.html').render_async(name=name)
            #return send_file(self.web_page)

        @self.app.route("/page2")
        def page2():
            return "This is page 2"

        @self.app.route('/get_warning_data')
        def get_warning_data():

            warning_str = self.check_warning_message()
            warning = {'content':warning_str}
            return jsonify(warning)

        @self.app.route('/get_pump_data')
        def get_updated_data():
            print("In get_pump_data")
            # Logic to fetch/generate updated content
            try:
                self.pressure_val = self.q.get()
                self.pump_on_off = self.voltage_q.get()
            except Exception as e:
                pass

            self.pressure_str = f"{self.pressure_val:.2f}"
            #data = {'content':self.pressure_str}
            data = {'content':self.pressure_str, 'pump_on_off':self.pump_on_off}

            return jsonify(data)

    def run(self, ip, port, debug=True):
        # To run an https server use the following parameters.
        # Unfortunately works on ipad but not on android or chrome on windows
        #https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
        #self.app.run(ssl_context=('ssl_certs/cert.pem', 'ssl_certs/key.pem'), **kwargs)
        #self.app.run(**kwargs)
        self.app.run(host=ip, port=port, debug=debug)



async def handle_request(reader, writer):
    try:
        raw_request = await reader.read(2048)

        request = RequestParser(raw_request)

        response_builder = ResponseBuilder()

        # filter out api request
        #if request.url_match("/api"):
        if request.url_match("/get_pump_data"):

            action = request.get_action()
            if action == 'readPot':
                # ajax request for potentiometer data
                # used in simple test
                pot_value = IoHandler.get_pot_reading()
                # send back reading as simple text
                response_builder.set_body(pot_value)
            elif action == 'readData':
                # ajax request for data
                pot_value = IoHandler.get_pot_reading()
                temp_value = IoHandler.get_temp_reading()
                cled_states = {
                    'blue': IoHandler.get_blue_led(),
                    'yellow': IoHandler.get_yellow_led(),
                    'green': IoHandler.get_green_led()
                }
                response_obj = {
                    'status': 0,
                    'pot_value': pot_value,
                    'temp_value': temp_value,
                    'cled_states': cled_states,
                    'rgb_leds': IoHandler.rgb_led_colours
                }
                response_builder.set_body_from_dict(response_obj)
            elif action == 'setLedColour':
                # turn on requested coloured led
                # returns json object with led states
                led_colour = request.data()['colour']

                status = 'OK'
                cled_states = {
                    'blue': 0,
                    'yellow': 0,
                    'green': 0
                }
                if led_colour == 'blue':
                    cled_states['blue'] = 1
                elif led_colour == 'yellow':
                    cled_states['yellow'] = 1
                elif led_colour == 'green':
                    cled_states['green'] = 1
                elif led_colour == 'off':
                    # leave leds off
                    pass
                else:
                    status = 'Error'
                IoHandler.set_coloured_leds([cled_states['blue'], cled_states['yellow'], cled_states['green']])
                response_obj = {
                    'status': status,
                    'cled_states': cled_states
                }
                response_builder.set_body_from_dict(response_obj)
            elif action == 'setRgbColour':
                # set RGB colour of first 4 neopixels
                # returns json object with led states
                rgb_red = int(request.data()['red'])
                rgb_green = int(request.data()['green'])
                rgb_blue = int(request.data()['blue'])

                status = 'OK'
                rgb_colours = {
                    'red': rgb_red,
                    'green': rgb_green,
                    'blue': rgb_blue
                }
                IoHandler.set_rgb_leds(rgb_red, rgb_green, rgb_blue)
                response_obj = {
                    'status': status,
                    'rgb_colours': rgb_colours
                }
                response_builder.set_body_from_dict(response_obj)
            else:
                # unknown action
                #response_builder.set_status(404)
                pressure = IoHandler.get_pressure_reading()
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

                data = {
                    'content': pressure,
                    'pump_on_off': pump_on_off
                }
                response_builder.set_body_from_dict(data)




        # try to serve static file
        else:
            #response_builder.serve_static_file(request.url, "/api_index.html")
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
        await uasyncio.sleep(1)

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
   # voltage_q = deque()
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
