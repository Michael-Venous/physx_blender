#ifndef SIMULATION_H
#define SIMULATION_H

#include <stdint.h>
#include <stddef.h>

// Emitter type constants
#define EMITTER_TYPE_SPHERE 0
#define EMITTER_TYPE_MESH 1
#define EMITTER_TYPE_PARTICLES 2

typedef struct {
    // Existing fields
    uint32_t frame_count;
    float emitter_radius;
    float emitter_temperature;
    float emitter_smoke;
    float emitter_velocity_y;
    float couple_rate_smoke;
    float nanoVdb_couple_rate;
    const char* output_filename_prefix;

    // New fields for mesh/particle support
    int emitter_type;           // 0=sphere, 1=mesh, 2=particles
    const char* mesh_file;      // Path to OBJ file
    const char* particle_file;  // Path to CSV file
    const char* velocity_file;  // Optional velocity override file
    float velocity[3];          // Velocity override (x, y, z)
    const char* output_dir;     // Directory for output .vdb files
} SimulationParams;

// Initialize SimulationParams with default values
static inline void SimulationParams_InitDefaults(SimulationParams* params) {
    params->frame_count = 60;
    params->emitter_radius = 10.0f;
    params->emitter_temperature = 1.0f;
    params->emitter_smoke = 1.0f;
    params->emitter_velocity_y = 10.0f;
    params->couple_rate_smoke = 2.0f;
    params->nanoVdb_couple_rate = 1.0f;
    params->output_filename_prefix = "smoke_";
    params->emitter_type = EMITTER_TYPE_SPHERE;
    params->mesh_file = NULL;
    params->particle_file = NULL;
    params->velocity_file = NULL;
    params->velocity[0] = 0.0f;
    params->velocity[1] = 0.0f;
    params->velocity[2] = 0.0f;
    params->output_dir = NULL;
}

struct NvFlowLoader;
void run_simulation(struct NvFlowLoader* loader, const SimulationParams* params);

#endif // SIMULATION_H
