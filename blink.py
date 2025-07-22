from machine import Pin
from utime import sleep
import uasyncio

class LED:
    def __init__(self, pin_name):
        self.pin = Pin(pin_name, Pin.OUT)

    def toggle(self):
        self.pin.toggle()

    def off(self):
        self.pin.off()

    def on(self):
        self.pin.on()

    def toggle_led(self):
        while True:
            self.pin.toggle()  # Toggle the LED state (on/off)
            sleep(0.5)   # Delay for 0.5 seconds

    def flash_onboard_led(self):
        print("LED starts flashing...")
        pin = Pin("LED", Pin.OUT)  # Use the onboard LED pin
        pin.off()  # Ensure the LED is off initially
        while True:
            try:
                pin.toggle()
                sleep(1) # sleep 1sec
            except KeyboardInterrupt:
                break
            pin.off()
            sleep(1)


# Main function
async def led_test():
#    led = LED("LED")  # Initialize LED on the onboard pin
#    led.flash_onboard_led ()  # Start flashing the LED
    led = LED("GP13")  # Initialize LED on a specific GPIO pin (e.g., GP13)
    led.off()  # Turn the LED off
    led.toggle_led()  # Start toggling the LED state
    led.off()  # Ensure the LED is off before starting
    return


if __name__ == "__main__":
    uasyncio.run(led_test())
