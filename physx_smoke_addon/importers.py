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

    remove_imported_volumes(prefix)

    pattern = os.path.join(directory, f"{prefix}*.vdb")
    vdb_files = sorted(glob.glob(pattern))
    if not vdb_files:
        pattern = os.path.join(directory, f"{prefix}*.nvdb")
        vdb_files = sorted(glob.glob(pattern))
    
    if not vdb_files:
        logger.warning(f"No VDB files found matching pattern: {pattern}")
        return []
    
    if len(vdb_files) == 1:
        return import_single_vdb(vdb_files[0])
    
    first_file = vdb_files[0]
    first_fname = os.path.basename(first_file)

    try:
        bpy.ops.object.volume_import(
            filepath=first_file,
            files=[{"name": os.path.basename(f)} for f in vdb_files],
            directory=directory,
            use_sequence_detection=True,
        )
    except Exception as e:
        logger.error(f"volume_import sequence failed: {e}")
        return []

    imported = []
    for obj in bpy.context.selected_objects:
        if obj.type == 'VOLUME':
            imported.append(obj)
            logger.info(f"Imported volume: {obj.name}")
            obj.data.update_tag()
            obj.data.reload()

    logger.info(f"Imported {len(imported)} volume objects")
    return imported


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
    
    try:
        bpy.ops.object.volume_import(
            filepath=filepath,
            files=[{"name": filename}],
            directory=os.path.dirname(filepath),
            use_sequence_detection=False,
        )
        
        for obj in bpy.context.selected_objects:
            if obj.type == 'VOLUME':
                obj.data.update_tag()
                obj.data.reload()
                logger.info(f"Imported {filepath} as '{obj.name}'")
                return obj
    except Exception as e:
        logger.warning(f"volume_import failed: {e}")
    
    try:
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
