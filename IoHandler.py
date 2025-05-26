# class to handle the IO for the demo setup
from machine import Pin, ADC
import neopixel
import time


class IoHandler:

    conversion_factor = 3.3 / 65535  # Assuming a 3.3V reference voltage

    pin = Pin("LED", Pin.OUT)

    voltage_sensor = ADC(0)  # Assuming voltage sensor is connected to ADC channel 0
    pressure_sensor = ADC(1)  # Assuming pressure sensor is connected to ADC channel 1

    # create array of neopixels
    rgb_leds = neopixel.NeoPixel(Pin(15), 8)
    # create list of RGB tuples to control led states
    rgb_led_colours = [(0, 0, 0)] * 8

    # red led
    led = Pin(28, Pin.OUT)
    led_state = 0

    # potentiometer
    pot = ADC(26)
    pot_value = 0

    # temp sensor
    temp = ADC(4)
    temp_value = 0

    # coloured leds
    blue_led = Pin(16, Pin.OUT)
    yellow_led = Pin(17, Pin.OUT)
    green_led = Pin(18, Pin.OUT)
    coloured_states = [0, 0, 0]

    def __init__(self):
        # get everything into a starting state
        self.__class__.show_red_led()
        self.__class__.get_pot_reading()
        self.__class__.show_coloured_leds()
        self.__class__.clear_rgb_leds()

    # blink onboard led
    @classmethod
    def blink_onboard_led(cls):
        cls.pin.toggle()

    @classmethod
    def show_coloured_leds(cls):
        cls.blue_led.value(cls.coloured_states[0])
        cls.yellow_led.value(cls.coloured_states[1])
        cls.green_led.value(cls.coloured_states[2])

    @classmethod
    def set_coloured_leds(cls, states):
        try:
            cls.set_blue_led(states[0])
            cls.set_yellow_led(states[1])
            cls.set_green_led(states[2])
        except:
            pass
        cls.show_coloured_leds()

    @classmethod
    def set_blue_led(cls, state):
        cls.coloured_states[0] = 0 if state == 0 else 1

    @classmethod
    def set_yellow_led(cls, state):
        cls.coloured_states[1] = 0 if state == 0 else 1

    @classmethod
    def set_green_led(cls, state):
        cls.coloured_states[2] = 0 if state == 0 else 1

    @classmethod
    def get_blue_led(cls):
        return 0 if cls.coloured_states[0] == 0 else 1

    @classmethod
    def get_yellow_led(cls):
        return 0 if cls.coloured_states[1] == 0 else 1

    @classmethod
    def get_green_led(cls):
        return 0 if cls.coloured_states[2] == 0 else 1

    # red led handlers
    @classmethod
    def show_red_led(cls):
        cls.led.value(cls.led_state)

    @classmethod
    def toggle_red_led(cls):
        cls.led_state = 0 if cls.led_state == 1 else 1
        cls.show_red_led()

    @classmethod
    def get_red_led(cls):
        return 0 if cls.led_state == 0 else 1

    @classmethod
    def set_red_led(cls, state):
        cls.led_state = 0 if state == 0 else 1
        cls.show_red_led()

    # potentiometer handler
    @classmethod
    def get_pot_reading(cls):
        cls.pot_value = cls.pot.read_u16()
        return cls.pot_value

    # voltage sensor handler
    @classmethod
    def get_voltage_reading(cls):
        voltage_value = cls.voltage_sensor.read_u16() * cls.conversion_factor
        return voltage_value

    # pressure sensor handler
    @classmethod
    def get_pressure_reading(cls):
        adc_value = cls.pressure_sensor.read_u16()
        voltage = adc_value * cls.conversion_factor
        psi = round(((voltage * 95.48) - 34.81), 2)
        if psi < 0:
            psi = 0
        pressure_value = psi
        return pressure_value

    # temp handler
    @classmethod
    def get_temp_reading(cls):
        temp_voltage = cls.temp.read_u16() * (3.3 / 65535)
        cls.temp_value = 27 - (temp_voltage - 0.706) / 0.001721
        return cls.temp_value

    # rgb leds
    @classmethod
    def set_rgb_pixel(cls, pixel, colour):
        cls.rgb_leds[pixel] = colour
        cls.rgb_led_colours[pixel] = colour

    @classmethod
    def get_rgb_pixel(cls, pixel):
        return cls.rgb_led_colours[pixel]

    @classmethod
    def set_rgb_leds(cls, rgb_red, rgb_green, rgb_blue):
        for n in range(4):
            cls.set_rgb_pixel(n, (rgb_red, rgb_green, rgb_blue))
        cls.show_rgb_leds()

    @classmethod
    def show_rgb_leds(cls):
        cls.rgb_leds.write()

    @classmethod
    def clear_rgb_leds(cls):
        for n in range(8):
            cls.set_rgb_pixel(n, (0, 0, 0))
        cls.show_rgb_leds()
