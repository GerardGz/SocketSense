#ifndef HARDWARE_CONTROLLER_H
#define HARDWARE_CONTROLLER_H

#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>

class HardwareController {
public:
    // Constructor: Takes a pointer to the already-initialized driver
    HardwareController(Adafruit_PWMServoDriver* pwm_driver);

    // The main action command
    void executeSortAction(int servoID);

private:
    // A pointer to the servo driver
    Adafruit_PWMServoDriver* _pwm;

    // These are the pulse lengths for your servos (0 and 100 degrees)
    // You MUST tune these values for your specific servos!
    int SERVOMIN;
    int SERVOMAX;
};

#endif