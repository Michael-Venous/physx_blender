#pragma once

#include <vector>
#include <string>

class FlowEngine {
public:
    FlowEngine();
    ~FlowEngine();

    bool init();
    void step(float deltaTime, int frameIndex);

private:
    struct Impl;
    Impl* m_impl;
};
