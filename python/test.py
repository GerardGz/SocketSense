import serial
import time

# --- CONFIGURATION ---
# UPDATE THIS to match your Pi's port for the Arduino
# Linux/Pi: '/dev/ttyUSB0' or '/dev/ttyACM0'
# Windows: 'COM3'
ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
# ---------------------

print("Starting hardware test script...")
print("This will test the Arduino's 'SORT' command.")

try:
    # --- 1. Connect and Handshake ---
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    print(f"Connecting to {ARDUINO_PORT}...")
    
    # Wait for Arduino to reset
    time.sleep(2) 
    
    # Clear any "booting..." messages
    ser.reset_input_buffer()
    
    # Send the "START" handshake
    print("Sending 'START' handshake...")
    ser.write("START\n".encode('utf-8'))
    
    # Wait for the "Handshake OK" reply
    response = ser.readline().decode('utf-8').strip()
    
    if "Handshake OK" in response:
        print(f"Arduino replied: {response}")
        print("--- Handshake successful. Ready to send commands. ---")
    else:
        print(f"--- Handshake FAILED. ---")
        print(f"Arduino sent an unexpected reply: {response}")
        ser.close()
        exit()

    # --- 2. Command Loop ---
    while True:
        # Get command from user
        command = input("\nEnter command (e.g., SORT:90) or 'quit' to exit: ")
        
        if command.lower() == 'quit':
            break
            
        if not command:
            continue

        # Send the command to the Arduino
        command_to_send = command + '\n'
        ser.write(command_to_send.encode('utf-8'))
        print(f"Sent: {command}")
        
        # --- 3. Listen for ALL replies ---
        print("--- Arduino Replies ---")
        try:
            # Listen for 10 seconds (or until the Arduino stops talking)
            # This is because the stepper action is "blocking" and will
            # send multiple messages ("Moving...", "Complete...", "Homing...")
            
            # Set a timeout for this read operation
            start_time = time.time()
            while time.time() - start_time < 10.0: # 10-second timeout
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    if response:
                        print(response)
                else:
                    # If we got no data, check if we're done
                    if time.time() - start_time > 1.0: # Stop if 1 sec of silence
                        break 
        except Exception as e:
            print(f"Error while reading: {e}")
            
        print("-----------------------")

except serial.SerialException as e:
    print(f"\n--- FATAL ERROR ---")
    print(f"Could not open port {ARDUINO_PORT}. {e}")

except KeyboardInterrupt:
    print("\nShutting down by user command...")

finally:
    # --- 4. Clean up ---
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print(f"Serial port {ARDUINO_PORT} closed. Goodbye.")