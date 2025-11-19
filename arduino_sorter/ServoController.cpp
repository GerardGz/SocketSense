#include "ServoController.h"

ServoController::ServoController(Adafruit_PWMServoDriver* pwm_driver) {
    _pwm = pwm_driver;
    ORIGINAL_PULSE = 300; // Tune this
    ACTIVATED_PULSE = 115; // Tune this
}

void ServoController::executeAction(int servoID) {
    int servoChannel = servoID - 1; 
    Serial.print("SERVO: Activating flap for servo ID ");
    Serial.println(servoID);

    _pwm->setPWM(servoChannel, 0, ACTIVATED_PULSE); // Open
    delay(1000);
    _pwm->setPWM(servoChannel, 0, ORIGINAL_PULSE); // Close
    
    Serial.println("SERVO: Flap cycle complete.");
}