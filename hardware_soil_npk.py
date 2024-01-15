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
        if message:
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
        self.uart = machine.UART(1, baudrate=4800, tx=17, rx=16)
        self.shared_data = shared_data
        self.time_copy = time.time()
        self.interval = 10 # seconds
    
    def read_sensor(self):
        query_data = bytearray([0x01, 0x03, 0x00, 0x00, 0x00, 0x07, 0x04, 0x08])
        self.uart.write(query_data)
        time.sleep(0.1)
        received_data = self.uart.read(19)
        if received_data:
            h = (received_data[3] << 8) | received_data[4]
            t = (received_data[5] << 8) | received_data[6]
            ec = (received_data[7] << 8) | received_data[8]
            ph = (received_data[9] << 8) | received_data[10]
            n = (received_data[11] << 8) | received_data[12]
            p = (received_data[13] << 8) | received_data[14]
            k = (received_data[15] << 8) | received_data[16]      
            return (float(h) / 10.0, float(t) / 10.0, ec, float(ph) / 10.0, n, p, k )
    
    def prepare_publish_data(self):
        try:
            with self.shared_data.event:
                self.shared_data.shared_variable["status"] = False
                data = self.read_sensor()
                self.shared_data.shared_variable["data"] = {
                    "id": 1,
                    "name": "Sitting Room",
                    "data" : {
                            "Humidity"    : data[0],
                            "Temperature" : data[1],
                            "Conductivity": data[2],
                            "Ph"          : data[3],
                            "Nitrogen"    : data[4],
                            "Phosphorous" : data[5],
                            "Potassium"   : data[6],
                        }    
                    }
        except Exception as e:
            print("Error =>", e)
        
    def run(self):
        while(True):
            if  (time.time() - self.time_copy) >= self.interval:
                self.prepare_publish_data()
                self.time_copy = time.time()
    


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



