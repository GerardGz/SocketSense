// Will control the main flow for c++ of taking angle and executing rotation
// Will handle dropping of socket also (python will probably handle voice)

#include <iostream>
#include <string>
#include <sstream>
#include "HardwareController.h" 

int main() {
    HardwareController controller; // class that controls steppers/servos
    std::string line;

    // Continuously read lines from standard input (from Python)
    while (std::getline(std::cin, line)) {
        std::stringstream ss(line);
        std::string command;
        
        // Parse the "COMMAND:VALUE" format
        if (std::getline(ss, command, ':')) {
            if (command == "ROTATE") { 
                int angle;
                std::string value;
                
                if (std::getline(ss, value)) {
                    try {
                        angle = std::stoi(value);
                        
                        std::cout << "C++ Received: Rotate " << angle << " degrees." << std::endl;
                        controller.executeSortAction(angle);
                        
                    } catch (const std::exception& e) {
                        std::cerr << "C++ Error: Invalid angle format." << std::endl;
                    }
                }
            }
        }
    }
    return 0;
}