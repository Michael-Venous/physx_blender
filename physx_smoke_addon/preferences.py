import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty


class PhysXSmokePreferences(AddonPreferences):
    """Addon preferences for PhysX Smoke Simulation."""
    bl_idname = __package__.split('.')[0] if '.' in __package__ else __package__
    
    executable_path: StringProperty(
        name="Executable Path",
        description="Path to the PhysX smoke simulation executable (leave empty to use bundled)",
        default="",
        subtype="FILE_PATH",
    )
    
    library_path: StringProperty(
        name="Library Path",
        description="Path to additional libraries (leave empty to use bundled)",
        default="",
        subtype="DIR_PATH",
    )
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Simulation Executable", icon="FILE_SCRIPT")
        box.prop(self, "executable_path")
        box.label(text="Leave empty to use the bundled executable in the addon's bin/ directory.", icon="INFO")
        
        box = layout.box()
        box.label(text="Library Path", icon="LIBRARY_DATA_DIRECT")
        box.prop(self, "library_path")
        box.label(text="Leave empty to use bundled libraries.", icon="INFO")


def register():
    try:
        bpy.utils.unregister_class(PhysXSmokePreferences)
    except RuntimeError:
        pass
    bpy.utils.register_class(PhysXSmokePreferences)


def unregister():
    try:
        bpy.utils.unregister_class(PhysXSmokePreferences)
    except RuntimeError:
        pass


if __name__ == "__main__":
    register()
