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


    def flash_onboard_led(self):
        print("LED starts flashing...")
        while True:
            try:
                self.pin.toggle()
                sleep(1) # sleep 1sec
            except KeyboardInterrupt:
                break
            self.pin.off()
            sleep(1)


# Main function
async def led_test():
    led = LED("LED")  # Initialize LED on the onboard pin
    led.flash_onboard_led ()  # Start flashing the LED
    return


if __name__ == "__main__":
    uasyncio.run(led_test())
