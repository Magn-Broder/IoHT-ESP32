from umqtt.simple import MQTTClient
from machine import SoftI2C, UART
from micropyGPS import MicropyGPS
from machine import Pin
from time import sleep
import mpu6050

#Initialisering af MQTTclient objekt
SERVER = '192.168.1.5' 
CLIENT_ID = 'ESP322'
PORT = 1883
USER = 'esp_client'
PASSWORD = 'mqttclient123'
TOPIC = b'falls'

client = MQTTClient(CLIENT_ID, SERVER, PORT, USER, PASSWORD)

#Initialisering af I2C objekt
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))

#Initialisering af mpu6050 objekt
mpu = mpu6050.accel(i2c)

#Initialisering af UART objekt
uart = UART(2, baudrate=9600, bits=8, parity=None,  stop=1, timeout=5000, rxbuf=1024)

#Initialisering af GPS objekt
gps = MicropyGPS()

def gps_main():
    buf = uart.readline()
    for char in buf:
    # Note the conversion to to chr, UART outputs ints normally
        gps.update(chr(char))
    coordinates = f"{gps.latitude_string()} {gps.longitude_string()}"
    return coordinates
    

def detect_fall():
    # Get accelerometer values
    values = mpu.get_values()
    
    # Extract relevant values
    accel_x = values['AcX']
    accel_y = values['AcY']
    accel_z = values['AcZ']

    # Calculate the magnitude of acceleration
    accel_magnitude = (accel_x**2 + accel_y**2 + accel_z**2)**0.5

    # Set a threshold for fall detection (adjust as needed)
    fall_threshold = 2500
    

    # Check if the magnitude of acceleration is below the threshold
    if accel_magnitude < fall_threshold:
        return True

#Forbind til MQTT-broker
MAX_RETRIES = 3
retries = 0

while retries < MAX_RETRIES:
    try:
        print("Connecting to MQTT broker...")
        client.connect()
        print("Connection successful!")
        break  # Exit the loop if the connection is successful
    except Exception as e:
        print(f"Connection Error (Attempt {retries + 1}): {e}")
        retries += 1
        time.sleep(5)  # Wait before retrying
        
while True:
    if detect_fall():
        print("Fall detected!")
        place = gps_main()
        message = f"Faldet!,{place}"
        msg = b'{}'.format(message)
        client.publish(TOPIC, msg)
        print("Published status:", message)
        sleep(2)
        
        


  

