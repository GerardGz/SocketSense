// Defines what our hardware can do (no implementations just declarations)
// idk how to do this part

#ifndef HARDWARE_CONTROLLER_H
#define HARDWARE_CONTROLLER_H


class HardwareController {
public:
    // --- Public Interface ---
    // These are the functions that main.cpp is allowed to see and call.

    /**
     * @brief Constructor: This function is called once, when the 
     * HardwareController object is first created.
     * Use this to set up your GPIO pins and initialize hardware.
     */
    HardwareController();

    /**
     * @brief Destructor: This function is called once, when the 
     * program is closing.
     * Use this to safely shut down hardware and release pins.
     */
    ~HardwareController();

    /**
     * @brief The main action command.
     * @param angle The specific angle (in degrees) to rotate to.
     */
    void executeSortAction(int angle);

private:
    // --- Private Members ---
    // These are internal variables and helper functions that main.cpp
    // does NOT need to know about. They are for internal use only.

    // Example: Store the pin numbers for your hardware
    int stepper_pin_1;
    int stepper_pin_2;
    int servo_pin;

    /**
     * @brief A private helper function for the constructor to use.
     * Keeps the constructor clean.
     */
    void initializeHardware();
};

#endif // HARDWARE_CONTROLLER_H