import _thread
from umqtt.simple import MQTTClient
import machine
import network
import time
import json

class SharedData:
    def __init__(self):
        self.shared_variable = {
                "data" : {},
                "status": False
             }
        self.event = _thread.allocate_lock()

class Thread1:
    def __init__(self, shared_data):
        self.name = "Thread 1"
        self.shared_data = shared_data
        self.mqtt_broker = "192.168.1.102"
        self.mqtt_port = 1883
        self.mqtt_topic = b"test_topic"
        self.wifi_ssid = "TP-Link_0772"
        self.wifi_password = "39222480"
    
    def connect_to_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print("Connecting to WiFi...")
            wlan.connect(self.wifi_ssid, self.wifi_password)
            while not wlan.isconnected():
                time.sleep(1)
            print("Connected to WiFi")

    def publish_message(self,client, message):
        try:
            client.publish(self.mqtt_topic, json.dumps(message))
            print(f"Published: {message}")
        except Exception as e:
            print(f"Error publishing message: {e}")

    def on_message(self, topic, message):
        print(f"Received message on topic {topic}: {message}")
        
    def run(self):
        self.connect_to_wifi()
        unique_id = machine.unique_id()
        unique_id_bytes = machine.unique_id()
        unique_id_hex = ''.join(['{:02X}'.format(b) for b in unique_id_bytes])
        client_id = "esp32-" + unique_id_hex
        client = MQTTClient(client_id, self.mqtt_broker, port=self.mqtt_port)
        client.set_callback(self.on_message)
        try:
            client.connect()
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            machine.reset()
            
        client.subscribe(self.mqtt_topic)
        print(f"Subscribed to topic: {self.mqtt_topic}")
        
        try:
            while True:
                client.check_msg()
                
                if self.shared_data.shared_variable["status"] == False:
                    self.publish_message(client, self.shared_data.shared_variable["data"])
                    self.shared_data.shared_variable["status"] = True
                    
        except KeyboardInterrupt:
            pass
        finally:
            client.disconnect()
            print("Disconnected from the broker.")

class Thread2:
    def __init__(self, shared_data):
        self.name = "Thread 2"
        self.shared_data = shared_data

    def run(self):
        i = 0
        while True:
            with self.shared_data.event:
                if i >= 15:
                    self.shared_data.shared_variable["status"] = False
                    self.shared_data.shared_variable["data"] = {"name": "wilbroad"}
                    i = 0
            time.sleep(1)
            i+=1




def run_thread(obj):
    _thread.start_new_thread(obj.run, ())
shared_data = SharedData()
thread1 = Thread1(shared_data)
thread2 = Thread2(shared_data)
run_thread(thread1)
time.sleep(1)
run_thread(thread2)
try:
    while True:
        pass
except KeyboardInterrupt:
    pass
finally:
    _thread.exit()

