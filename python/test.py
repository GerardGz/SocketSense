import serial
import time

# --- CONFIGURATION ---
ARDUINO_PORT = '/dev/ttyUSB0' # <-- Check this port on your Pi
BAUD_RATE = 9600
# ---------------------

print("Starting serial communication test...")

try:
    # Connect to the Arduino
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2) # 2-second timeout
    print(f"Connecting to {ARDUINO_PORT}...")
    
    # 1. Wait for Arduino to reset
    time.sleep(2) 
    print("Sending 'START' handshake...")
    
    # 2. Send the "START" command
    ser.write("START\n".encode('utf-8'))
    
    # 3. Wait for the "Handshake OK" reply
    response = ser.readline().decode('utf-8').strip()
    
    if "Handshake OK" in response:
        print(f"Arduino replied: {response}")
        print("--- Handshake successful. Ready to test commands. ---")
    else:
        print(f"Arduino sent an unexpected reply: {response}")
        print("--- Handshake FAILED. ---")
        exit()

    # 4. Start the user input loop
    while True:
        command = input("Enter command to send (or 'quit' to exit): ")
        
        if command.lower() == 'quit':
            break

        command_to_send = command + '\n'
        ser.write(command_to_send.encode('utf-8'))
        print(f"Sent: {command}")

        # Wait for and read the "Echo:" response
        response = ser.readline().decode('utf-8').strip()
        
        if response:
            print(f"Arduino replied: {response}")
        else:
            print("Arduino did not reply (timeout).")

except serial.SerialException as e:
    print(f"\n--- ERROR ---")
    print(f"Could not open port {ARDUINO_PORT}. {e}")

except KeyboardInterrupt:
    print("\nExiting test.")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print(f"Serial port {ARDUINO_PORT} closed.")