bl_info = {
    "name": "PhysX Smoke Simulation",
    "author": "PhysX Team",
    "version": (1, 1, 0),
    "blender": (5, 0, 0),
    "location": "Properties > Physics > PhysX Smoke Simulation",
    "description": "PhysX-based smoke simulation with OpenVDB output",
    "category": "Physics",
}

import bpy
from . import properties
from . import ui
from . import operators
from . import preferences


def menu_func(self, context):
    """Add menu item to Physics panel."""
    self.layout.operator("physx_smoke.bake", text="PhysX Smoke Simulation")


def register():
    """Register all addon classes and properties."""
    properties.register()
    ui.register()
    operators.register()
    preferences.register()

    physics_menu = getattr(bpy.types, 'PHYSICS_PT_add',
                           getattr(bpy.types, 'PHYSICS_MT_add', None))
    if physics_menu:
        try:
            physics_menu.remove(menu_func)
        except (ValueError, AttributeError):
            pass
        physics_menu.append(menu_func)


def unregister():
    """Unregister all addon classes and properties."""
    physics_menu = getattr(bpy.types, 'PHYSICS_PT_add',
                           getattr(bpy.types, 'PHYSICS_MT_add', None))
    if physics_menu:
        try:
            physics_menu.remove(menu_func)
        except (ValueError, AttributeError):
            pass

    preferences.unregister()
    operators.unregister()
    ui.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
