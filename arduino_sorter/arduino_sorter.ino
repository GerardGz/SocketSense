// arduino_sorter/arduino_sorter.ino

// --- Include ALL hardware libraries ---
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <AccelStepper.h>

// --- Include BOTH controller classes ---
#include "StepperController.h"
#include "ServoController.h"

// --- Stepper Config (for BOTH steppers) ---
const int STEPPER1_STEP_PIN = 3;
const int STEPPER1_DIR_PIN  = 4;
const int STEPPER2_STEP_PIN = 5;
const int STEPPER2_DIR_PIN  = 6;
const int STEPS_PER_REV = 200; // NEMA 17 default

// Create both stepper objects
AccelStepper stepper1 = AccelStepper(1, STEPPER1_STEP_PIN, STEPPER1_DIR_PIN);
AccelStepper stepper2 = AccelStepper(1, STEPPER2_STEP_PIN, STEPPER2_DIR_PIN);

// --- Servo Config ---
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// --- Create BOTH controller objects ---
// Pass both steppers to the StepperController
StepperController stepper_controller = StepperController(&stepper1, &stepper2, STEPS_PER_REV);
ServoController servo_controller = ServoController(&pwm);

// --- Serial Communication ---
String inputString = ""; // For commands from Pi (Serial)
bool stringComplete = false;
// Note: You would add a second string listener for your voice module,
// probably on Serial1 (pins 18, 19)

void setup() {
    // Serial port for the Raspberry Pi
    Serial.begin(9600); 
    Serial.println("Arduino booted. Waiting for 'START' command from Python..."); 

    while (true) {
        if (Serial.available()) {
            String msg = Serial.readStringUntil('\n');
            msg.trim(); // Remove any extra whitespace
            if (msg == "START") {
                // Send the "OK" reply back to Python
                Serial.println("Handshake OK. Initializing hardware...");
                break; // Exit this loop and continue setup()
            }
        }
        delay(100); // Don't spam the CPU
    } 
    
    // You might start a second serial port for the voice module
    // Serial1.begin(9600); 

    // Initialize Stepper 1
    stepper1.setMaxSpeed(1000);
    stepper1.setAcceleration(500);
    
    // Initialize Stepper 2
    stepper2.setMaxSpeed(500); // Slower for the drop
    stepper2.setAcceleration(200);
    Serial.println("Steppers initialized.");

    // Initialize Servo Driver
    pwm.begin();
    pwm.setPWMFreq(60); 
    Serial.println("Servo driver initialized.");
    
    Serial.println("Ready for commands...");
}

void loop() {
    // --- 1. Check for commands from the Raspberry Pi ---
    if (stringComplete) {
        Serial.print("Received command from Pi: ");
        Serial.println(inputString);
        
        parseCommand(inputString); // Process the command

        inputString = "";
        stringComplete = false;
    }
    
    // --- 2. Check for commands from the Voice Module ---
    // (Example of how you would listen to your voice module on different pins)
    /*
    while (Serial1.available()) {
        char inChar = (char)Serial1.read();
        if (inChar == '\n') {
            Serial.print("Received command from Voice: ");
            Serial.println(voiceInputString);
            parseCommand(voiceInputString);
            voiceInputString = "";
        } else {
            voiceInputString += inChar;
        }
    }
    */

    // AccelStepper's run() MUST be in the main loop to function
    stepper1.run();
    stepper2.run();
}

/**
 * @brief Parses a command string (e.g., "SORT:90" or "OPEN:1")
 * and calls the correct hardware controller.
 */
void parseCommand(String cmd) {
    int colonIndex = cmd.indexOf(':');
    
    if (colonIndex > 0) {
        String command = cmd.substring(0, colonIndex);
        String valueStr = cmd.substring(colonIndex + 1);
        int value = valueStr.toInt();

        if (command == "SORT") {
            // This is a blocking action. The loop will pause
            // while the steppers sort the socket.
            stepper_controller.executeSortAction(value);
        } else if (command == "OPEN") {
            // This is also blocking, but very fast.
            servo_controller.executeAction(value);
        } else {
            Serial.println("Error: Unknown command.");
        }
    } else {
        Serial.println("Error: Invalid command format.");
    }
}

// SerialEvent for the Raspberry Pi
void serialEvent() {
    while (Serial.available()) {
        char inChar = (char)Serial.read();
        inputString += inChar;
        if (inChar == '\n') {
            stringComplete = true;
        }
    }
}