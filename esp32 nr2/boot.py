import network
from time import sleep

def do_connect(ssid, password, max_retries=20, retry_delay=2):
    sta_if = network.WLAN(network.STA_IF)
    
    # Check if the station interface is already connected
    if sta_if.isconnected():
        print('Already connected. Network config:', sta_if.ifconfig())
        return
    
    # Activate the station interface
    sta_if.active(True)
    
    # Attempt to connect to the Wi-Fi network
    sta_if.connect(ssid, password)
    
    # Wait for the connection to be established
    retries = 0
    while not sta_if.isconnected() and retries < max_retries:
        print('Connecting to network... (Attempt {}/{})'.format(retries + 1, max_retries))
        sleep(retry_delay)
        retries += 1

    # Print network configuration
    if sta_if.isconnected():
        print('Connected. Network config:', sta_if.ifconfig())
    else:
        print('Failed to connect. Check Wi-Fi credentials.')

# Specify your Wi-Fi credentials
wifi_ssid = 'TP-Link_DC58'
wifi_password = '86634441'

# Connect to Wi-Fi
do_connect(wifi_ssid, wifi_password)