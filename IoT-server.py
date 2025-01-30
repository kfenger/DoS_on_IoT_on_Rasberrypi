import time
import paho.mqtt.client as mqtt
import random
import json

# Konfigurer MQTT-klienten
BROKER_IP = "172.20.10.7"  # Sett IP-adressen til IoT-serveren
BROKER_PORT = 1883  
TOPIC = "iot/device/data"

# Opprett MQTT-klient
client = mqtt.Client()

# Koble til broker
client.connect(BROKER_IP, BROKER_PORT, 60)
print("Starter IoT-enhet MQTT-server er oppe og kjører!")

try:
    while True:
        # Generer tilfeldige data for temperatur og fuktighet
        temperature = random.uniform(20.0, 30.0)
        humidity = random.uniform(40.0, 60.0)
        data = {"temperature": temperature, "humidity": humidity}

        # Publiser data til MQTT-broker
        client.publish(TOPIC, json.dumps(data))
        # print(f"Publisert data: {data}")

        # Vent i 2 sekunder før neste publisering
        time.sleep(2)

except KeyboardInterrupt:
    print("Avslutter IoT-enheten.")
    client.disconnect()
