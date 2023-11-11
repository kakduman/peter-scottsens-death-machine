import time
import serial
import threading

ser = serial.Serial('/dev/tty.usbserial-10', 9600, timeout=1)

def check_serial():
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            if line == "STOP":
                print("IT STOPPED")
        time.sleep(0.1)  # Check every 0.1 seconds

# Create a thread that runs the check_serial function
serial_thread = threading.Thread(target=check_serial)
serial_thread.daemon = True

# Start the thread
serial_thread.start()

while True:
    time.sleep(1)
    ser.write(f"{str(402)}\n".encode())
