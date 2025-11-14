#include "StepperController.h"

StepperController::StepperController(AccelStepper* s1, AccelStepper* s2, int steps_per_rev) {
    _stepper1 = s1;
    _stepper2 = s2;
    _steps_per_rev = steps_per_rev;
}

// Helper to convert degrees to steps
long StepperController::angleToSteps(int angle) {
    return (long)((angle / 360.0) * _steps_per_rev);
}

/**
 * @brief This function executes the full, multi-step sorting process.
 * It is "blocking," meaning the Arduino will wait until it's done.
 */
void StepperController::executeSortAction(int angle) {
    Serial.println("--- Starting Sort Action ---");

    // --- 1. Move Stepper 1 (Bottom) to the grid location ---
    Serial.print("STEPPER 1: Moving to ");
    Serial.print(angle);
    Serial.println(" degrees.");
    
    long stepsToMove = angleToSteps(angle);
    _stepper1->moveTo(stepsToMove);
    
    // This blocks until Stepper 1 is in position
    // The main loop() continues to call .run()
    _stepper1->runToPosition();
    
    Serial.println("STEPPER 1: In position.");

    // --- 2. Spin Stepper 2 (Top) one full 360 to drop ---
    Serial.println("STEPPER 2: Beginning 360 drop spin.");
    
    // Tell Stepper 2 to move 360 degrees (e.g., 200 steps)
    // from its current position.
    _stepper2->move(_steps_per_rev); 
    
    // This blocks until Stepper 2 completes its full rotation
    _stepper2->runToPosition();

    Serial.println("STEPPER 2: Drop complete.");

    // --- 3. Return Stepper 2 to its home position (optional) ---
    // We can just set its current position back to 0.
    // Or, if it has a home switch, we'd run a homing routine.
    _stepper2->setCurrentPosition(0);
    
    Serial.println("--- Sort Action Finished ---");
}