from umqtt.simple import MQTTClient
import machine
import network

# Set your MQTT broker's details
mqtt_broker = "192.168.1.102"  # Replace with your broker's IP address
mqtt_port = 1883
mqtt_topic = b"test_topic"

# WiFi settings
wifi_ssid = "TP-Link_0772"
wifi_password = "39222480"

# Function to connect to WiFi
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(wifi_ssid, wifi_password)
        while not wlan.isconnected():
            time.sleep(1)
        print("Connected to WiFi")

# Function to publish a message
def publish_message(client, message):
    try:
        client.publish(mqtt_topic, message)
        print(f"Published: {message}")
    except Exception as e:
        print(f"Error publishing message: {e}")

# Function to handle received messages
def on_message(topic, message):
    print(f"Received message on topic {topic}: {message}")

# Connect to WiFi
connect_to_wifi()

# Create MQTT client
unique_id = machine.unique_id()
unique_id_bytes = machine.unique_id()

# Convert the bytes to a hexadecimal string
unique_id_hex = ''.join(['{:02X}'.format(b) for b in unique_id_bytes])

# Create the client ID by appending the hexadecimal string
client_id = "esp32-" + unique_id_hex

client = MQTTClient(client_id, mqtt_broker, port=mqtt_port)

# Set the callback function for message reception
client.set_callback(on_message)

# Connect to the broker
try:
    client.connect()
except Exception as e:
    print(f"Error connecting to MQTT broker: {e}")
    machine.reset()

# Subscribe to the topic
client.subscribe(mqtt_topic)
print(f"Subscribed to topic: {mqtt_topic}")

# Main loop
try:
    while True:
        client.check_msg()

        # Check if there's a message to publish every 2 seconds
        user_input = input("Enter a message to publish (or 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break
        publish_message(client, user_input)
        time.sleep(2)

except KeyboardInterrupt:
    pass
finally:
    client.disconnect()
    print("Disconnected from the broker.")
