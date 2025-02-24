import streamlit as st
import paho.mqtt.client as mqtt
import time
import psutil
import datetime
import queue
import threading
import pandas as pd
import json  

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

    try:
        message_data = json.loads(message_content)  
        message_queue.put(message_time)
    except (ValueError, KeyError, json.JSONDecodeError):
        pass  

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for MQTT connection."""
    if rc == 0:
        client.subscribe(TOPIC)

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

# Create placeholders for graphs and messages
cpu_graph_placeholder = st.empty()
messages_graph_placeholder = st.empty()
messages_placeholder = st.empty()

# --- Data Update Function ---
def update_data():
    """Update session state with new MQTT messages and CPU usage."""
    current_time = time.time()

    # Process MQTT messages
    while not message_queue.empty():
        message_time = message_queue.get()
        st.session_state["mqtt_messages"].append(
            f"📩 Message received at {datetime.datetime.fromtimestamp(message_time).strftime('%H:%M:%S')}"
        )
        st.session_state["mqtt_timestamps"].append(message_time)

    # Remove old messages beyond TIME_WINDOW
    while st.session_state["mqtt_timestamps"] and (current_time - st.session_state["mqtt_timestamps"][0]) > TIME_WINDOW:
        st.session_state["mqtt_timestamps"].pop(0)
        st.session_state["mqtt_messages"].pop(0)

    # CPU Monitoring
    cpu_usage = psutil.cpu_percent(interval=0.1)
    st.session_state["cpu_usage"].append(cpu_usage)
    st.session_state["cpu_timestamps"].append(current_time)

    while st.session_state["cpu_timestamps"] and (current_time - st.session_state["cpu_timestamps"][0]) > TIME_WINDOW:
        st.session_state["cpu_timestamps"].pop(0)
        st.session_state["cpu_usage"].pop(0)

    # Count messages per minute
    messages_last_minute = len([t for t in st.session_state["mqtt_timestamps"] if current_time - t <= 60])
    st.session_state["messages_per_minute"].append(messages_last_minute)
    st.session_state["messages_per_minute_times"].append(current_time)

    while st.session_state["messages_per_minute_times"] and (current_time - st.session_state["messages_per_minute_times"][0]) > TIME_WINDOW:
        st.session_state["messages_per_minute_times"].pop(0)
        st.session_state["messages_per_minute"].pop(0)

# --- Plot Graphs ---
def plot_cpu_graph():
    if st.session_state["cpu_timestamps"]:
        data = pd.DataFrame({
            "Time": [datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S') for t in st.session_state["cpu_timestamps"]],
            "CPU Usage (%)": st.session_state["cpu_usage"]
        }).set_index("Time")

        cpu_graph_placeholder.empty()
        with cpu_graph_placeholder.container():
            st.subheader("💻 CPU Usage (%) Over Time")
            st.line_chart(data)

def plot_messages_per_minute():
    if st.session_state["messages_per_minute_times"]:
        data = pd.DataFrame({
            "Time": [datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S') for t in st.session_state["messages_per_minute_times"]],
            "Messages Per Minute": st.session_state["messages_per_minute"]
        }).set_index("Time")

        messages_graph_placeholder.empty()
        with messages_graph_placeholder.container():
            st.subheader("📩 Messages Per Minute Over Time")
            st.line_chart(data)

# --- Auto Refresh every 1 second ---
while True:
    update_data()
    plot_cpu_graph()
    plot_messages_per_minute()

    with messages_placeholder.container():
        st.subheader("📩 Latest MQTT Messages")
        for message in st.session_state["mqtt_messages"][-10:]:
            st.write(message)

    time.sleep(1)
