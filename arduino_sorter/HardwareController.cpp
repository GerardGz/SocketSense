// arduino_sorter/HardwareController.cpp

#include "HardwareController.h"

// Constructor
HardwareController::HardwareController(Adafruit_PWMServoDriver* pwm_driver) {
    _pwm = pwm_driver; // Store the pointer to the driver

    // --- TUNE THESE VALUES ---
    // This is the pulse width, in "ticks", for your servo
    // (out of 4096 total).
    // 150 = approx 0 degrees
    // 600 = approx 180 degrees
    SERVOMIN = 150; // Example: 0 degrees
    SERVOMAX = 400; // Example: 100 degrees
}

// The main action
void HardwareController::executeSortAction(int servoID) {
    // The servoID from Python (1, 2, 3, 4) must map to the
    // servo driver channel (0-15). Let's assume servo 1 = channel 0, etc.
    int servoChannel = servoID - 1;

    Serial.print("Executing action for Servo ID ");
    Serial.println(servoID);

    // --- This is the flap logic ---
    const int HOLD_TIME_MS = 1000;

    // 1. Open the flap (move to 100 degrees)
    Serial.println("Opening flap...");
    _pwm->setPWM(servoChannel, 0, SERVOMAX);
    
    // 2. Hold for the socket to drop
    delay(HOLD_TIME_MS);

    // 3. Close the flap (move back to 0 degrees)
    Serial.println("Closing flap.");
    _pwm->setPWM(servoChannel, 0, SERVOMIN);
}