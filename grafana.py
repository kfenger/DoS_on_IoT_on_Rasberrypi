import paho.mqtt.client as mqtt
import pandas as pd
from flask import Flask, render_template
import plotly.express as px

# Flask app
app = Flask(__name__)

# MQTT Konfigurasjon
BROKER_IP = "192.168.86.129"  # Sett IP-en til IoT serveren
BROKER_PORT = 1883
TOPIC = "iot/device/data"  # MQTT-toppen for angrep/meldinger

# Liste for å lagre sanntidsdata
mqtt_data = []

# MQTT Klient Konfigurasjon
client = mqtt.Client()

# Callback for når en melding mottas
def on_message(client, userdata, message):
    global mqtt_data
    payload = message.payload.decode('utf-8')
    mqtt_data.append(payload)
    print(f"Mottatt data: {payload}")

# Koble til MQTT Broker og abonner på topic
client.on_message = on_message
client.connect(BROKER_IP, BROKER_PORT)
client.subscribe(TOPIC)

# Start MQTT-drikkingstråd
client.loop_start()

# Flask side for å vise dashboard
@app.route("/")
def index():
    # Bruk data fra MQTT for å lage en graf
    df = pd.DataFrame(mqtt_data, columns=['Data'])

    # Generer en enkel tidsserie-graf
    fig = px.line(df, x=df.index, y='Data', title="IoT Performance and Attack Visualization")
    
    # Tjenesten som leverer grafen
    return fig.to_html()

# Kjør Flask-appen
if __name__ == "__main__":
    app.run(debug=True)
