#include <iostream>
#include <cstring>
#include <cstdlib>
#include <sys/stat.h>

#include "nvflowext/NvFlowLoader.h"
#include "simulation.h"

static void flowLoaderError(const char *str, void *userdata) {
  std::cerr << "Flow Error: " << str << std::endl;
}

static void print_usage(const char* progname) {
    std::cout << "Usage: " << progname << " [options]\n"
              << "Options:\n"
              << "  --frame-count <N>            Number of frames to simulate (default: 60)\n"
              << "  --start-frame <N>            Frame to start simulation from (default: 0)\n"
              << "  --emitter-radius <F>         Radius of sphere emitter (default: 10.0)\n"
              << "  --emitter-temperature <F>    Temperature of emitter (default: 1.0)\n"
              << "  --emitter-smoke <F>          Smoke density of emitter (default: 1.0)\n"
              << "  --emitter-velocity-y <F>     Y velocity of sphere emitter (default: 10.0)\n"
              << "  --couple-rate-smoke <F>      Smoke coupling rate (default: 2.0)\n"
              << "  --output-prefix <S>          Prefix for output files (default: smoke_)\n"
              << "  --emitter-type <N>           Emitter type: 0=sphere, 1=mesh, 2=particles (default: 0)\n"
              << "  --mesh-file <path>           Path to OBJ file for mesh emitter\n"
              << "  --particle-file <path>       Path to CSV file for particle emitter\n"
              << "  --velocity-file <path>       Optional velocity override file\n"
              << "  --velocity-x <F>             X component of velocity override\n"
              << "  --velocity-y <F>             Y component of velocity override\n"
              << "  --velocity-z <F>             Z component of velocity override\n"
              << "  --output-dir <path>          Directory for output .vdb files (default: current dir)\n"
              << "  --fps <F>                    Frames per second (default: 60.0)\n"
              << "  --resolution <N>             Grid resolution (default: 64)\n"
              << "  --gravity-x <F>              Gravity X component (default: 0.0)\n"
              << "  --gravity-y <F>              Gravity Y component (default: -9.81)\n"
              << "  --gravity-z <F>              Gravity Z component (default: 0.0)\n"
              << "  --turbulence <F>             Turbulence strength (default: 0.0)\n"
              << "  --vorticity <F>              Vorticity confinement (default: 0.0)\n"
              << "  --dissipation <F>            Smoke dissipation (default: 0.0)\n"
              << "  --emitter-pos-x <F>          Emitter world position X (default: 0.0)\n"
              << "  --emitter-pos-y <F>          Emitter world position Y (default: 0.0)\n"
              << "  --emitter-pos-z <F>          Emitter world position Z (default: 0.0)\n"
              << "  --object-vel-x <F>           Object velocity X for advection (default: 0.0)\n"
              << "  --object-vel-y <F>           Object velocity Y for advection (default: 0.0)\n"
              << "  --object-vel-z <F>           Object velocity Z for advection (default: 0.0)\n"
              << "  --help                       Show this help message\n";
}

static bool create_directory_if_not_exists(const char* path) {
    if (!path || strlen(path) == 0) return true;
    struct stat st;
    if (stat(path, &st) == 0) {
        return S_ISDIR(st.st_mode);
    }
    return mkdir(path, 0755) == 0;
}

