import paho.mqtt.client as mqtt
import threading

broker_address = "192.168.1.102"
port = 1883
topic = "test_topic"

def on_message(client, userdata, message):
    print(f"Received message on topic {message.topic}: {message.payload.decode()}")

def on_publish(client, userdata, mid):
    print(f"Message published with MID: {mid}")

def publish_message(message):
    client.publish(topic, message)

def input_thread():
    while True:
        user_input = input("Enter a message to publish (or 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break
        publish_message(user_input)

# Setup MQTT client
client = mqtt.Client()
client.on_message = on_message
client.on_publish = on_publish

client.connect(broker_address, port)
client.subscribe(topic)

# Start a thread for handling user input
input_thread = threading.Thread(target=input_thread, daemon=True)
input_thread.start()

# Loop to handle MQTT events
client.loop_forever()

