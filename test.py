from machine import UART
import time

uart = UART(1, baudrate=4800, tx=17, rx=16)

def read_sensor_data():
    query_data = bytearray([0x01, 0x03, 0x00, 0x00, 0x00, 0x07, 0x04, 0x08])
    uart.write(query_data)
    time.sleep(0.1)
    received_data = uart.read(19)

    if received_data:
        h = (received_data[3] << 8) | received_data[4]
        t = (received_data[5] << 8) | received_data[6]
        ec = (received_data[7] << 8) | received_data[8]
        ph = (received_data[9] << 8) | received_data[10]
        n = (received_data[11] << 8) | received_data[12]
        p = (received_data[13] << 8) | received_data[14]
        k = (received_data[15] << 8) | received_data[16]

        print("Humidity:", float(h) / 10.0)
        print("Temperature:", float(t) / 10.0)
        print("Conductivity:", ec)
        print("Ph:", float(ph) / 10.0)
        print("Nitrogen:", n)
        print("Phosphorous:", p)
        print("Potassium:", k)
        print("\n\n")

while True:
    read_sensor_data()
    time.sleep(2)
