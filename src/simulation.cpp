#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <cstring>

#include "nvflowext/NvFlowLoader.h"
#include "nvflowext/shaders/NvFlowRayMarchParams.h"
#include "simulation.h"

#include <nanovdb/NanoVDB.h>
#include <nanovdb/GridHandle.h>
#include <nanovdb/tools/NanoToOpenVDB.h>
#include <openvdb/openvdb.h>

// Simple OBJ loader structures
struct ObjVertex {
    float x, y, z;
};

struct ObjFace {
    std::vector<int> vertex_indices; // 1-based indices
};

struct ObjMesh {
    std::vector<ObjVertex> vertices;
    std::vector<ObjFace> faces;
};

// Simple OBJ parser
static bool load_obj_file(const char* filename, ObjMesh& mesh) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open OBJ file: " << filename << std::endl;
        return false;
    }

    std::string line;
    while (std::getline(file, line)) {
        // Skip empty lines and comments
        if (line.empty() || line[0] == '#') {
            continue;
        }
        
        std::istringstream iss(line);
        std::string prefix;
        iss >> prefix;

        if (prefix == "v") {
            ObjVertex v;
            if (iss >> v.x >> v.y >> v.z) {
                mesh.vertices.push_back(v);
            }
        } else if (prefix == "f") {
            ObjFace face;
            std::string token;
            while (iss >> token) {
                // Parse the first index (may be followed by /texture/normal)
                size_t slash_pos = token.find('/');
                std::string idx_str = (slash_pos != std::string::npos) ? token.substr(0, slash_pos) : token;
                try {
                    int idx = std::stoi(idx_str);
                    face.vertex_indices.push_back(idx);
                } catch (...) {
                    // Skip invalid tokens
                }
            }
            if (face.vertex_indices.size() >= 3) {
                mesh.faces.push_back(face);
            }
        }
    }

    if (mesh.vertices.empty() || mesh.faces.empty()) {
        std::cerr << "Error: OBJ file has no valid vertices or faces: " << filename << std::endl;
        return false;
    }

    std::cout << "Loaded OBJ: " << mesh.vertices.size() << " vertices, " 
              << mesh.faces.size() << " faces" << std::endl;
    return true;
}

// Particle data structure
struct ParticleData {
    float x, y, z;      // position
    float vx, vy, vz;   // velocity
    float temperature;
    float smoke;
};

// Simple CSV parser for particles
static bool load_particle_file(const char* filename, std::vector<ParticleData>& particles) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open particle file: " << filename << std::endl;
        return false;
    }

    std::string line;
    int line_num = 0;
    while (std::getline(file, line)) {
        line_num++;
        // Skip empty lines and comments
        if (line.empty() || line[0] == '#') continue;
        
        // Skip header line if it contains non-numeric content
        if (line_num == 1) {
            std::istringstream check(line);
            std::string first;
            check >> first;
            // If first token is not a number, it's a header
            bool is_header = false;
            for (char c : first) {
                if (!isdigit(c) && c != '.' && c != '-' && c != '+') {
                    is_header = true;
                    break;
                }
            }
            if (is_header) continue;
        }

        std::istringstream iss(line);
        ParticleData p;
        char comma;
        if (iss >> p.x >> comma >> p.y >> comma >> p.z >> comma >> 
            p.vx >> comma >> p.vy >> comma >> p.vz >> comma >>
            p.temperature >> comma >> p.smoke) {
            particles.push_back(p);
        } else {
            // Try without commas (space-separated)
            std::istringstream iss2(line);
            if (iss2 >> p.x >> p.y >> p.z >> p.vx >> p.vy >> p.vz >> p.temperature >> p.smoke) {
                particles.push_back(p);
            } else {
                std::cerr << "Warning: Skipping invalid particle line " << line_num << std::endl;
            }
        }
    }

    if (particles.empty()) {
        std::cerr << "Error: No valid particles loaded from: " << filename << std::endl;
        return false;
    }

    std::cout << "Loaded " << particles.size() << " particles from: " << filename << std::endl;
    return true;
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

