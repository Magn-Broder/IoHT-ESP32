from machine import Pin, SoftI2C, ADC
from umqtt.simple import MQTTClient
import usocket as socket
import ubinascii
import uhashlib
import _thread
import ssd1306
import ussl
import time

SERVER = '192.168.1.5'
CLIENT_ID = 'ESP321'
PORT = 1883
USER = 'esp_client'
PASSWORD = 'mqttclient123'
TOPIC = b'BPM'

client = MQTTClient(CLIENT_ID, SERVER, PORT, USER, PASSWORD)

adc = ADC(Pin(32))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_10BIT)

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
display = ssd1306.SSD1306_I2C(128, 32, i2c)

MAX_HISTORY = 10
TOTAL_BEATS = 30

history = []
beats = []
bpm = None
beat = False

HEART = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 1, 1, 0],
    [1, 1, 1, 1, 0, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0],
]
last_y = 0

def refresh(bpm, beat, v, minima, maxima):
    global last_y

    display.vline(0, 0, 32, 0)
    display.scroll(-1, 0)

    if maxima - minima > 0:
        y = 32 - int(16 * (v - minima) / (maxima - minima))
        display.line(125, last_y, 126, y, 1)
        last_y = y

    display.fill_rect(0, 0, 128, 16, 0)  

    if bpm is not None:
        display.text("%d bpm" % bpm, 12, 0)

    if beat:
        for y, row in enumerate(HEART):
            for x, c in enumerate(row):
                display.pixel(x, y, c)

    display.show()

def calculate_bpm(beats):
    if len(beats) > 1:
        beat_time = beats[-1] - beats[0]
        if beat_time > 0:
            return int(len(beats) / (beat_time / 60))

def detect():
    while True:
        global history, beats, bpm, beat

        v = adc.read()
        history.append(v)

        history = history[-MAX_HISTORY:]

        minima, maxima = min(history), max(history)

        threshold_on = (minima + maxima *2) // 3 # 3/4
        threshold_off = (minima + maxima) // 2  # 1/2

        if v > threshold_on and not beat:
            beat = True
            beats.append(time.time())
            # Truncate beats queue to max
            beats = beats[-TOTAL_BEATS:]
            bpm = calculate_bpm(beats)

        if v < threshold_off and beat:
            beat = False
        print("BPM:", bpm)

        refresh(bpm, beat, v, minima, maxima)
        
def sha256(data):
    hash_sha256 = uhashlib.sha256()
    hash_sha256.update(data)
    return ubinascii.hexlify(hash_sha256.digest()).decode()

def mqtt_publish():
    while True:
        global bpm
        if bpm is not None:
            try:
                bpm_hash = sha256(str(bpm).encode())
                msg = b'{},{}'.format(bpm, bpm_hash)
                client.publish(TOPIC, msg)
                print("Published BPM:", bpm)
                sleep(60)
            except Exception as e:
                print(f"Error publishing message: {e}")
        
MAX_RETRIES = 3
retries = 0

while retries < MAX_RETRIES:
    try:
        print("Connecting to MQTT broker...")
        client.connect()
        print("Connection successful!")
        break  
    except Exception as e:
        print(f"Connection Error (Attempt {retries + 1}): {e}")
        retries += 1
        time.sleep(5)  


_thread.start_new_thread(detect, ())
mqtt_publish()
