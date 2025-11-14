#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H
#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>

class ServoController {
public:
    ServoController(Adafruit_PWMServoDriver* pwm_driver);
    void executeAction(int servoID);
private:
    Adafruit_PWMServoDriver* _pwm;
    int SERVOMIN;
    int SERVOMAX;
};
#endif