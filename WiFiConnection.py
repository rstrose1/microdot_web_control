# class to handle WiFi connection
import utime
import network
from NetworkCredentials import NetworkCredentials


class WiFiConnection:
    # class level vars accessible to all code
    status = network.STAT_IDLE
    ip = ""
    subnet_mask = ""
    gateway = ""
    dns_server = ""
    wlan = None
    ssid = None
    password = None

    def __init__(self, ssid=None, password=None):
        self.ssid = ssid
        self.password = password

    def modify_credential_file(self, filename, original, replacement):
        print(filename)
        print(original)
        print(replacement)

        try:
            with open(filename, "r") as f:
                file_content = f.read()
            #Modify the content
            updated_content = file_content.replace(original, replacement)
            with open(filename, "w") as f:
                f.write(updated_content)
            f.close()

        except Exception as e:
            print(f"Error updating file: {filename}: {e}")


    def update_credentials(self, filename, credentials):
        ssid_value = credentials['ssid']
        pwd_value = credentials['password']

        WiFiConnection.ssid = ssid_value
        WiFiConnection.password = pwd_value

        # Save to file
        # Cant figure out a way as yet to update elements in file all at once
        # so will do one by one for now.
        # some how f.writelines doesn't appear to be woring in micropython --need to investigate further
        original_str = "ssid = ''"
        replacement_str = f"ssid = '{ssid_value}'"
        self.modify_credential_file(filename, original_str, replacement_str)

        original_str = "password = ''"
        replacement_str = f"password = '{pwd_value}'"
        self.modify_credential_file(filename, original_str, replacement_str)


    @classmethod
    def start_station_mode(cls, print_progress=False):
        # set WiFi to station interface
        cls.wlan = network.WLAN(network.STA_IF)
        # activate the network interface
        cls.wlan.active(True)
        # connect to wifi network
        print("Testing ssid..........")
        print(cls.ssid)
        if cls.ssid is not None:
            cls.wlan.connect(cls.ssid, cls.password)
        else:
            cls.wlan.connect(NetworkCredentials.ssid, NetworkCredentials.password)

        cls.status = network.STAT_CONNECTING
        if print_progress:
            print("Connecting to Wi-Fi - please wait")
        max_wait = 20
        # wait for connection - poll every 0.5 secs
        while max_wait > 0:
            """
                0   STAT_IDLE -- no connection and no activity,
                1   STAT_CONNECTING -- connecting in progress,
                -3  STAT_WRONG_PASSWORD -- failed due to incorrect password,
                -2  STAT_NO_AP_FOUND -- failed because no access point replied,
                -1  STAT_CONNECT_FAIL -- failed due to other problems,
                3   STAT_GOT_IP -- connection successful.
            """
            if cls.wlan.status() < 0 or cls.wlan.status() >= 3:
                # connection attempt finished
                break
            max_wait -= 1
            utime.sleep(0.5)

        # check connection
        cls.status = cls.wlan.status()
        if cls.wlan.status() != 3:
            # No connection
            if print_progress:
                print("Connection Failed")
            return False
        else:
            # connection successful
            config = cls.wlan.ifconfig()
            cls.ip = config[0]
            cls.subnet_mask = config[1]
            cls.gateway = config[2]
            cls.dns_server = config[3]
            if print_progress:
                print('ip = ' + str(cls.ip))
            return True
