#include "ServoController.h"

ServoController::ServoController(Adafruit_PWMServoDriver* pwm_driver) {
    _pwm = pwm_driver;
    SERVOMIN = 150; // Tune this
    SERVOMAX = 400; // Tune this
}

void ServoController::executeAction(int servoID) {
    int servoChannel = servoID - 1; 
    Serial.print("SERVO: Activating flap for servo ID ");
    Serial.println(servoID);

    _pwm->setPWM(servoChannel, 0, SERVOMAX); // Open
    delay(1000);
    _pwm->setPWM(servoChannel, 0, SERVOMIN); // Close
    
    Serial.println("SERVO: Flap cycle complete.");
}