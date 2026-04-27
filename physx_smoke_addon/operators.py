import os
import bpy
import threading
import logging
from bpy.types import Operator
from bpy.props import StringProperty
from .utils import (
    get_executable_path,
    get_bundled_lib_path,
    temp_dir,
    run_simulation_async,
    show_message_box,
    validate_simulation_inputs,
    cleanup_baked_data,
)
from .exporters import build_command_args
from .importers import import_vdb_sequence

logger = logging.getLogger(__name__)


class BAKE_OT_physx_smoke(Operator):
    """Bake the PhysX smoke simulation."""
    bl_idname = "physx_smoke.bake"
    bl_label = "Bake Simulation"
    bl_description = "Bake the smoke simulation"
    bl_options = {"REGISTER", "UNDO"}
    
    _timer = None
    _running = False
    _process = None
    _result = None
    _thread = None
    _tmpdir = None

    def _run_subprocess(self, cmd, env, cwd):
        try:
            process = run_simulation_async(cmd, env=env, cwd=cwd)
            self._process = process
            stdout, stderr = process.communicate()
            self._result = type("Result", (), {
                "returncode": process.returncode,
                "stdout": stdout or "",
                "stderr": stderr or "",
            })()
        except Exception as e:
            self._result = type("Result", (), {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            })()

    def modal(self, context, event):
        if event.type == "TIMER":
            props = context.scene.physx_smoke

            if self._result is not None:
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                if self._thread:
                    self._thread.join(timeout=1.0)
                    self._thread = None

                if self._tmpdir:
                    import shutil
                    shutil.rmtree(self._tmpdir, ignore_errors=True)
                    self._tmpdir = None

                if self._result.returncode == 0:
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
                        logger.error(f"Import failed: {e}")
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
                self._process = None
                return {"FINISHED"}

            if props.simulation_state == "stopped" and self._process is not None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except Exception:
                    self._process.kill()
                self._process = None
                if self._tmpdir:
                    import shutil
                    shutil.rmtree(self._tmpdir, ignore_errors=True)
                    self._tmpdir = None
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                self._running = False
                return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        props = context.scene.physx_smoke

        is_valid, error_msg = validate_simulation_inputs(props)
        if not is_valid:
            show_message_box(error_msg, "Validation Error", "ERROR")
            return {"CANCELLED"}

        exe_path = get_executable_path()
        if not exe_path:
            show_message_box("Simulation executable not found. Please check addon preferences.", "Error", "ERROR")
            return {"CANCELLED"}

        env = os.environ.copy()
        lib_path = get_bundled_lib_path()
        if os.path.exists(lib_path):
            current_ld_path = env.get("LD_LIBRARY_PATH", "")
            if current_ld_path:
                env["LD_LIBRARY_PATH"] = f"{lib_path}:{current_ld_path}"
            else:
                env["LD_LIBRARY_PATH"] = lib_path

        import tempfile
        self._tmpdir = tempfile.mkdtemp(prefix="physx_smoke_")

        try:
            cmd_args, _ = build_command_args(props, self._tmpdir)
            cmd = [exe_path] + cmd_args
        except Exception as e:
            import shutil
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None
            show_message_box(f"Failed to build command: {e}", "Error", "ERROR")
            return {"CANCELLED"}

        self._result = None
        self._process = None
        self._thread = threading.Thread(
            target=self._run_subprocess, args=(cmd, env, self._tmpdir), daemon=True
        )
        self._thread.start()

        props.simulation_state = "baking"
        props.baked_frames = 0

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        self._running = True

        return {"RUNNING_MODAL"}

    def cancel(self, context):
        if self._running:
            if self._process:
                self._process.terminate()
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
            bpy.ops.physx_smoke.bake()
        elif props.simulation_state == "baked":
            bpy.ops.physx_smoke.bake()
        else:
            show_message_box("No stopped or baked simulation to continue.", "Info", "INFO")
        
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
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


if __name__ == "__main__":
    register()
