#include "FlowEngine.h"
#include <iostream>
#include <string>
#include <cstdarg>

// NVIDIA Flow
#include "nvflowext/NvFlowLoader.h"
#include "nvflowext/shaders/NvFlowRayMarchParams.h"

// OpenVDB & NanoVDB
#include <openvdb/openvdb.h>
#include <openvdb/tools/Dense.h>
#include <nanovdb/NanoVDB.h>
#include <nanovdb/util/NanoToOpenVDB.h>

struct FlowEngine::Impl {
    NvFlowLoader loader = {};
    NvFlowContextInterface contextInterface = {};
    NvFlowDeviceManager* deviceManager = nullptr;
    NvFlowDevice* device = nullptr;
    NvFlowDeviceQueue* deviceQueue = nullptr;
    NvFlowGrid* grid = nullptr;
    NvFlowGridParamsNamed* gridParamsNamed = nullptr;

    bool valid = false;

    static void flowLoaderError(const char* str, void* userdata) {
        std::cerr << "Flow Error: " << str << std::endl;
    }

    static void logPrint(NvFlowLogLevel level, const char* format, ...) {
        va_list args;
        va_start(args, format);
        char buf[512];
        vsnprintf(buf, sizeof(buf), format, args);
        if (level == eNvFlowLogLevel_error) std::cerr << "FlowError: " << buf << std::endl;
        else if (level == eNvFlowLogLevel_warning) std::cout << "FlowWarn: " << buf << std::endl;
        else std::cout << "FlowInfo: " << buf << std::endl;
        va_end(args);
    }
};

FlowEngine::FlowEngine() : m_impl(new Impl()) {}

FlowEngine::~FlowEngine() {
    if (m_impl->valid) {
        NvFlowContext* context = m_impl->loader.deviceInterface.getContext(m_impl->deviceQueue);
        m_impl->loader.deviceInterface.waitIdle(m_impl->deviceQueue);
        
        m_impl->loader.gridInterface.destroyGrid(context, m_impl->grid);
        m_impl->loader.gridParamsInterface.destroyGridParamsNamed(m_impl->gridParamsNamed);
        
        NvFlowUint64 flushedFrameID = 0;
        m_impl->loader.deviceInterface.flush(m_impl->deviceQueue, &flushedFrameID, nullptr, nullptr);
        m_impl->loader.deviceInterface.waitIdle(m_impl->deviceQueue);
        
        m_impl->loader.deviceInterface.destroyDevice(m_impl->deviceManager, m_impl->device);
        m_impl->loader.deviceInterface.destroyDeviceManager(m_impl->deviceManager);
    }
    NvFlowLoaderDestroy(&m_impl->loader);
    delete m_impl;
}

bool FlowEngine::init() {
    openvdb::initialize();

    // Initialize Vulkan context (GPU simulation)
    NvFlowLoaderInitDeviceAPI(&m_impl->loader, Impl::flowLoaderError, nullptr, eNvFlowContextApi_vulkan);

    if (!m_impl->loader.module_nvflow || !m_impl->loader.module_nvflowext) {
        std::cerr << "Failed to load NVIDIA Flow libraries." << std::endl;
        return false;
    }

    std::cout << "  Creating device manager..." << std::endl;
    m_impl->deviceManager = m_impl->loader.deviceInterface.createDeviceManager(NV_FLOW_TRUE, nullptr, 0u);
    NvFlowDeviceDesc deviceDesc = {};
    deviceDesc.deviceIndex = 0;
    deviceDesc.enableExternalUsage = NV_FLOW_FALSE;
    deviceDesc.logPrint = Impl::logPrint;

    std::cout << "  Creating device..." << std::endl;
    m_impl->device = m_impl->loader.deviceInterface.createDevice(m_impl->deviceManager, &deviceDesc);
    
    std::cout << "  Getting device queue..." << std::endl;
    m_impl->deviceQueue = m_impl->loader.deviceInterface.getDeviceQueue(m_impl->device);
    NvFlowContextInterface_duplicate(&m_impl->contextInterface, m_impl->loader.deviceInterface.getContextInterface(m_impl->deviceQueue));

    NvFlowContext* context = m_impl->loader.deviceInterface.getContext(m_impl->deviceQueue);

    NvFlowGridDesc gridDesc = NvFlowGridDesc_default;
    gridDesc.maxLocations = 4096;

    std::cout << "  Creating grid..." << std::endl;
    m_impl->grid = m_impl->loader.gridInterface.createGrid(&m_impl->contextInterface, context, m_impl->loader.opList_orig, m_impl->loader.extOpList_orig, &gridDesc);
    
    std::cout << "  Creating grid params..." << std::endl;
    m_impl->gridParamsNamed = m_impl->loader.gridParamsInterface.createGridParamsNamed("flowUsd");

    std::cout << "  Init done." << std::endl;

    m_impl->valid = true;
    return true;
}

