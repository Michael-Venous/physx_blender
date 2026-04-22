import os
import bpy
import glob
import logging

logger = logging.getLogger(__name__)


def import_vdb_sequence(directory, prefix):
    """
    Import OpenVDB sequence as volume objects.
    
    Args:
        directory: Directory containing VDB files
        prefix: File prefix for VDB files
    
    Returns:
        list: List of imported volume objects
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    # Find all matching VDB files
    pattern = os.path.join(directory, f"{prefix}*.vdb")
    vdb_files = sorted(glob.glob(pattern))
    
    if not vdb_files:
        # Try .nvdb extension as fallback (older versions)
        pattern = os.path.join(directory, f"{prefix}*.nvdb")
        vdb_files = sorted(glob.glob(pattern))
    
    if not vdb_files:
        logger.warning(f"No VDB files found matching pattern: {pattern}")
        return []
    
    imported_objects = []
    
    for vdb_file in vdb_files:
        try:
            obj = import_single_vdb(vdb_file)
            if obj:
                imported_objects.append(obj)
        except Exception as e:
            logger.error(f"Failed to import {vdb_file}: {e}")
    
    logger.info(f"Imported {len(imported_objects)} VDB files")
    return imported_objects


def import_single_vdb(filepath):
    """
    Import a single VDB file as a volume object.
    
    Args:
        filepath: Path to VDB file
    
    Returns:
        bpy.types.Object: Imported volume object or None
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    filename = os.path.basename(filepath)
    obj_name = os.path.splitext(filename)[0]
    
    # Try using Blender's OpenVDB import operator
    try:
        # For Blender 4.1+ with native OpenVDB support
        bpy.ops.wm.openvdb_import(
            filepath=filepath,
            files=[{"name": filename}],
            directory=os.path.dirname(filepath),
        )
        
        # Get the imported object
        obj = bpy.data.objects.get(obj_name)
        if obj:
            logger.info(f"Imported {filepath} as '{obj_name}'")
            return obj
    except AttributeError:
        # openvdb_import not available, try alternative method
        pass
    except Exception as e:
        logger.warning(f"openvdb_import failed: {e}")
    
    # Fallback: Create a placeholder volume object
    # This creates a mesh object that references the VDB file
    # In practice, users should have OpenVDB support enabled
    try:
        # Create an empty to represent the volume
        obj = bpy.data.objects.new(obj_name, None)
        obj.empty_display_type = "CUBE"
        obj["vdb_path"] = filepath
        obj["is_physx_volume"] = True
        bpy.context.collection.objects.link(obj)
        logger.info(f"Created placeholder object for {filepath}")
        return obj
    except Exception as e:
        logger.error(f"Failed to create placeholder: {e}")
        return None


def link_vdb_to_scene(obj, vdb_path):
    """
    Link a VDB file to an existing object as a volume modifier.
    
    Args:
        obj: Blender object to link to
        vdb_path: Path to VDB file
    """
    if obj is None:
        raise ValueError("Invalid object")
    
    obj["vdb_path"] = vdb_path
    obj["is_physx_volume"] = True
    
    logger.info(f"Linked {vdb_path} to object '{obj.name}'")


def remove_imported_volumes(prefix):
    """
    Remove all volume objects with the given prefix.
    
    Args:
        prefix: Object name prefix
    
    Returns:
        int: Number of objects removed
    """
    count = 0
    for obj in bpy.data.objects:
        if obj.name.startswith(prefix) and obj.get("is_physx_volume"):
            name = obj.name
            bpy.data.objects.remove(obj)
            count += 1
            logger.info(f"Removed volume object: {name}")
    
    return count
