#include <iostream>

#include "nvflowext/NvFlowLoader.h"
#include "simulation.h"

static void flowLoaderError(const char *str, void *userdata) {
  std::cerr << "Flow Error: " << str << std::endl;
}

int main() {
  NvFlowLoader loader = {};
  NvFlowLoaderInitDeviceAPI(&loader, flowLoaderError, nullptr,
                            eNvFlowContextApi_vulkan);

  if (!loader.module_nvflow || !loader.module_nvflowext) {
    std::cerr << "Failed to load NVIDIA Flow" << std::endl;
    return 1;
  }

  SimulationParams params = {};
  params.frame_count = 60;
  params.emitter_radius = 10.0f;
  params.emitter_temperature = 1.0f;
  params.emitter_smoke = 1.0f;
  params.emitter_velocity_y = 10.0f;
  params.couple_rate_smoke = 2.0f;
  params.nanoVdb_couple_rate = 1.0f;
  params.output_filename_prefix = "smoke_";

  run_simulation(&loader, &params);

  NvFlowLoaderDestroy(&loader);

  std::cout << "Simulation complete!" << std::endl;
  return 0;
}
