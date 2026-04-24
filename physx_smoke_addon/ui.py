import bpy
from bpy.types import Panel
from .properties import PhysXSmokeProperties


class PHYSX_PT_smoke_simulation(Panel):
    """Main panel for PhysX smoke simulation in the Physics tab."""
    bl_label = "PhysX Smoke Simulation"
    bl_idname = "PHYSX_PT_smoke_simulation"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "PHYSICS"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.physx_smoke

        # Control Buttons
        box = layout.box()
        row = box.row(align=True)
        row.operator("physx_smoke.bake", icon="PLAY", text="Bake")
        row.operator("physx_smoke.stop", icon="PAUSE", text="Stop")
        row.operator("physx_smoke.continue_bake", icon="FF", text="Continue")
        row.operator("physx_smoke.delete_baked", icon="TRASH", text="Delete")

        # Simulation State Display
        if props.simulation_state == "baking":
            box.label(text=f"Baking... Frame {props.baked_frames}/{props.frame_count}", icon="ANIM")
        elif props.simulation_state == "baked":
            box.label(text=f"Simulation baked ({props.baked_frames} frames)", icon="CHECKMARK")
        elif props.simulation_state == "stopped":
            box.label(text=f"Simulation stopped at frame {props.baked_frames}", icon="PAUSE")

        # Emitter Settings
        box = layout.box()
        box.prop(props, "emitter_type", icon="EMITTER")

        # Conditional emitter settings
        if props.emitter_type == "sphere":
            box.prop(props, "emitter_radius")
        elif props.emitter_type == "mesh":
            box.prop(props, "mesh_object", icon="MESH_DATA")
        elif props.emitter_type == "particles":
            box.prop(props, "particle_system_name", icon="PARTICLE_DATA")

        box.prop(props, "emitter_temperature")
        box.prop(props, "emitter_smoke")
        box.prop(props, "emitter_velocity_y")

        # Smoke Parameters
        box = layout.box()
        box.label(text="Smoke Parameters", icon="SMOKE")
        box.prop(props, "couple_rate_smoke")
        box.prop(props, "nanoVdb_couple_rate")
        box.prop(props, "velocity")

        # Simulation Settings
        box = layout.box()
        box.label(text="Simulation Settings", icon="SETTINGS")
        box.prop(props, "frame_count")
        box.prop(props, "resolution")
        box.prop(props, "output_prefix")
        box.prop(props, "output_dir")

        # Advanced Settings
        box = layout.box()
        box.label(text="Advanced", icon="TOOL_SETTINGS")
        box.prop(props, "gravity")
        box.prop(props, "turbulence")
        box.prop(props, "vorticity")
        box.prop(props, "dissipation")


def register():
    try:
        bpy.utils.unregister_class(PHYSX_PT_smoke_simulation)
    except RuntimeError:
        pass
    bpy.utils.register_class(PHYSX_PT_smoke_simulation)


def unregister():
    try:
        bpy.utils.unregister_class(PHYSX_PT_smoke_simulation)
    except RuntimeError:
        pass


if __name__ == "__main__":
    register()
