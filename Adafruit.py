import paho.mqtt.client as mqtt


# Adafruit IO credentials
ADAFRUIT_IO_USERNAME = 'Kfenger' # Replace with your Adafruit username
ADAFRUIT_IO_KEY = 'aio_BJeD89hPlw09JNRBr3QYGDcN2ZQn' # Replace with your Adafruit IO key. You can find this key on the Adafruit IO website under the "API Key" section, Linux Shell.


# Adafruit IO feed details
FEED = 'IoT-device'
BROKER = 'io.adafruit.com'
PORT = 1883
TOPIC = f'{ADAFRUIT_IO_USERNAME}/feeds/{FEED}'

# Define the callback functions
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}: {msg.payload.decode()}")


# Set up the client
client = mqtt.Client()
client.username_pw_set(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(BROKER, PORT, 60)

# Blocking loop to process network traffic and dispatch callbacks
client.loop_forever()