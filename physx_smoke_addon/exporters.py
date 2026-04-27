import os
import bpy
import json
import csv
import logging

logger = logging.getLogger(__name__)


def export_mesh(obj, filepath):
    """
    Export selected mesh as OBJ file with world transform applied.
    
    Args:
        obj: Blender mesh object
        filepath: Output file path for OBJ
    """
    if obj is None or obj.type != "MESH":
        raise ValueError("Invalid mesh object")
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(eval_obj)
    
    world_matrix = obj.matrix_world
    
    with open(filepath, "w") as f:
        f.write("# Exported by PhysX Smoke Addon\n")
        f.write(f"o {obj.name}\n")
        
        for v in mesh.vertices:
            world_co = world_matrix @ v.co
            f.write(f"v {world_co.x:.6f} {world_co.y:.6f} {world_co.z:.6f}\n")
        
        for poly in mesh.polygons:
            f.write("f")
            for vi in poly.vertices:
                f.write(f" {vi + 1}")
            f.write("\n")
    
    bpy.data.meshes.remove(mesh)
    
    logger.info(f"Exported mesh '{obj.name}' to {filepath}")
    return filepath


def export_particles(particle_system, emitter_obj, filepath, default_temperature=1.0, default_smoke=1.0):
    """
    Export particle positions, velocities, temperature, and smoke as CSV
    in world coordinates.
    
    Args:
        particle_system: Blender particle system
        emitter_obj: Object that owns the particle system
        filepath: Output file path for CSV
        default_temperature: Default temperature for particles
        default_smoke: Default smoke density for particles
    """
    if particle_system is None:
        raise ValueError("Invalid particle system")
    
    particles = particle_system.particles
    world_matrix = emitter_obj.matrix_world if emitter_obj else None
    
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["px", "py", "pz", "vx", "vy", "vz", "temperature", "smoke"])
        
        for particle in particles:
            pos = particle.location.copy()
            vel = particle.velocity.copy()
            
            if world_matrix:
                pos = world_matrix @ pos
                vel = world_matrix.to_3x3() @ vel
            
            writer.writerow([
                pos.x, pos.y, pos.z,
                vel.x, vel.y, vel.z,
                default_temperature,
                default_smoke,
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
        "emitter_temperature": params.emitter_temperature,
        "emitter_smoke": params.emitter_smoke,
        "emitter_velocity_y": params.emitter_velocity_y,
        "couple_rate_smoke": params.couple_rate_smoke,
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
    elif params.emitter_type == "particles" and params.particle_system_name:
        found = False
        for obj in bpy.data.objects:
            if obj.particle_systems:
                for ps in obj.particle_systems:
                    if ps.name == params.particle_system_name:
                        export_particles(ps, obj, particles_file,
                                         params.emitter_temperature,
                                         params.emitter_smoke)
                        found = True
                        break
            if found:
                break
    
    # Write parameters as JSON for debugging (not used by executable)
    write_params_json(params, params_file)
    
    # Map emitter type string to integer
    emitter_type_map = {
        "sphere": 0,
        "mesh": 1,
        "particles": 2,
    }
    emitter_type_int = emitter_type_map.get(params.emitter_type, 0)
    
    # Get active object's world position and velocity for emitter
    obj_pos = (0.0, 0.0, 0.0)
    obj_vel = (0.0, 0.0, 0.0)
    active_obj = bpy.context.active_object
    if active_obj:
        pos = active_obj.matrix_world.translation
        obj_pos = (pos.x, pos.y, pos.z)
        fps = bpy.context.scene.render.fps
        cur_frame = bpy.context.scene.frame_current
        if fps > 0 and cur_frame > bpy.context.scene.frame_start:
            orig = cur_frame
            bpy.context.scene.frame_set(cur_frame - 1)
            prev_pos = active_obj.matrix_world.translation.copy()
            bpy.context.scene.frame_set(orig)
            delta = pos - prev_pos
            obj_vel = (delta.x * fps, delta.y * fps, delta.z * fps)

    # Build command arguments list
    cmd_args = [
        "--frame-count", str(params.frame_count),
        "--emitter-radius", str(params.emitter_radius),
        "--emitter-temperature", str(params.emitter_temperature),
        "--emitter-smoke", str(params.emitter_smoke),
        "--emitter-velocity-y", str(params.emitter_velocity_y),
        "--couple-rate-smoke", str(params.couple_rate_smoke),
        "--output-prefix", params.output_prefix,
        "--emitter-type", str(emitter_type_int),
        "--output-dir", params.output_dir,
        "--fps", str(bpy.context.scene.render.fps),
        "--resolution", str(params.resolution),
        "--gravity-x", str(params.gravity[0]),
        "--gravity-y", str(params.gravity[1]),
        "--gravity-z", str(params.gravity[2]),
        "--turbulence", str(params.turbulence),
        "--vorticity", str(params.vorticity),
        "--dissipation", str(params.dissipation),
        "--emitter-pos-x", str(obj_pos[0]),
        "--emitter-pos-y", str(obj_pos[1]),
        "--emitter-pos-z", str(obj_pos[2]),
        "--object-vel-x", str(obj_vel[0]),
        "--object-vel-y", str(obj_vel[1]),
        "--object-vel-z", str(obj_vel[2]),
    ]

    if params.baked_frames > 0:
        cmd_args.extend(["--start-frame", str(params.baked_frames)])
    
    # Add velocity components if any non-zero (optional)
    if abs(params.velocity[0]) > 1e-6 or abs(params.velocity[1]) > 1e-6 or abs(params.velocity[2]) > 1e-6:
        cmd_args.extend(["--velocity-x", str(params.velocity[0])])
        cmd_args.extend(["--velocity-y", str(params.velocity[1])])
        cmd_args.extend(["--velocity-z", str(params.velocity[2])])
    
    # Add mesh or particle file if applicable
    if params.emitter_type == "mesh" and params.mesh_object:
        cmd_args.extend(["--mesh-file", mesh_file])
    elif params.emitter_type == "particles" and params.particle_system_name:
        cmd_args.extend(["--particle-file", particles_file])
    
    return cmd_args, {
        "mesh_file": mesh_file if params.emitter_type == "mesh" else None,
        "particles_file": particles_file if params.emitter_type == "particles" else None,
        "params_file": params_file,
    }
