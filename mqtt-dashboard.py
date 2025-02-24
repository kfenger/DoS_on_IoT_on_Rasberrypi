import streamlit as st
import paho.mqtt.client as mqtt
import time
import psutil
import datetime
import queue
import threading
import pandas as pd
import json  # <-- Importerer for JSON parsing

# Set page configuration
st.set_page_config(layout="wide", page_title="MQTT & CPU Monitor")

# MQTT Broker Configuration
BROKER = "10.0.0.18"
TOPIC = "raspberry_pi/test"
TIME_WINDOW = 60  # Keep only the last 60 seconds of data

# --- Global state ---
if "mqtt_timestamps" not in st.session_state:
    st.session_state["mqtt_timestamps"] = []
    st.session_state["cpu_usage"] = []
    st.session_state["cpu_timestamps"] = []
    st.session_state["mqtt_messages"] = []
    st.session_state["messages_per_minute"] = []
    st.session_state["messages_per_minute_times"] = []

# --- MQTT Message Queue ---
message_queue = queue.Queue()

def on_message(client, userdata, msg):
    """Callback for when a message is received from MQTT broker."""
    message_time = time.time()
    message_content = msg.payload.decode()

    print(f"📩 Received message: {message_content}")  # Sjekker formatet på meldingene

    try:
        # **🔍 Forsøk å parse JSON-meldingen**
        message_data = json.loads(message_content)  # <-- Konverterer til dict
        temperature = float(message_data["temperature"])  # <-- Henter temperatur
        humidity = float(message_data["humidity"])  # <-- Henter fuktighet

        # **Legg meldingen i køen**
        message_queue.put(message_time)

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"⚠ JSON parsing error: {e}")  # Hvis meldingen ikke er riktig formatert

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for MQTT connection."""
    if rc == 0:
        print("✅ Connected to MQTT broker!")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Connection failed with code {rc}")

def mqtt_thread():
    """Separate thread to handle MQTT client."""
    client = mqtt.Client(protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)
    client.loop_forever()

# Start MQTT in a separate thread
if "mqtt_thread_started" not in st.session_state:
    threading.Thread(target=mqtt_thread, daemon=True).start()
    st.session_state["mqtt_thread_started"] = True

# --- Streamlit UI ---
st.title("📡 MQTT & CPU Monitor")
st.write("Monitoring MQTT messages and CPU usage in real-time (last 60 seconds).")

# Create placeholders for the graphs
cpu_graph_placeholder = st.empty()
messages_graph_placeholder = st.empty()
messages_placeholder = st.empty()

# --- Data Update Function ---
def update_data():
    """Update session state with new MQTT messages and CPU usage."""
    current_time = time.time()

    # Hent nye meldinger fra køen
    while not message_queue.empty():
        message_time = message_queue.get()
        st.session_state["mqtt_messages"].append(
            f"📩 Message received at {datetime.datetime.fromtimestamp(message_time).strftime('%H:%M:%S')}"
        )
        st.session_state["mqtt_timestamps"].append(message_time)

    # Fjern gamle meldinger (eldre enn 60 sekunder)
    while st.session_state["mqtt_timestamps"] and (current_time - st.session_state["mqtt_timestamps"][0]) > TIME_WINDOW:
        st.session_state["mqtt_timestamps"].pop(0)
        st.session_state["mqtt_messages"].pop(0)

    # CPU-bruk oppdatering
    cpu_usage = psutil.cpu_percent(interval=0.1)
    st.session_state["cpu_usage"].append(cpu_usage)
    st.session_state["cpu_timestamps"].append(current_time)

    # Fjern gammel CPU-data
    while st.session_state["cpu_timestamps"] and (current_time - st.session_state["cpu_timestamps"][0]) > TIME_WINDOW:
        st.session_state["cpu_timestamps"].pop(0)
        st.session_state["cpu_usage"].pop(0)

    # **Telle nye meldinger per minutt**
    messages_last_minute = len([t for t in st.session_state["mqtt_timestamps"] if current_time - t <= 60])
    st.session_state["messages_per_minute"].append(messages_last_minute)
    st.session_state["messages_per_minute_times"].append(current_time)

    # Fjern gammel meldingsstatistikk
    while st.session_state["messages_per_minute_times"] and (current_time - st.session_state["messages_per_minute_times"][0]) > TIME_WINDOW:
        st.session_state["messages_per_minute_times"].pop(0)
        st.session_state["messages_per_minute"].pop(0)

# --- Plot Graphs ---
def plot_cpu_graph():
    if st.session_state["cpu_timestamps"]:
        st.subheader("💻 CPU Usage (%) Over Time")
        data = pd.DataFrame({
            "Time": [datetime.datetime.fromtimestamp(t) for t in st.session_state["cpu_timestamps"]],
            "CPU Usage (%)": st.session_state["cpu_usage"]
        })
        cpu_graph_placeholder.line_chart(data.set_index("Time"))

def plot_messages_per_minute():
    if st.session_state["messages_per_minute_times"]:
        st.subheader("📩 Messages Per Minute Over Time")
        data = pd.DataFrame({
            "Time": [datetime.datetime.fromtimestamp(t) for t in st.session_state["messages_per_minute_times"]],
            "Messages Per Minute": st.session_state["messages_per_minute"]
        })
        messages_graph_placeholder.line_chart(data.set_index("Time"))

# --- Auto Refresh every 1 second ---
st_autorefresh = st.empty()
st_autorefresh.write("🔄 Auto-updating...")

# --- Main Update Loop ---
while True:
    update_data()
    plot_cpu_graph()
    plot_messages_per_minute()  # <--- Nå vises Messages Per Minute

    with messages_placeholder.container():
        st.subheader("📩 Latest MQTT Messages")
        for message in st.session_state["mqtt_messages"][-10:]:
            st.write(message)

    # Auto refresh every 1 second
    time.sleep(1)
    st_autorefresh.text(f"🔄 Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")