// Helper to build output path
static std::string build_output_path(const SimulationParams* params, int frame) {
    std::string path;
    if (params->output_dir && strlen(params->output_dir) > 0) {
        path = params->output_dir;
        // Ensure trailing slash
        if (path.back() != '/') {
            path += '/';
        }
    }
    path += params->output_filename_prefix;
    path += std::to_string(frame);
    path += ".vdb";
    return path;
}

void run_simulation(NvFlowLoader* loader, const SimulationParams* params) {
  std::cout << "Creating Device Manager" << std::endl;
  NvFlowDeviceManager *deviceManager =
      loader->deviceInterface.createDeviceManager(NV_FLOW_FALSE, nullptr, 0u);
  NvFlowDeviceDesc deviceDesc = {};
  deviceDesc.deviceIndex = 0;
  deviceDesc.enableExternalUsage = NV_FLOW_FALSE;
  deviceDesc.logPrint = logPrint;

  std::cout << "Creating Device" << std::endl;
  NvFlowDevice *device =
      loader->deviceInterface.createDevice(deviceManager, &deviceDesc);

  std::cout << "Getting Device Queue" << std::endl;
  NvFlowDeviceQueue *deviceQueue =
      loader->deviceInterface.getDeviceQueue(device);

  NvFlowContextInterface contextInterface = {};
  NvFlowContextInterface_duplicate(
      &contextInterface,
      loader->deviceInterface.getContextInterface(deviceQueue));
  NvFlowContext *context = loader->deviceInterface.getContext(deviceQueue);

  std::cout << "Creating Grid" << std::endl;
  NvFlowGridDesc gridDesc = NvFlowGridDesc_default;
  gridDesc.maxLocations = (params->resolution / 32) * (params->resolution / 32) * (params->resolution / 8);
  if (gridDesc.maxLocations < 4096u) gridDesc.maxLocations = 4096u;
  NvFlowGrid *grid = loader->gridInterface.createGrid(
      &contextInterface, context, loader->opList_orig, loader->extOpList_orig,
      &gridDesc);

  std::cout << "Creating Grid Params Named" << std::endl;
  NvFlowGridParamsNamed *gridParamsNamed =
      loader->gridParamsInterface.createGridParamsNamed("flowUsd");

  NvFlowGridParams *paramSrc =
      loader->gridParamsInterface.mapGridParamsNamed(gridParamsNamed);

  // Load mesh data if needed
  ObjMesh objMesh;
  bool mesh_loaded = false;
  if (params->emitter_type == EMITTER_TYPE_MESH && params->mesh_file) {
      mesh_loaded = load_obj_file(params->mesh_file, objMesh);
      if (!mesh_loaded) {
          std::cerr << "Warning: Failed to load mesh, falling back to sphere emitter" << std::endl;
      }
  }

  // Load particle data if needed
  std::vector<ParticleData> particleData;
  bool particles_loaded = false;
  if (params->emitter_type == EMITTER_TYPE_PARTICLES && params->particle_file) {
      particles_loaded = load_particle_file(params->particle_file, particleData);
      if (!particles_loaded) {
          std::cerr << "Warning: Failed to load particles, falling back to sphere emitter" << std::endl;
      }
  }

  // Determine effective emitter type (fall back to sphere if loading failed)
  int effective_emitter_type = params->emitter_type;
  if (effective_emitter_type == EMITTER_TYPE_MESH && !mesh_loaded) {
      effective_emitter_type = EMITTER_TYPE_SPHERE;
  }
  if (effective_emitter_type == EMITTER_TYPE_PARTICLES && !particles_loaded) {
      effective_emitter_type = EMITTER_TYPE_SPHERE;
  }

  // Determine velocity to use
  float vel_x = params->velocity[0];
  float vel_y = params->emitter_velocity_y;
  float vel_z = params->velocity[2];

  if (params->velocity[0] != 0.0f) vel_x = params->velocity[0];
  if (params->velocity[1] != 0.0f) vel_y = params->velocity[1];
  if (params->velocity[2] != 0.0f) vel_z = params->velocity[2];

  // Pre-allocate mesh emitter params for mesh type
  NvFlowGridEmitterMeshParams meshEmitterParams = NvFlowEmitterMeshParams_default;
  std::vector<NvFlowFloat3> meshPositions;
  std::vector<int> meshFaceIndices;
  std::vector<int> meshFaceCounts;

  if (effective_emitter_type == EMITTER_TYPE_MESH && mesh_loaded) {
      // Convert OBJ vertices to NvFlowFloat3
      meshPositions.reserve(objMesh.vertices.size());
      for (const auto& v : objMesh.vertices) {
          NvFlowFloat3 pos = {v.x, v.y, v.z};
          meshPositions.push_back(pos);
      }

      // Convert faces to vertex indices and counts
      int total_indices = 0;
      for (const auto& face : objMesh.faces) {
          total_indices += face.vertex_indices.size();
      }
      meshFaceIndices.reserve(total_indices);
      meshFaceCounts.reserve(objMesh.faces.size());

      for (const auto& face : objMesh.faces) {
          meshFaceCounts.push_back((int)face.vertex_indices.size());
          for (int idx : face.vertex_indices) {
              if (idx < 0) {
                  idx = (int)objMesh.vertices.size() + idx;
              } else {
                  idx = idx - 1;
              }
              meshFaceIndices.push_back(idx);
          }
      }

      // Set up mesh emitter params
      meshEmitterParams.enabled = NV_FLOW_TRUE;
      meshEmitterParams.velocity = {vel_x, vel_y, vel_z};
      meshEmitterParams.temperature = params->emitter_temperature;
      meshEmitterParams.smoke = params->emitter_smoke;
      meshEmitterParams.coupleRateSmoke = params->couple_rate_smoke;
      meshEmitterParams.meshPositions = meshPositions.data();
      meshEmitterParams.meshPositionCount = meshPositions.size();
      meshEmitterParams.meshFaceVertexIndices = meshFaceIndices.data();
      meshEmitterParams.meshFaceVertexIndexCount = meshFaceIndices.size();
      meshEmitterParams.meshFaceVertexCounts = meshFaceCounts.data();
      meshEmitterParams.meshFaceVertexCountCount = meshFaceCounts.size();
  }

  // Pre-allocate particle emitter params for particle type
  // Use a single NvFlowGridEmitterPointParams with arrays for all particles
  NvFlowGridEmitterPointParams particleEmitterParams = NvFlowEmitterPointParams_default;
  std::vector<NvFlowFloat3> particlePositions;
  std::vector<NvFlowFloat3> particleVelocities;
  std::vector<float> particleTemperatures;
  std::vector<float> particleSmokes;

  if (effective_emitter_type == EMITTER_TYPE_PARTICLES && particles_loaded) {
      particlePositions.reserve(particleData.size());
      particleVelocities.reserve(particleData.size());
      particleTemperatures.reserve(particleData.size());
      particleSmokes.reserve(particleData.size());

      for (size_t i = 0; i < particleData.size(); i++) {
          const auto& p = particleData[i];
          
          NvFlowFloat3 pos = {p.x, p.y, p.z};
          NvFlowFloat3 vel = {p.vx, p.vy, p.vz};
          
          // Apply velocity override if specified
          if (params->velocity[0] != 0.0f || params->velocity[1] != 0.0f || params->velocity[2] != 0.0f) {
              vel = {vel_x, vel_y, vel_z};
          }

          particlePositions.push_back(pos);
          particleVelocities.push_back(vel);
          particleTemperatures.push_back(p.temperature);
          particleSmokes.push_back(p.smoke);
      }

      // Set up single emitter params with all particles as arrays
      particleEmitterParams.enabled = NV_FLOW_TRUE;
      particleEmitterParams.pointPositions = particlePositions.data();
      particleEmitterParams.pointPositionCount = particlePositions.size();
      particleEmitterParams.pointVelocities = particleVelocities.data();
      particleEmitterParams.pointVelocityCount = particleVelocities.size();
      particleEmitterParams.pointTemperatures = particleTemperatures.data();
      particleEmitterParams.pointTemperatureCount = particleTemperatures.size();
      particleEmitterParams.pointSmokes = particleSmokes.data();
      particleEmitterParams.pointSmokeCount = particleSmokes.size();
      particleEmitterParams.coupleRateSmoke = params->couple_rate_smoke;
  }

  openvdb::initialize();

  std::cout << "Running simulation..." << std::endl;

  for (uint32_t frame = params->start_frame; frame < params->start_frame + params->frame_count; frame++) {
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
    testSimulate.nanoVdbExport.velocityEnabled = NV_FLOW_FALSE;
    testSimulate.stepsPerSecond = params->fps;

    // Set up emitter based on type
    if (effective_emitter_type == EMITTER_TYPE_SPHERE) {
        testSpheres.enabled = NV_FLOW_TRUE;
        testSpheres.position = {params->emitter_position[0],
                                params->emitter_position[1],
                                params->emitter_position[2]};
        testSpheres.radius = params->emitter_radius;
        testSpheres.radiusIsWorldSpace = NV_FLOW_TRUE;
        testSpheres.temperature = params->emitter_temperature;
        testSpheres.fuel = 0.0f;
        testSpheres.smoke = params->emitter_smoke;

        float obj_vx = params->object_velocity[0];
        float obj_vy = params->object_velocity[1];
        float obj_vz = params->object_velocity[2];
        testSpheres.velocity = {vel_x + obj_vx, vel_y + obj_vy, vel_z + obj_vz};

        testSpheres.coupleRateSmoke = params->couple_rate_smoke;
        testSpheres.coupleRateVelocity = params->couple_rate_smoke;
        testSpheres.coupleRateTemperature = params->couple_rate_smoke;
    }

    static NvFlowGridSimulateLayerParams *pTestSimulate = &testSimulate;
    static NvFlowGridEmitterSphereParams *pTestSpheres = &testSpheres;
    static NvFlowGridOffscreenLayerParams *pTestOffscreen = &testOffscreen;
    static NvFlowGridRenderLayerParams *pTestRender = &testRender;

    static NvFlowUint64 version = 1u;
    version++;

    // Build type snapshots array based on emitter type
    std::vector<NvFlowDatabaseTypeSnapshot> typeSnapshots;
    typeSnapshots.push_back({version, &NvFlowGridSimulateLayerParams_NvFlowReflectDataType,
         (NvFlowUint8 **)&pTestSimulate, 1u});
    
    if (effective_emitter_type == EMITTER_TYPE_SPHERE) {
        typeSnapshots.push_back({version, &NvFlowGridEmitterSphereParams_NvFlowReflectDataType,
             (NvFlowUint8 **)&pTestSpheres, 1u});
    } else if (effective_emitter_type == EMITTER_TYPE_MESH) {
        NvFlowGridEmitterMeshParams* pMeshParams = &meshEmitterParams;
        typeSnapshots.push_back({version, &NvFlowGridEmitterMeshParams_NvFlowReflectDataType,
             (NvFlowUint8 **)&pMeshParams, 1u});
    } else if (effective_emitter_type == EMITTER_TYPE_PARTICLES) {
        // For particles, we use a single point params struct with arrays
        NvFlowGridEmitterPointParams* pParticleParams = &particleEmitterParams;
        typeSnapshots.push_back({version, &NvFlowGridEmitterPointParams_NvFlowReflectDataType,
             (NvFlowUint8 **)&pParticleParams, 1u});
    }
    
    typeSnapshots.push_back({version, &NvFlowGridOffscreenLayerParams_NvFlowReflectDataType,
         (NvFlowUint8 **)&pTestOffscreen, 1u});
    typeSnapshots.push_back({version, &NvFlowGridRenderLayerParams_NvFlowReflectDataType,
         (NvFlowUint8 **)&pTestRender, 1u});

    static NvFlowDatabaseSnapshot snapshot = {version, nullptr, 0u};
    snapshot.version = version;
    snapshot.typeSnapshots = typeSnapshots.data();
    snapshot.typeSnapshotCount = typeSnapshots.size();

    double absoluteSimTime = (double)frame / (double)params->fps;
    float timeStep = 1.0f / params->fps;
    static NvFlowGridParamsDescSnapshot gridParamsDescSnapshot = {
        snapshot, absoluteSimTime, timeStep, NV_FLOW_FALSE, nullptr, 0u};
    gridParamsDescSnapshot.snapshot = snapshot;
    gridParamsDescSnapshot.absoluteSimTime = absoluteSimTime;
    gridParamsDescSnapshot.deltaTime = timeStep;

    loader->gridParamsInterface.commitParams(paramSrc, &gridParamsDescSnapshot);

    NvFlowGridParamsDesc gridParamsDesc = {};
    NvFlowGridParamsSnapshot *paramsSnapshot =
        loader->gridParamsInterface.getParamsSnapshot(paramSrc, absoluteSimTime,
                                                     0llu);

    if (loader->gridParamsInterface.mapParamsDesc(paramSrc, paramsSnapshot,
                                                 &gridParamsDesc)) {
      std::cout << "  Calling simulate" << std::endl;
      loader->gridInterface.simulate(context, grid, &gridParamsDesc,
                                    NV_FLOW_FALSE);

      std::cout << "  Getting render data" << std::endl;
      NvFlowGridRenderData renderData = {};
      loader->gridInterface.getRenderData(context, grid, &renderData);

      std::cout << "  Flushing device queue" << std::endl;
      NvFlowUint64 flushedFrameID = 0llu;
      loader->deviceInterface.flush(deviceQueue, &flushedFrameID, nullptr,
                                   nullptr);
      std::cout << "  Waiting for frame " << flushedFrameID << std::endl;
      loader->deviceInterface.waitForFrame(deviceQueue, flushedFrameID);

      NvFlowUint64 lastCompletedFrame =
          contextInterface.getLastFrameCompleted(context);

      if (renderData.nanoVdb.readbackCount > 0u) {
        for (NvFlowUint64 idx = renderData.nanoVdb.readbackCount - 1u;
             idx < renderData.nanoVdb.readbackCount; idx--) {
          const auto readback = renderData.nanoVdb.readbacks + idx;
          if (lastCompletedFrame >= readback->globalFrameCompleted) {
            if (readback->smokeNanoVdbReadbackSize > 0) {
              std::cout << "Frame " << frame << " NanoVDB size: "
                        << readback->smokeNanoVdbReadbackSize << " bytes"
                        << std::endl;

              auto buffer = nanovdb::HostBuffer::createFull(
                  readback->smokeNanoVdbReadbackSize,
                  readback->smokeNanoVdbReadback);
              nanovdb::GridHandle<nanovdb::HostBuffer> handle(std::move(buffer));

              auto openvdbGrid = nanovdb::tools::nanoToOpenVDB(handle, 0);
              if (!openvdbGrid) {
                  std::cerr << "Warning: Failed to convert NanoVDB to OpenVDB for frame "
                            << frame << std::endl;
                  continue;
              }
              openvdbGrid->setName("density");

              std::string filename = build_output_path(params, frame);
              openvdb::GridPtrVec grids;
              grids.push_back(openvdbGrid);
              openvdb::io::File file(filename);
              file.setCompression(openvdb::io::COMPRESS_NONE);
              file.write(grids);
              file.close();

              std::cout << "  Saved OpenVDB: " << filename << std::endl;
            }
            break;
          }
        }
      }
      loader->gridParamsInterface.unmapParamsDesc(paramSrc, paramsSnapshot);
    }
  }

  loader->deviceInterface.waitIdle(deviceQueue);
  loader->gridInterface.destroyGrid(context, grid);
  loader->gridParamsInterface.destroyGridParamsNamed(gridParamsNamed);

  loader->deviceInterface.destroyDevice(deviceManager, device);
  loader->deviceInterface.destroyDeviceManager(deviceManager);
}
