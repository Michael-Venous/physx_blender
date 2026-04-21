#include "FlowEngine.h"
#include <iostream>

int main() {
    std::cout << "Initializing NVIDIA Flow Minimal App..." << std::endl;
    
    FlowEngine engine;
    if (!engine.init()) {
        std::cerr << "Engine initialization failed!" << std::endl;
        return 1;
    }
    
    std::cout << "Running Simulation Loop..." << std::endl;
    
    // Simulate 50 frames
    const int numFrames = 50;
    const float fps = 60.0f;
    const float deltaTime = 1.0f / fps;
    
    for (int i = 0; i < numFrames; ++i) {
        std::cout << "Simulating Frame " << i << "..." << std::endl;
        engine.step(deltaTime, i);
    }
    
    std::cout << "Simulation Complete." << std::endl;
    return 0;
}
