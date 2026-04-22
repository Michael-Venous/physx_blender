import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .utils import (
    get_executable_path,
    get_bundled_lib_path,
    temp_dir,
    run_simulation,
    show_message_box,
    validate_simulation_inputs,
    cleanup_baked_data,
)
from .exporters import build_command_args
from .importers import import_vdb_sequence


class BAKE_OT_physx_smoke(Operator):
    """Bake the PhysX smoke simulation."""
    bl_idname = "physx_smoke.bake"
    bl_label = "Bake Simulation"
    bl_description = "Bake the smoke simulation"
    bl_options = {"REGISTER", "UNDO"}
    
    _timer = None
    _running = False
    _result = None
    
    def modal(self, context, event):
        if event.type == "TIMER":
            if self._result is not None:
                # Simulation finished
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                
                props = context.scene.physx_smoke
                
                if self._result.returncode == 0:
                    # Import VDB sequence
                    try:
                        imported = import_vdb_sequence(props.output_dir, props.output_prefix)
                        props.simulation_state = "baked"
                        props.baked_frames = props.frame_count
                        show_message_box(
                            f"Simulation completed successfully! Imported {len(imported)} frames.",
                            "Bake Complete",
                            "CHECKMARK",
                        )
                    except Exception as e:
                        props.simulation_state = "idle"
                        show_message_box(
                            f"Simulation completed but import failed: {e}",
                            "Import Error",
                            "ERROR",
                        )
                else:
                    props.simulation_state = "idle"
                    show_message_box(
                        f"Simulation failed with return code {self._result.returncode}\n{self._result.stderr}",
                        "Simulation Error",
                        "ERROR",
                    )
                
                self._running = False
                return {"FINISHED"}
        
        return {"PASS_THROUGH"}
    
    def execute(self, context):
        props = context.scene.physx_smoke
        
        # Validate inputs
        is_valid, error_msg = validate_simulation_inputs(props)
        if not is_valid:
            show_message_box(error_msg, "Validation Error", "ERROR")
            return {"CANCELLED"}
        
        # Get executable path
        exe_path = get_executable_path()
        if not exe_path:
            show_message_box("Simulation executable not found. Please check addon preferences.", "Error", "ERROR")
            return {"CANCELLED"}
        
        # Set up environment
        env = os.environ.copy()
        lib_path = get_bundled_lib_path()
        if os.path.exists(lib_path):
            current_ld_path = env.get("LD_LIBRARY_PATH", "")
            if current_ld_path:
                env["LD_LIBRARY_PATH"] = f"{lib_path}:{current_ld_path}"
            else:
                env["LD_LIBRARY_PATH"] = lib_path
        
        # Build command
        with temp_dir() as tmpdir:
            try:
                cmd_args, files = build_command_args(props, tmpdir)
                cmd = [exe_path] + cmd_args
                
                # Run simulation synchronously for now
                # For long simulations, consider threading
                self._result = run_simulation(cmd, env=env, cwd=tmpdir)
                
                # Trigger modal to handle import
                props.simulation_state = "baking"
                props.baked_frames = 0
                
                wm = context.window_manager
                self._timer = wm.event_timer_add(0.1, window=context.window)
                wm.modal_handler_add(self)
                self._running = True
                
                return {"RUNNING_MODAL"}
                
            except Exception as e:
                show_message_box(f"Simulation failed: {e}", "Error", "ERROR")
                return {"CANCELLED"}
    
    def cancel(self, context):
        if self._running:
            props = context.scene.physx_smoke
            props.simulation_state = "idle"
            props.baked_frames = 0


class STOP_OT_physx_smoke(Operator):
    """Stop the current simulation bake."""
    bl_idname = "physx_smoke.stop"
    bl_label = "Stop Simulation"
    bl_description = "Stop the current simulation bake"
    
    def execute(self, context):
        props = context.scene.physx_smoke
        
        if props.simulation_state == "baking":
            props.simulation_state = "stopped"
            show_message_box("Simulation stopped.", "Stopped", "PAUSE")
        else:
            show_message_box("No simulation is currently running.", "Info", "INFO")
        
        return {"FINISHED"}


class CONTINUE_OT_physx_smoke(Operator):
    """Continue a stopped simulation bake."""
    bl_idname = "physx_smoke.continue_bake"
    bl_label = "Continue Simulation"
    bl_description = "Continue a stopped simulation bake"
    
    def execute(self, context):
        props = context.scene.physx_smoke
        
        if props.simulation_state == "stopped":
            # Restart from where we left off
            props.simulation_state = "idle"
            # Trigger bake operator
            bpy.ops.physx_smoke.bake()
        else:
            show_message_box("No stopped simulation to continue.", "Info", "INFO")
        
        return {"FINISHED"}


class DELETE_OT_physx_smoke_baked(Operator):
    """Delete baked simulation data."""
    bl_idname = "physx_smoke.delete_baked"
    bl_label = "Delete Baked Data"
    bl_description = "Delete baked simulation files and volume objects"
    
    def execute(self, context):
        props = context.scene.physx_smoke
        
        # Clean up files
        if props.output_dir:
            count = cleanup_baked_data(props.output_dir, props.output_prefix)
            if count:
                self.report({"INFO"}, f"Deleted {count} baked files")
        
        # Remove imported volume objects
        from .importers import remove_imported_volumes
        removed = remove_imported_volumes(props.output_prefix)
        if removed:
            self.report({"INFO"}, f"Removed {removed} volume objects")
        
        # Reset state
        props.simulation_state = "idle"
        props.baked_frames = 0
        
        show_message_box("Baked data deleted.", "Deleted", "TRASH")
        return {"FINISHED"}


# Registration
classes = (
    BAKE_OT_physx_smoke,
    STOP_OT_physx_smoke,
    CONTINUE_OT_physx_smoke,
    DELETE_OT_physx_smoke_baked,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
