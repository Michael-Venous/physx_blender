import os
import bpy
import json
import csv
import logging

logger = logging.getLogger(__name__)


def export_mesh(obj, filepath):
    """
    Export selected mesh as OBJ file.
    
    Args:
        obj: Blender mesh object
        filepath: Output file path for OBJ
    """
    if obj is None or obj.type != "MESH":
        raise ValueError("Invalid mesh object")
    
    # Select the object and deselect others
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Export as OBJ
    bpy.ops.wm.obj_export(
        filepath=filepath,
        export_selected_objects=True,
        export_materials=False,
        export_uv=False,
        export_normals=True,
    )
    
    logger.info(f"Exported mesh '{obj.name}' to {filepath}")
    return filepath


def export_particles(particle_system, filepath):
    """
    Export particle positions and velocities as CSV.
    
    Args:
        particle_system: Blender particle system
        filepath: Output file path for CSV
    """
    if particle_system is None:
        raise ValueError("Invalid particle system")
    
    particles = particle_system.particles
    
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["px", "py", "pz", "vx", "vy", "vz"])
        
        for particle in particles:
            pos = particle.location
            vel = particle.velocity
            writer.writerow([
                pos.x, pos.y, pos.z,
                vel.x, vel.y, vel.z,
            ])
    
    logger.info(f"Exported {len(particles)} particles to {filepath}")
    return filepath


def write_params_json(params, filepath):
    """
    Write simulation parameters as JSON for C++ executable.
    
    Args:
        params: PhysXSmokeProperties instance
        filepath: Output file path for JSON
    """
    # Build parameters dict matching C++ SimulationParams
    params_dict = {
        "emitter_type": params.emitter_type,
        "emitter_radius": params.emitter_radius,
        "emitter_size": list(params.emitter_size),
        "emitter_temperature": params.emitter_temperature,
        "emitter_smoke": params.emitter_smoke,
        "emitter_velocity_y": params.emitter_velocity_y,
        "couple_rate_smoke": params.couple_rate_smoke,
        "nanoVdb_couple_rate": params.nanoVdb_couple_rate,
        "frame_count": params.frame_count,
        "velocity": list(params.velocity),
        "resolution": params.resolution,
        "output_prefix": params.output_prefix,
        "output_dir": params.output_dir,
        "gravity": list(params.gravity),
        "turbulence": params.turbulence,
        "vorticity": params.vorticity,
        "dissipation": params.dissipation,
    }
    
    with open(filepath, "w") as f:
        json.dump(params_dict, f, indent=2)
    
    logger.info(f"Wrote simulation parameters to {filepath}")
    return filepath


def build_command_args(params, temp_dir):
    """
    Build command-line arguments for the simulation executable.
    
    Args:
        params: PhysXSmokeProperties instance
        temp_dir: Temporary directory for intermediate files
    
    Returns:
        list: Command arguments
    """
    mesh_file = os.path.join(temp_dir, "emitter.obj")
    particles_file = os.path.join(temp_dir, "particles.csv")
    params_file = os.path.join(temp_dir, "params.json")
    
    # Export based on emitter type
    if params.emitter_type == "mesh" and params.mesh_object:
        export_mesh(params.mesh_object, mesh_file)
    elif params.emitter_type == "particles" and params.particle_system:
        export_particles(params.particle_system, particles_file)
    
    # Write parameters
    write_params_json(params, params_file)
    
    # Build command
    cmd = [
        params_file,
    ]
    
    return cmd, {
        "mesh_file": mesh_file if params.emitter_type == "mesh" else None,
        "particles_file": particles_file if params.emitter_type == "particles" else None,
        "params_file": params_file,
    }
