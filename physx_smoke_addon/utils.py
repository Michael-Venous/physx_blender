import os
import bpy
import tempfile
import shutil
import subprocess
import logging
from pathlib import Path
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_addon_directory():
    """Get the directory where this addon is installed."""
    return os.path.dirname(os.path.abspath(__file__))


def get_bundled_bin_path():
    """Returns path to bundled executable (inside addon's bin/ directory)."""
    return os.path.join(get_addon_directory(), "bin")


def get_bundled_lib_path():
    """Returns path to bundled libraries."""
    return os.path.join(get_addon_directory(), "bin", "libs")


def get_executable_path():
    """Get the path to the simulation executable."""
    bin_path = get_bundled_bin_path()
    exe_name = "flow_to_nvdb_minimal"
    
    # Check for preferences override
    prefs = bpy.context.preferences.addons.get(__package__.split('.')[0])
    if prefs and prefs.preferences.executable_path:
        return prefs.preferences.executable_path
    
    # Default to bundled executable
    exe_path = os.path.join(bin_path, exe_name)
    if os.path.exists(exe_path):
        return exe_path
    
    return None


@contextmanager
def temp_dir(prefix="physx_smoke_"):
    """Context manager for temporary directory."""
    tmpdir = tempfile.mkdtemp(prefix=prefix)
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_simulation(cmd, env=None, cwd=None):
    """
    Run simulation subprocess with logging.
    
    Args:
        cmd: List of command arguments
        env: Optional environment variables dict
        cwd: Optional working directory
    
    Returns:
        subprocess.CompletedProcess instance
    """
    logger.info(f"Running simulation: {' '.join(cmd)}")
    
    # Set up environment
    if env is None:
        env = os.environ.copy()
    
    # Add bundled library path to LD_LIBRARY_PATH
    lib_path = get_bundled_lib_path()
    if os.path.exists(lib_path):
        current_ld_path = env.get("LD_LIBRARY_PATH", "")
        if current_ld_path:
            env["LD_LIBRARY_PATH"] = f"{lib_path}:{current_ld_path}"
        else:
            env["LD_LIBRARY_PATH"] = lib_path
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd,
            check=False,
        )
        
        # Log output
        if result.stdout:
            logger.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.warning(f"STDERR: {result.stderr}")
        
        return result
    except FileNotFoundError as e:
        logger.error(f"Executable not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise


def show_message_box(message, title="PhysX Smoke", icon="INFO"):
    """Show a message box in Blender."""
    def draw(self, context):
        self.layout.label(text=message)
    
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def validate_simulation_inputs(props):
    """
    Validate simulation parameters before baking.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not props.output_dir:
        return False, "Output directory is not set"
    
    
    if props.frame_count < 1:
        return False, "Frame count must be at least 1"
    
    if props.emitter_type == "mesh" and not props.mesh_object:
        return False, "Mesh object is required for mesh emitter type"
    
    if props.emitter_type == "particles" and not props.particle_system:
        return False, "Particle system is required for particles emitter type"
    
    exe_path = get_executable_path()
    if not exe_path:
        return False, "Simulation executable not found. Please check addon preferences."
    
    if not os.path.exists(exe_path):
        return False, f"Simulation executable not found at: {exe_path}"
    
    return True, ""


def cleanup_baked_data(output_dir, prefix):
    """Delete all baked VDB files from the output directory."""
    if not os.path.exists(output_dir):
        return
    
    count = 0
    for filename in os.listdir(output_dir):
        if filename.startswith(prefix) and filename.endswith((".nvdb", ".vdb")):
            filepath = os.path.join(output_dir, filename)
            try:
                os.remove(filepath)
                count += 1
            except OSError as e:
                logger.error(f"Failed to delete {filepath}: {e}")
    
    logger.info(f"Cleaned up {count} baked files")
    return count