int main(int argc, char* argv[]) {
    // Initialize params with defaults
    SimulationParams params;
    SimulationParams_InitDefaults(&params);

    // Parse command-line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "--frame-count") == 0 && i + 1 < argc) {
            params.frame_count = (uint32_t)atoi(argv[++i]);
        } else if (strcmp(argv[i], "--start-frame") == 0 && i + 1 < argc) {
            params.start_frame = (uint32_t)atoi(argv[++i]);
        } else if (strcmp(argv[i], "--emitter-radius") == 0 && i + 1 < argc) {
            params.emitter_radius = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--emitter-temperature") == 0 && i + 1 < argc) {
            params.emitter_temperature = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--emitter-smoke") == 0 && i + 1 < argc) {
            params.emitter_smoke = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--emitter-velocity-y") == 0 && i + 1 < argc) {
            params.emitter_velocity_y = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--couple-rate-smoke") == 0 && i + 1 < argc) {
            params.couple_rate_smoke = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--output-prefix") == 0 && i + 1 < argc) {
            params.output_filename_prefix = argv[++i];
        } else if (strcmp(argv[i], "--emitter-type") == 0 && i + 1 < argc) {
            params.emitter_type = atoi(argv[++i]);
            if (params.emitter_type < 0 || params.emitter_type > 2) {
                std::cerr << "Error: emitter-type must be 0 (sphere), 1 (mesh), or 2 (particles)\n";
                return 1;
            }
        } else if (strcmp(argv[i], "--mesh-file") == 0 && i + 1 < argc) {
            params.mesh_file = argv[++i];
        } else if (strcmp(argv[i], "--particle-file") == 0 && i + 1 < argc) {
            params.particle_file = argv[++i];
        } else if (strcmp(argv[i], "--velocity-file") == 0 && i + 1 < argc) {
            params.velocity_file = argv[++i];
        } else if (strcmp(argv[i], "--velocity-x") == 0 && i + 1 < argc) {
            params.velocity[0] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--velocity-y") == 0 && i + 1 < argc) {
            params.velocity[1] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--velocity-z") == 0 && i + 1 < argc) {
            params.velocity[2] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--output-dir") == 0 && i + 1 < argc) {
            params.output_dir = argv[++i];
        } else if (strcmp(argv[i], "--fps") == 0 && i + 1 < argc) {
            params.fps = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--resolution") == 0 && i + 1 < argc) {
            params.resolution = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--gravity-x") == 0 && i + 1 < argc) {
            params.gravity[0] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--gravity-y") == 0 && i + 1 < argc) {
            params.gravity[1] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--gravity-z") == 0 && i + 1 < argc) {
            params.gravity[2] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--turbulence") == 0 && i + 1 < argc) {
            params.turbulence = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--vorticity") == 0 && i + 1 < argc) {
            params.vorticity = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--dissipation") == 0 && i + 1 < argc) {
            params.dissipation = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--emitter-pos-x") == 0 && i + 1 < argc) {
            params.emitter_position[0] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--emitter-pos-y") == 0 && i + 1 < argc) {
            params.emitter_position[1] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--emitter-pos-z") == 0 && i + 1 < argc) {
            params.emitter_position[2] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--object-vel-x") == 0 && i + 1 < argc) {
            params.object_velocity[0] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--object-vel-y") == 0 && i + 1 < argc) {
            params.object_velocity[1] = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "--object-vel-z") == 0 && i + 1 < argc) {
            params.object_velocity[2] = (float)atof(argv[++i]);
        } else {
            std::cerr << "Error: Unknown argument: " << argv[i] << "\n";
            print_usage(argv[0]);
            return 1;
        }
    }

    // Validate emitter type requirements
    if (params.emitter_type == EMITTER_TYPE_MESH && !params.mesh_file) {
        std::cerr << "Error: --mesh-file is required for mesh emitter type\n";
        return 1;
    }
    if (params.emitter_type == EMITTER_TYPE_PARTICLES && !params.particle_file) {
        std::cerr << "Error: --particle-file is required for particle emitter type\n";
        return 1;
    }

    // Validate file existence
    if (params.emitter_type == EMITTER_TYPE_MESH && params.mesh_file) {
        struct stat st;
        if (stat(params.mesh_file, &st) != 0 || !S_ISREG(st.st_mode)) {
            std::cerr << "Error: Mesh file not found or not a regular file: " << params.mesh_file << "\n";
            return 1;
        }
    }
    if (params.emitter_type == EMITTER_TYPE_PARTICLES && params.particle_file) {
        struct stat st;
        if (stat(params.particle_file, &st) != 0 || !S_ISREG(st.st_mode)) {
            std::cerr << "Error: Particle file not found or not a regular file: " << params.particle_file << "\n";
            return 1;
        }
    }
    if (params.velocity_file) {
        struct stat st;
        if (stat(params.velocity_file, &st) != 0 || !S_ISREG(st.st_mode)) {
            std::cerr << "Error: Velocity file not found or not a regular file: " << params.velocity_file << "\n";
            return 1;
        }
    }

    // Validate numeric parameters
    if (params.frame_count == 0) {
        std::cerr << "Error: frame-count must be greater than 0\n";
        return 1;
    }
    if (params.emitter_radius <= 0.0f) {
        std::cerr << "Error: emitter-radius must be greater than 0\n";
        return 1;
    }
    if (params.emitter_temperature < 0.0f) {
        std::cerr << "Error: emitter-temperature must not be negative\n";
        return 1;
    }
    if (params.emitter_smoke < 0.0f) {
        std::cerr << "Error: emitter-smoke must not be negative\n";
        return 1;
    }
    if (params.couple_rate_smoke < 0.0f) {
        std::cerr << "Error: couple-rate-smoke must not be negative\n";
        return 1;
    }
    if (params.fps <= 0.0f) {
        std::cerr << "Error: fps must be greater than 0\n";
        return 1;
    }
    if (params.resolution < 16) {
        std::cerr << "Error: resolution must be at least 16\n";
        return 1;
    }
    if (params.turbulence < 0.0f) {
        std::cerr << "Error: turbulence must not be negative\n";
        return 1;
    }
    if (params.vorticity < 0.0f) {
        std::cerr << "Error: vorticity must not be negative\n";
        return 1;
    }
    if (params.dissipation < 0.0f || params.dissipation > 1.0f) {
        std::cerr << "Error: dissipation must be between 0 and 1\n";
        return 1;
    }

    // Create output directory if specified
    if (params.output_dir && !create_directory_if_not_exists(params.output_dir)) {
        std::cerr << "Error: Failed to create output directory: " << params.output_dir << "\n";
        return 1;
    }

    // Initialize NvFlow
    NvFlowLoader loader = {};
    NvFlowLoaderInitDeviceAPI(&loader, flowLoaderError, nullptr,
                              eNvFlowContextApi_vulkan);

    if (!loader.module_nvflow || !loader.module_nvflowext) {
        std::cerr << "Failed to load NVIDIA Flow" << std::endl;
        return 1;
    }

    run_simulation(&loader, &params);

    NvFlowLoaderDestroy(&loader);

    std::cout << "Simulation complete!" << std::endl;
    return 0;
}
