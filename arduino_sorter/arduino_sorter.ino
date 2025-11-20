// arduino_sorter/arduino_sorter.ino

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
// Note: AccelStepper is NO LONGER NEEDED, but keeping the include won't hurt.

#include "StepperController.h"
#include "ServoController.h"

// --- Stepper Pin Config ---
// Make sure these match your actual wiring!
const int STEPPER1_STEP_PIN = 2;
const int STEPPER1_DIR_PIN  = 3;
const int STEPPER2_STEP_PIN = 4;
const int STEPPER2_DIR_PIN  = 5;

// --- Servo Config ---
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// --- Create Controllers ---
// NEW: We pass the PIN NUMBERS directly, not stepper objects
StepperController stepper_controller = StepperController(STEPPER1_STEP_PIN, STEPPER1_DIR_PIN, STEPPER2_STEP_PIN, STEPPER2_DIR_PIN);

ServoController servo_controller = ServoController(&pwm);

// --- Serial Config ---
String inputString = "";
bool stringComplete = false;

void setup() {
    Serial.begin(9600); 
    Serial.println("Arduino booted. Waiting for 'START'...");

    // Handshake Logic
    while (true) {
        if (Serial.available()) {
            String msg = Serial.readStringUntil('\n');
            msg.trim();
            if (msg == "START") {
                Serial.println("Handshake OK.");
                break; 
            }
        }
        delay(100); 
    }
    
    // Initialize Servo Driver
    pwm.begin();
    pwm.setPWMFreq(60); 
    Serial.println("System Ready.");
}

void loop() {
    if (stringComplete) {
        Serial.print("Received: ");
        Serial.println(inputString);
        parseCommand(inputString);
        inputString = "";
        stringComplete = false;
    }
    
    // Note: We NO LONGER need stepper.run() here 
    // because the movement functions are blocking loops.
}

void parseCommand(String cmd) {
    int colonIndex = cmd.indexOf(':');
    if (colonIndex > 0) {
        String command = cmd.substring(0, colonIndex);
        int value = cmd.substring(colonIndex + 1).toInt();

        if (command == "SORT") {
            stepper_controller.executeSortAction(value);
        } else if (command == "OPEN") {
            servo_controller.executeAction(value);
        } else {
            Serial.println("Error: Unknown command.");
        }
    }
}

void serialEvent() {
    while (Serial.available()) {
        char inChar = (char)Serial.read();
        inputString += inChar;
        if (inChar == '\n') stringComplete = true;
    }
}