// Will contain logic for controlling servos and steppers

#include "HardwareController.h"
#include <iostream>

void HardwareController::executeSortAction(int angle) {
    // Rotate to the opening
    std::cout << "STEPPER: Rotating " << angle << " degrees." << std::endl;
    // stepper.rotate(angle);
    
    // Drop the socket
    std::cout << "SERVO: Opening drop mechanism." << std::endl;
    // delay(500); delay so there is enough time for socket to fall

    // Rotate back to original position
    std::cout << "STEPPER: Rotating " << -angle << " degrees." << std::endl;
    // stepper.rotate(-angle);
}