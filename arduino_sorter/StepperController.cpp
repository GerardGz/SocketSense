#include "StepperController.h"

StepperController::StepperController(int s1_step, int s1_dir, int s2_step, int s2_dir) {
    _s1_step_pin = s1_step;
    _s1_dir_pin  = s1_dir;
    _s2_step_pin = s2_step;
    _s2_dir_pin  = s2_dir;

    pinMode(_s1_step_pin, OUTPUT);
    pinMode(_s1_dir_pin, OUTPUT);
    pinMode(_s2_step_pin, OUTPUT);
    pinMode(_s2_dir_pin, OUTPUT);
}

long StepperController::angleToSteps(int angle) {
    return (long)((angle / 360.0) * 200.0);
}

// --- UPDATED PULSE FUNCTION ---
// Now accepts 'speedDelay'. 
// Lower number = Faster (Low Torque)
// Higher number = Slower (High Torque)
void StepperController::stepMotor(int stepPin, int steps, int speedDelay) {
    for (int i = 0; i < steps; i++) {
        digitalWrite(stepPin, HIGH);
        delayMicroseconds(speedDelay); 
        digitalWrite(stepPin, LOW);
        delayMicroseconds(speedDelay);
    }
}

void StepperController::executeSortAction(int angle) {
    Serial.println("--- Starting Sort Action ---");

    int s1_steps = angleToSteps(angle);

    // --- Phase 1: Stepper 1 moves (Keep it FAST) ---
    Serial.print("STEPPER 1: Moving steps: ");
    Serial.println(s1_steps);
    digitalWrite(_s1_dir_pin, LOW); 
    
    // 700 is fast (good for the lightweight sorting grid)
    stepMotor(_s1_step_pin, s1_steps, 700); 
    
    delay(500);

    // --- Phase 2: Stepper 2 spins 360 (Make it SLOW & STRONG) ---
    Serial.println("STEPPER 2: Spinning 360.");
    digitalWrite(_s2_dir_pin, LOW); 
    
    // 2000 is slow (very high torque for the drop mechanism)
    // If 2000 is too slow, try 1500. If it still skips, try 2500.
    stepMotor(_s2_step_pin, 200, 700); 
    
    delay(500); 

    // --- Phase 3: Stepper 1 returns (Keep it FAST) ---
    Serial.println("STEPPER 1: Returning Home.");
    digitalWrite(_s1_dir_pin, HIGH); 
    stepMotor(_s1_step_pin, s1_steps, 700); 

    Serial.println("--- Sort Action Complete ---");
}