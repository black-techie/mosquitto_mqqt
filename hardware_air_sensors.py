import _thread
from umqtt.simple import MQTTClient
import machine
import network
import time
import json
import aht

class SharedData:
    def __init__(self):
        self.shared_variable = {
                "data" : {},
                "status": True
            }
        self.event = _thread.allocate_lock()

class Comm:
    def __init__(self, shared_data):
        self.name = "Thread 1"
        self.shared_data = shared_data
        self.mqtt_broker = "192.168.1.102"
        self.mqtt_port = 1883
        self.mqtt_topic = b"test_topic"
        self.wifi_ssid = "TP-Link_0772"
        self.wifi_password = "39222480"
        self.client = None
    
    def connect_to_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print("Connecting to WiFi...")
            wlan.connect(self.wifi_ssid, self.wifi_password)
            while not wlan.isconnected():
                time.sleep(1)
            print("Connected to WiFi")
            
    def connect_to_broker(self):
        self.connect_to_wifi()
        unique_id_bytes = machine.unique_id()
        unique_id_hex = ''.join(['{:02X}'.format(b) for b in unique_id_bytes])
        client_id = "esp32-" + unique_id_hex
        self.client = MQTTClient(client_id, self.mqtt_broker, port=self.mqtt_port)
        self.client.set_callback(self.on_message)
        try:
            self.client.connect()
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            machine.reset()    
        self.client.subscribe(self.mqtt_topic)
        print(f"Subscribed to topic: {self.mqtt_topic}")
        return True      
    def publish_message(self,client, message):
        try:
            client.publish(self.mqtt_topic, json.dumps(message))
            print(f"Published: {message}")
        except Exception as e:
            print(f"Error publishing message: {e}")
    def on_message(self, topic, message):
        print(f"Received message on topic {topic}: {message}")
    def run(self):
        try:
            is_connected =self.connect_to_broker()
            while is_connected:
                self.client.check_msg()
                if self.shared_data.shared_variable["status"] == False:
                    self.publish_message(self.client, self.shared_data.shared_variable["data"])
                    self.shared_data.shared_variable["status"] = True          
        except KeyboardInterrupt:
            pass
        finally:
            self.client.disconnect()
            print("Disconnected from the broker.")


class Main:
    def __init__(self, shared_data):
        self.name = "Main"
        self.i2c = machine.I2C(1,scl=machine.Pin(22), sda=machine.Pin(21))
        self.sensor = aht.AHT2x(self.i2c, crc=True)
        self.shared_data = shared_data
        self.time_copy = time.time()
        self.CO = machine.ADC(34)
        self.NH3 = machine.ADC(35)
        self.NO2 = machine.ADC(32)
        self.interval = 20 # seconds

    def run(self):
        data =  {
                    "CO" : [],
                    "NH3": [],
                    "NO2": [],
                    "TMP": [],
                    "HUM": [],
                    }
        while(self.sensor.is_ready):
            data["CO"].append((self.CO.read_u16()*100)/65535)
            data["NH3"].append((self.NH3.read_u16()*100)/65535)
            data["NO2"].append((self.NO2.read_u16()*100)/65535)
            data["TMP"].append(self.sensor.temperature)
            data["HUM"].append(self.sensor.humidity)
            try:
                with self.shared_data.event:
                    if  (time.time() - self.time_copy) >= self.interval:
                        self.shared_data.shared_variable["status"] = False
                        self.shared_data.shared_variable["data"] = {
                            "id": 1,
                            "name": "Sitting Room",
                            "data" : {
                                    "CO" : ( sum(data["CO"]) / len(data["CO"]) ),
                                    "NH3": ( sum(data["NH3"]) / len(data["NH3"]) ),
                                    "NO2": ( sum(data["NO2"]) / len(data["NO2"]) ),
                                    "TMP": ( sum(data["TMP"]) / len(data["TMP"]) ),
                                    "HUM": ( sum(data["HUM"]) / len(data["HUM"]) ),       
                            }    
                        }
                        data =  {
                                "CO" : [],
                                "NH3": [],
                                "NO2": [],
                                "TMP": [],
                                "HUM": [],
                        }
                        self.time_copy = time.time()
            except Exception as e:
                print(e)
    


shared_data = SharedData()
communication = Comm(shared_data)
main = Main(shared_data)

_thread.start_new_thread(communication.run, ())
time.sleep(0.5)
_thread.start_new_thread(main.run, ())

try:
    while True:
        pass

except KeyboardInterrupt:
    pass

finally:
    _thread.exit()