void FlowEngine::step(float deltaTime, int frameIndex) {
    if (!m_impl->valid) return;

    NvFlowContext* context = m_impl->loader.deviceInterface.getContext(m_impl->deviceQueue);

    // Setup simulation parameters for this frame
    static NvFlowGridSimulateLayerParams testSimulate = NvFlowGridSimulateLayerParams_default;
    static NvFlowGridEmitterSphereParams testSpheres = NvFlowEmitterSphereParams_default;
    static NvFlowGridOffscreenLayerParams testOffscreen = NvFlowGridOffscreenLayerParams_default;
    static NvFlowGridRenderLayerParams testRender = NvFlowGridRenderLayerParams_default;
    
    // Enable NanoVDB export and readback so we can pull data from Flow
    testSimulate.nanoVdbExport.enabled = NV_FLOW_TRUE;
    testSimulate.nanoVdbExport.readbackEnabled = NV_FLOW_TRUE;

    testSpheres.position = {0.0f, 0.0f, 0.0f};
    testSpheres.radius = 10.0f;
    testSpheres.temperature = 1.0f;
    testSpheres.fuel = 1.0f;
    testSpheres.velocity = {0.0f, 10.0f, 0.0f};

    static NvFlowGridSimulateLayerParams* pTestSimulate = &testSimulate;
    static NvFlowGridEmitterSphereParams* pTestSpheres = &testSpheres;
    static NvFlowGridOffscreenLayerParams* pTestOffscreen = &testOffscreen;
    static NvFlowGridRenderLayerParams* pTestRender = &testRender;
    static NvFlowUint64 version = 1u;

    static NvFlowDatabaseTypeSnapshot typeSnapshots[4u] = {
        {version, &NvFlowGridSimulateLayerParams_NvFlowReflectDataType,  (NvFlowUint8**)&pTestSimulate,  1u},
        {version, &NvFlowGridEmitterSphereParams_NvFlowReflectDataType,  (NvFlowUint8**)&pTestSpheres,   1u},
        {version, &NvFlowGridOffscreenLayerParams_NvFlowReflectDataType, (NvFlowUint8**)&pTestOffscreen, 1u},
        {version, &NvFlowGridRenderLayerParams_NvFlowReflectDataType,    (NvFlowUint8**)&pTestRender,    1u}
    };
    static NvFlowDatabaseSnapshot snapshot = { version, typeSnapshots, 4u };
    
    double absoluteSimTime = (double)(frameIndex * deltaTime);
    NvFlowGridParamsDescSnapshot gridParamsDescSnapshot = { snapshot, absoluteSimTime, deltaTime, NV_FLOW_FALSE, nullptr, 0u };

    std::cout << "  Mapping params named..." << std::endl;
    NvFlowGridParams* gridParams = m_impl->loader.gridParamsInterface.mapGridParamsNamed(m_impl->gridParamsNamed);
    
    std::cout << "  Committing params..." << std::endl;
    m_impl->loader.gridParamsInterface.commitParams(gridParams, &gridParamsDescSnapshot);

    // Simulate
    std::cout << "  Simulating..." << std::endl;
    NvFlowGridParamsDesc gridParamsDesc = {};
    NvFlowGridParamsSnapshot* paramsSnapshot = m_impl->loader.gridParamsInterface.getParamsSnapshot(gridParams, absoluteSimTime, 0llu);
    if (m_impl->loader.gridParamsInterface.mapParamsDesc(gridParams, paramsSnapshot, &gridParamsDesc)) {
        std::cout << "    calling simulate()... context=" << context << ", grid=" << m_impl->grid << ", simulate=" << (void*)m_impl->loader.gridInterface.simulate << std::endl;
        if (context && m_impl->grid && m_impl->loader.gridInterface.simulate) {
            m_impl->loader.gridInterface.simulate(context, m_impl->grid, &gridParamsDesc, NV_FLOW_FALSE);
        } else {
            std::cout << "    ERROR: Null pointer detected!" << std::endl;
        }
        m_impl->loader.gridParamsInterface.unmapParamsDesc(gridParams, paramsSnapshot);
    }

    std::cout << "  Flushing..." << std::endl;
    // Ensure CPU sync
    NvFlowUint64 flushedFrameID = 0;
    m_impl->loader.deviceInterface.flush(m_impl->deviceQueue, &flushedFrameID, nullptr, nullptr);
    std::cout << "  Waiting for frame..." << std::endl;
    m_impl->loader.deviceInterface.waitForFrame(m_impl->deviceQueue, flushedFrameID);

    std::cout << "  Extracting NanoVDB data..." << std::endl;
    // Extract NanoVDB data
    NvFlowGridRenderData renderData = {};
    m_impl->loader.gridInterface.getRenderData(context, m_impl->grid, &renderData);

    uint8_t* temperatureData = nullptr;
    uint8_t* smokeData = nullptr;
    
    NvFlowUint64 lastCompletedFrame = m_impl->contextInterface.getLastFrameCompleted(context);
    if (renderData.nanoVdb.readbackCount > 0u) {
        for (NvFlowUint64 idx = renderData.nanoVdb.readbackCount - 1u; idx < renderData.nanoVdb.readbackCount; idx--) {
            const auto readback = renderData.nanoVdb.readbacks + idx;
            if (lastCompletedFrame >= readback->globalFrameCompleted) {
                temperatureData = readback->temperatureNanoVdbReadback;
                smokeData = readback->smokeNanoVdbReadback;
                break;
            }
        }
    }

    // Write to OpenVDB
    if (temperatureData || smokeData) {
        openvdb::GridPtrVec grids;

        if (smokeData) {
            auto* nanoGrid = reinterpret_cast<const nanovdb::NanoGrid<float>*>(smokeData);
            if (nanoGrid && nanoGrid->isValid()) {
                auto vdbGrid = nanovdb::tools::nanoToOpenVDB(*nanoGrid);
                vdbGrid->setName("density");
                grids.push_back(vdbGrid);
            }
        }
        
        if (temperatureData) {
            auto* nanoGrid = reinterpret_cast<const nanovdb::NanoGrid<float>*>(temperatureData);
            if (nanoGrid && nanoGrid->isValid()) {
                auto vdbGrid = nanovdb::tools::nanoToOpenVDB(*nanoGrid);
                vdbGrid->setName("temperature");
                grids.push_back(vdbGrid);
            }
        }

        if (!grids.empty()) {
            char filename[256];
            snprintf(filename, sizeof(filename), "frame_%04d.vdb", frameIndex);
            
            openvdb::io::File file(filename);
            file.write(grids);
            file.close();
            
            std::cout << "Wrote " << filename << std::endl;
        }
    }
}
