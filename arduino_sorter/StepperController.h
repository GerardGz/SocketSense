#ifndef STEPPER_CONTROLLER_H
#define STEPPER_CONTROLLER_H
#include <Arduino.h>
#include <AccelStepper.h>

class StepperController {
public:
    // Constructor now takes pointers to BOTH steppers
    StepperController(AccelStepper* stepper1, AccelStepper* stepper2, int steps_per_rev);
    
    // This is the main sorting action
    void executeSortAction(int angle); 

private:
    AccelStepper* _stepper1; // The bottom grid-selection stepper
    AccelStepper* _stepper2; // The top 360-spin stepper
    int _steps_per_rev;
    
    long angleToSteps(int angle);
};
#endif