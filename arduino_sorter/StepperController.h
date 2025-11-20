#ifndef STEPPER_CONTROLLER_H
#define STEPPER_CONTROLLER_H
#include <Arduino.h>

class StepperController {
public:
    StepperController(int s1_step, int s1_dir, int s2_step, int s2_dir);
    void executeSortAction(int angle); 

private:
    int _s1_step_pin;
    int _s1_dir_pin;
    int _s2_step_pin;
    int _s2_dir_pin;
    
    long angleToSteps(int angle);

    // NEW: Added 'speedDelay' parameter
    void stepMotor(int stepPin, int steps, int speedDelay);
};
#endif