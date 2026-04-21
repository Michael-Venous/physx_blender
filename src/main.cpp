#include <fstream>
#include <iostream>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "nvflowext/NvFlowLoader.h"
#include "nvflowext/shaders/NvFlowRayMarchParams.h"

static void flowLoaderError(const char *str, void *userdata) {
  std::cerr << "Flow Error: " << str << std::endl;
}

static void logPrint(NvFlowLogLevel level, const char *format, ...) {
  va_list args;
  va_start(args, format);
  char buf[256u];
  buf[0u] = '\0';
  if (level == eNvFlowLogLevel_error) {
    vsnprintf(buf, 256u, format, args);
    std::cerr << "FlowError: " << buf << std::endl;
  } else if (level == eNvFlowLogLevel_warning) {
    vsnprintf(buf, 256u, format, args);
    std::cerr << "FlowWarn: " << buf << std::endl;
  } else if (level == eNvFlowLogLevel_info) {
    vsnprintf(buf, 256u, format, args);
    std::cout << "FlowInfo: " << buf << std::endl;
  }
  va_end(args);
}

int main() {
  NvFlowLoader loader = {};
  NvFlowLoaderInitDeviceAPI(&loader, flowLoaderError, nullptr,
                            eNvFlowContextApi_vulkan);

  if (!loader.module_nvflow || !loader.module_nvflowext) {
    std::cerr << "Failed to load NVIDIA Flow" << std::endl;
    return 1;
  }

  std::cout << "Creating Device Manager" << std::endl;
  NvFlowDeviceManager *deviceManager =
      loader.deviceInterface.createDeviceManager(NV_FLOW_FALSE, nullptr, 0u);
  NvFlowDeviceDesc deviceDesc = {};
  deviceDesc.deviceIndex = 0;
  deviceDesc.enableExternalUsage = NV_FLOW_FALSE;
  deviceDesc.logPrint = logPrint;

  std::cout << "Creating Device" << std::endl;
  NvFlowDevice *device =
      loader.deviceInterface.createDevice(deviceManager, &deviceDesc);

  std::cout << "Getting Device Queue" << std::endl;
  NvFlowDeviceQueue *deviceQueue =
      loader.deviceInterface.getDeviceQueue(device);

  NvFlowContextInterface contextInterface = {};
  NvFlowContextInterface_duplicate(
      &contextInterface,
      loader.deviceInterface.getContextInterface(deviceQueue));
  NvFlowContext *context = loader.deviceInterface.getContext(deviceQueue);

  std::cout << "Creating Grid" << std::endl;
  NvFlowGridDesc gridDesc = NvFlowGridDesc_default;
  NvFlowGrid *grid = loader.gridInterface.createGrid(
      &contextInterface, context, loader.opList_orig, loader.extOpList_orig,
      &gridDesc);

  std::cout << "Creating Grid Params Named" << std::endl;
  NvFlowGridParamsNamed *gridParamsNamed =
      loader.gridParamsInterface.createGridParamsNamed("flowUsd");

  NvFlowGridParams *paramSrc =
      loader.gridParamsInterface.mapGridParamsNamed(gridParamsNamed);

  std::cout << "Running barebones prototype..." << std::endl;

  for (uint32_t frame = 0; frame < 60; frame++) {
    static NvFlowGridSimulateLayerParams testSimulate =
        NvFlowGridSimulateLayerParams_default;
    static NvFlowGridEmitterSphereParams testSpheres =
        NvFlowEmitterSphereParams_default;
    static NvFlowGridOffscreenLayerParams testOffscreen =
        NvFlowGridOffscreenLayerParams_default;
    static NvFlowGridRenderLayerParams testRender =
        NvFlowGridRenderLayerParams_default;

    testSimulate.nanoVdbExport.enabled = NV_FLOW_TRUE;
    testSimulate.nanoVdbExport.readbackEnabled = NV_FLOW_TRUE;
    testSimulate.nanoVdbExport.smokeEnabled = NV_FLOW_TRUE;

    testSpheres.position = {0.0f, 0.0f, 0.0f};
    testSpheres.radius = 10.0f;
    testSpheres.temperature = 1.0f;
    testSpheres.fuel = 0.0f;
    testSpheres.smoke = 1.0f;
    testSpheres.velocity = {0.0f, 10.0f, 0.0f};

    static NvFlowGridSimulateLayerParams *pTestSimulate = &testSimulate;
    static NvFlowGridEmitterSphereParams *pTestSpheres = &testSpheres;
    static NvFlowGridOffscreenLayerParams *pTestOffscreen = &testOffscreen;
    static NvFlowGridRenderLayerParams *pTestRender = &testRender;

    static NvFlowUint64 version = 1u;

    static NvFlowDatabaseTypeSnapshot typeSnapshots[4u] = {
        {version, &NvFlowGridSimulateLayerParams_NvFlowReflectDataType,
         (NvFlowUint8 **)&pTestSimulate, 1u},
        {version, &NvFlowGridEmitterSphereParams_NvFlowReflectDataType,
         (NvFlowUint8 **)&pTestSpheres, 1u},
        {version, &NvFlowGridOffscreenLayerParams_NvFlowReflectDataType,
         (NvFlowUint8 **)&pTestOffscreen, 1u},
        {version, &NvFlowGridRenderLayerParams_NvFlowReflectDataType,
         (NvFlowUint8 **)&pTestRender, 1u}};
    static NvFlowDatabaseSnapshot snapshot = {version, typeSnapshots, 4u};

    double absoluteSimTime = (double)frame;
    static NvFlowGridParamsDescSnapshot gridParamsDescSnapshot = {
        snapshot, absoluteSimTime, 1.f / 60.f, NV_FLOW_FALSE, nullptr, 0u};
    gridParamsDescSnapshot.absoluteSimTime = absoluteSimTime; // Update time

    loader.gridParamsInterface.commitParams(paramSrc, &gridParamsDescSnapshot);

    NvFlowGridParamsDesc gridParamsDesc = {};
    NvFlowGridParamsSnapshot *paramsSnapshot =
        loader.gridParamsInterface.getParamsSnapshot(paramSrc, absoluteSimTime,
                                                     0llu);

    if (loader.gridParamsInterface.mapParamsDesc(paramSrc, paramsSnapshot,
                                                 &gridParamsDesc)) {
      std::cout << "  Calling simulate" << std::endl;
      loader.gridInterface.simulate(context, grid, &gridParamsDesc,
                                    NV_FLOW_FALSE);

      std::cout << "  Getting render data" << std::endl;
      NvFlowGridRenderData renderData = {};
      loader.gridInterface.getRenderData(context, grid, &renderData);

      std::cout << "  Flushing device queue" << std::endl;
      NvFlowUint64 flushedFrameID = 0llu;
      loader.deviceInterface.flush(deviceQueue, &flushedFrameID, nullptr,
                                   nullptr);
      std::cout << "  Waiting for frame " << flushedFrameID << std::endl;
      loader.deviceInterface.waitForFrame(deviceQueue, flushedFrameID);

      NvFlowUint64 lastCompletedFrame =
          contextInterface.getLastFrameCompleted(context);

      if (renderData.nanoVdb.readbackCount > 0u) {
        for (NvFlowUint64 idx = renderData.nanoVdb.readbackCount - 1u;
             idx < renderData.nanoVdb.readbackCount; idx--) {
          const auto readback = renderData.nanoVdb.readbacks + idx;
          if (lastCompletedFrame >= readback->globalFrameCompleted) {
            if (readback->smokeNanoVdbReadbackSize > 0) {
              std::cout << "Frame " << frame << " exported NanoVDB! Size: "
                        << readback->smokeNanoVdbReadbackSize << " bytes"
                        << std::endl;

              std::string filename = "smoke_" + std::to_string(frame) + ".nvdb";
              std::ofstream out(filename, std::ios::binary);
              out.write(reinterpret_cast<const char *>(
                            readback->smokeNanoVdbReadback),
                        readback->smokeNanoVdbReadbackSize);
              out.close();
            }
            break;
          }
        }
      }
      loader.gridParamsInterface.unmapParamsDesc(paramSrc, paramsSnapshot);
    }
  }

  loader.deviceInterface.waitIdle(deviceQueue);
  loader.gridInterface.destroyGrid(context, grid);
  loader.gridParamsInterface.destroyGridParamsNamed(gridParamsNamed);

  loader.deviceInterface.destroyDevice(deviceManager, device);
  loader.deviceInterface.destroyDeviceManager(deviceManager);
  NvFlowLoaderDestroy(&loader);

  std::cout << "Simulation complete!" << std::endl;
  return 0;
}
