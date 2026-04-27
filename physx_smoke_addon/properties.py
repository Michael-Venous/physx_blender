import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
    PointerProperty,
    BoolProperty,
)


class PhysXSmokeProperties(bpy.types.PropertyGroup):
    """Custom PropertyGroup storing all simulation parameters for PhysX smoke simulation."""
    
    # Emitter Settings
    emitter_type: EnumProperty(
        name="Emitter Type",
        description="Type of smoke emitter",
        items=[
            ("sphere", "Sphere", "Spherical emitter"),
            ("mesh", "Mesh", "Mesh-based emitter"),
            ("particles", "Particles", "Particle system emitter"),
        ],
        default="sphere",
    )
    
    emitter_radius: FloatProperty(
        name="Emitter Radius",
        description="Radius of the spherical emitter",
        default=10.0,
        min=0.01,
        subtype="DISTANCE",
    )
    
    emitter_temperature: FloatProperty(
        name="Emitter Temperature",
        description="Temperature of emitted smoke",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    
    emitter_smoke: FloatProperty(
        name="Smoke Density",
        description="Density of emitted smoke",
        default=1.0,
        min=0.0,
        soft_max=5.0,
    )
    
    emitter_velocity_y: FloatProperty(
        name="Emitter Velocity Y",
        description="Initial velocity in Y direction",
        default=10.0,
    )
    
    # Smoke Parameters
    couple_rate_smoke: FloatProperty(
        name="Smoke Coupling Rate",
        description="How much smoke enters the grid per frame",
        default=2.0,
        min=0.0,
        soft_max=10.0,
    )
    
    # Simulation Settings
    frame_count: IntProperty(
        name="Frame Count",
        description="Number of frames to simulate",
        default=60,
        min=1,
    )
    
    velocity: FloatVectorProperty(
        name="Initial Velocity",
        description="Initial velocity vector for emitted smoke",
        default=(0.0, 20.0, 0.0),
        size=3,
        subtype="VELOCITY",
    )
    
    resolution: IntProperty(
        name="Resolution",
        description="Grid resolution for simulation",
        default=64,
        min=16,
        max=512,
    )
    
    # Output Settings
    output_prefix: StringProperty(
        name="Output Prefix",
        description="Prefix for output files",
        default="smoke_",
    )
    
    output_dir: StringProperty(
        name="Output Directory",
        description="Directory for output files",
        default="",
        subtype="DIR_PATH",
    )
    
    # Object References
    mesh_object: PointerProperty(
        name="Mesh Object",
        description="Mesh object to use as emitter (for mesh emitter type)",
        type=bpy.types.Object,
    )
    
    particle_system_name: StringProperty(
        name="Particle System",
        description="Name of the particle system to use as emitter (for particles emitter type)",
        default="",
    )
    
    # Advanced Settings
    gravity: FloatVectorProperty(
        name="Gravity",
        description="Gravity vector for simulation",
        default=(0.0, -9.81, 0.0),
        size=3,
        subtype="ACCELERATION",
    )
    
    turbulence: FloatProperty(
        name="Turbulence",
        description="Turbulence strength",
        default=0.0,
        min=0.0,
        max=10.0,
    )
    
    vorticity: FloatProperty(
        name="Vorticity",
        description="Vorticity confinement strength",
        default=0.0,
        min=0.0,
        max=10.0,
    )
    
    dissipation: FloatProperty(
        name="Dissipation",
        description="Smoke dissipation rate",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    
    # Simulation State
    simulation_state: EnumProperty(
        name="Simulation State",
        description="Current state of the simulation",
        items=[
            ("idle", "Idle", "No simulation running"),
            ("baking", "Baking", "Simulation is baking"),
            ("baked", "Baked", "Simulation has been baked"),
            ("stopped", "Stopped", "Simulation was stopped"),
        ],
        default="idle",
    )
    
    baked_frames: IntProperty(
        name="Baked Frames",
        description="Number of frames that have been baked",
        default=0,
        min=0,
    )


def register():
    # Unregister first if already registered (handles re-enable after disable)
    try:
        bpy.utils.unregister_class(PhysXSmokeProperties)
    except RuntimeError:
        pass  # Not registered, that's fine
    bpy.utils.register_class(PhysXSmokeProperties)
    bpy.types.Scene.physx_smoke = PointerProperty(type=PhysXSmokeProperties)


def unregister():
    # Remove scene property if it exists
    if hasattr(bpy.types.Scene, 'physx_smoke'):
        del bpy.types.Scene.physx_smoke
    try:
        bpy.utils.unregister_class(PhysXSmokeProperties)
    except RuntimeError:
        pass  # Already unregistered


if __name__ == "__main__":
    register()
