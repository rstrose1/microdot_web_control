
import sys
import os
from sys import path
import bluetooth
import uasyncio
from ucollections import deque
from Bluetooth.bluetooth_peripheral import BLESimplePeripheral

class Bluetooth(object):
    def __init__(self, ble_deque, notify_deque):
        self.ble_deque = ble_deque
        self.notify_deque = notify_deque

    def extract_data_from_ble(self, data):
        """ Extracts specific data from a byte string received over Bluetooth."""
        data_list = data.split()
        return data_list[1].decode('utf-8')

    def append_to_deque(self, data):
        """ Appends data to the notification_deque."""
        ble_msg = data.decode('utf-8')
        self.notify_deque.append(ble_msg)
        print(ble_msg)

    def on_rx(self, data):
        """
        Callback function to handle data received via Bluetooth.
        Args:
            data (bytes): The data received from the Bluetooth connection.
        """
        print("Pico Data received: ", data)  # Print the received data

        # User requested IP address via bluetooth connection
        if 'ip' in data:
            self.append_to_deque(data)

        # User requested PSI value via bluetooth connection
        elif 'psi' in data:
            self.append_to_deque(data)

        # User requested VOLT value
        elif 'volt' in data:
            self.append_to_deque(data)

        # User passed wifi ssid over bluetooth connection
        elif 'ssid' in data:
            self.append_to_deque(data)

        # User passed email address over bluetooth connection
        elif 'email' in data:
            self.append_to_deque(data)

        # User passed wifi password over bluetooth connection
        elif 'pwd' in data:
            self.append_to_deque(data)

        # User passed wifi password over bluetooth connection
        elif 'password' in data:
            self.append_to_deque(data)

        # User passed max psi over bluetooth connection
        elif 'max' in data:
            self.append_to_deque(data)

        # User passed min psi over bluetooth connection
        elif 'min' in data:
            self.append_to_deque(data)

        else:
            print("unknown data\n")

        return

    async def start_bluetooth(self):
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
                sp.on_write(self.on_rx)  # Set the callback function for data reception
                try:
                    if len(self.ble_deque) > 0:
                        snd_msg = self.ble_deque.popleft()
                        sp.send(snd_msg)
                except Exception:
                    pass

            await uasyncio.sleep(0)