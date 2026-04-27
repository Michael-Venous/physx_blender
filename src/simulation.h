#ifndef SIMULATION_H
#define SIMULATION_H

#include <stdint.h>
#include <stddef.h>

// Emitter type constants
#define EMITTER_TYPE_SPHERE 0
#define EMITTER_TYPE_MESH 1
#define EMITTER_TYPE_PARTICLES 2

typedef struct {
    uint32_t frame_count;
    uint32_t start_frame;
    float emitter_radius;
    float emitter_temperature;
    float emitter_smoke;
    float emitter_velocity_y;
    float couple_rate_smoke;
    const char* output_filename_prefix;

    int emitter_type;
    const char* mesh_file;
    const char* particle_file;
    const char* velocity_file;
    float velocity[3];
    const char* output_dir;

    float fps;
    int resolution;
    float gravity[3];
    float turbulence;
    float vorticity;
    float dissipation;

    float emitter_position[3];
    float object_velocity[3];
} SimulationParams;

// Initialize SimulationParams with default values
static inline void SimulationParams_InitDefaults(SimulationParams* params) {
    params->frame_count = 60;
    params->start_frame = 0;
    params->emitter_radius = 10.0f;
    params->emitter_temperature = 1.0f;
    params->emitter_smoke = 1.0f;
    params->emitter_velocity_y = 10.0f;
    params->couple_rate_smoke = 2.0f;
    params->output_filename_prefix = "smoke_";
    params->emitter_type = EMITTER_TYPE_SPHERE;
    params->mesh_file = NULL;
    params->particle_file = NULL;
    params->velocity_file = NULL;
    params->velocity[0] = 0.0f;
    params->velocity[1] = 0.0f;
    params->velocity[2] = 0.0f;
    params->output_dir = NULL;
    params->fps = 60.0f;
    params->resolution = 64;
    params->gravity[0] = 0.0f;
    params->gravity[1] = -9.81f;
    params->gravity[2] = 0.0f;
    params->turbulence = 0.0f;
    params->vorticity = 0.0f;
    params->dissipation = 0.0f;
    params->emitter_position[0] = 0.0f;
    params->emitter_position[1] = 0.0f;
    params->emitter_position[2] = 0.0f;
    params->object_velocity[0] = 0.0f;
    params->object_velocity[1] = 0.0f;
    params->object_velocity[2] = 0.0f;
}

struct NvFlowLoader;
void run_simulation(struct NvFlowLoader* loader, const SimulationParams* params);

#endif // SIMULATION_H
