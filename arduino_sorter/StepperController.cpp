#include "StepperController.h"

StepperController::StepperController(AccelStepper* s1, AccelStepper* s2, int steps_per_rev) {
    _stepper1 = s1;
    _stepper2 = s2;
    _steps_per_rev = steps_per_rev;
}

// --- HELPER FUNCTION IS UNCHANGED ---
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
    _stepper1->runToPosition(); // Blocks until Stepper 1 is in position
    
    Serial.println("STEPPER 1: In position.");

    // --- 2. Spin Stepper 2 (Top) one full 360 to drop ---
    Serial.println("STEPPER 2: Beginning 360 drop spin.");
    
    // Tell Stepper 2 to move 360 degrees from its current position.
    _stepper2->move(_steps_per_rev); 
    
    // This blocks until Stepper 2 completes its full rotation
    _stepper2->runToPosition();

    Serial.println("STEPPER 2: Drop complete.");

    // --- 3. NEW: Return BOTH steppers to home (0 degrees) ---
    Serial.println("HOMING: Returning both steppers to 0.");

    // Tell Stepper 1 to go home
    _stepper1->moveTo(0);
    
    // Tell Stepper 2 to go home (it will spin 360 degrees back)
    _stepper2->moveTo(0); 

    // Wait for them to get there. We must block and run them
    // sequentially so they finish before the next command.
    
    // Stepper 1 runs home:
    Serial.println("HOMING: Stepper 1 returning...");
    _stepper1->runToPosition();
    Serial.println("HOMING: Stepper 1 at 0.");
    
    // Stepper 2 runs home:
    Serial.println("HOMING: Stepper 2 returning...");
    _stepper2->runToPosition();
    Serial.println("HOMING: Stepper 2 at 0.");

    Serial.println("--- Sort Action Finished. Ready for next. ---");
}