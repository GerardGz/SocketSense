// arduino_sorter/arduino_sorter.ino

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "HardwareController.h"

// Initialize the Servo Driver (default I2C address 0x40)
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Create our controller object, passing it the pwm driver
HardwareController controller = HardwareController(&pwm);

String inputString = ""; // A string to hold incoming data
bool stringComplete = false;

void setup() {
    Serial.begin(9600);
    Serial.println("Socket Sorter Arduino Booting Up...");

    pwm.begin();
    pwm.setPWMFreq(60); // Set frequency for servos
    
    Serial.println("Servo driver initialized. Waiting for commands from Python...");
}

void loop() {
    // Check if a command has been fully received
    if (stringComplete) {
        Serial.print("Received command: ");
        Serial.println(inputString);
        
        // --- Parse the "OPEN:1" command ---
        if (inputString.startsWith("OPEN:")) {
            // Get the servo ID number
            String idStr = inputString.substring(5);
            int servoID = idStr.toInt();

            if (servoID > 0) {
                // Call the controller action
                controller.executeSortAction(servoID);
            } else {
                Serial.println("Error: Invalid servo ID.");
            }
        }

        // Clear the string for the next command
        inputString = "";
        stringComplete = false;
    }
}

/**
 * @brief This function runs in the background.
 * It reads incoming serial data byte-by-byte.
 */
void serialEvent() {
    while (Serial.available()) {
        char inChar = (char)Serial.read();
        inputString += inChar;
        // The newline character '\n' (sent by Python)
        // marks the end of the command.
        if (inChar == '\n') {
            stringComplete = true;
        }
    }
}