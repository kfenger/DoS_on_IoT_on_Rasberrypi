import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import paho.mqtt.client as mqtt
import threading
import paho.mqtt.client as mqtt
import time
import json

# Global variables for real-time data
received_messages = []  # Stores messages from the MQTT broker

# Function to handle MQTT messages
def on_message(client, userdata, message):
    global received_messages
    try:
        print(f"Received message on topic: {message.topic}")
        print(f"Raw message: {message.payload}")

        # Decode and parse message
        payload_str = message.payload.decode()
        print(f"Decoded message: {payload_str}")

        data = json.loads(payload_str)
        print(f"Parsed data: {data}")

        # Store valid messages in the list
        if "temperature" in data and "humidity" in data:
            received_messages.append({
                "Timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "Temperature": data["temperature"],
                "Humidity": data["humidity"]
            })

            # Limit stored messages to 10
            if len(received_messages) > 100:
                received_messages.pop(0)

            print(f"Number of stored messages: {len(received_messages)}")

    except Exception as e:
        print(f"Error processing message: {e}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully!")
        client.subscribe("iot/device/data")
        print("Subscribed to topic 'iot/device/data'")
    else:
        print(f"Failed to connect with code {rc}")

# Start MQTT subscription in a background thread
def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("10.2.8.52")  # Connect to broker
    client.loop_start()  # Start the MQTT loop to receive messages in the background

    # Keep the thread alive
    while True:
        time.sleep(1)


# Start MQTT thread
threading.Thread(target=mqtt_thread, daemon=True).start()

# Start MQTT thread
threading.Thread(target=mqtt_thread, daemon=True).start()

# Create the Dash application
app = dash.Dash(__name__)

# Layout for the dashboard
app.layout = html.Div([
    html.H1("IoT Device Performance Dashboard", style={"textAlign": "center"}),

    # Section for graphs
    html.Div([
        dcc.Graph(id="temperature-graph", style={"width": "50%", "display": "inline-block"}),
        dcc.Graph(id="humidity-graph", style={"width": "50%", "display": "inline-block"})
    ]),

    # Section for the table displaying messages
    html.Div([
        html.H3("Mottatte MQTT-meldinger"),
        dash_table.DataTable(
            id="message-table",
            columns=[{"name": i, "id": i} for i in ["Timestamp", "Temperature", "Humidity"]],
            style_table={"height": "300px", "overflowY": "auto"},
            style_cell={"textAlign": "left"}
        )
    ]),

    # Interval component for real-time updates
    dcc.Interval(
        id="interval-component",
        interval=2000,  # Update every 2 seconds
        n_intervals=0
    )
])


# Callback to update graphs and table
@app.callback(
    [Output("temperature-graph", "figure"),  # Change from "performance-graph"
     Output("humidity-graph", "figure"),     # Change from "attack-graph"
     Output("message-table", "data")],
    [Input("interval-component", "n_intervals")]
)
def update_dashboard(n):
    print(f"Interval triggered: {n}")
    print(f"Number of received messages: {len(received_messages)}")

    # If no messages, do not update
    if not received_messages:
        print("No data to display.")
        raise PreventUpdate

    # Check the received messages and print them for debugging
    print(f"Messages to display in table: {received_messages}")
    
    # Extract data for the graphs
    timestamps = [msg["Timestamp"] for msg in received_messages]
    temperatures = [msg["Temperature"] for msg in received_messages]
    humidities = [msg["Humidity"] for msg in received_messages]

    # Create the temperature graph
    temperature_fig = {
        "data": [
            go.Scatter(x=timestamps, y=temperatures, mode='lines+markers', name="Temperature")
        ],
        "layout": go.Layout(
            title="Temperature Over Time",
            xaxis={"title": "Time"},
            yaxis={"title": "Temperature (°C)"}
        )
    }

    # Create the humidity graph
    humidity_fig = {
        "data": [
            go.Scatter(x=timestamps, y=humidities, mode='lines+markers', name="Humidity")
        ],
        "layout": go.Layout(
            title="Humidity Over Time",
            xaxis={"title": "Time"},
            yaxis={"title": "Humidity (%)"}
        )
    }

    # Return the graphs and the table data
    return temperature_fig, humidity_fig, received_messages  # Return data for the table


# Start the Dash application
if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)

