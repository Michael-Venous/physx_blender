#!/usr/bin/env python3
"""
Standalone test script for physx_smoke_addon utility functions.
Tests validation and cleanup functions without requiring Blender.
"""
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import MagicMock, patch

# Create mock bpy module before importing utils
sys.modules['bpy'] = MagicMock()
sys.modules['bpy.types'] = MagicMock()
sys.modules['bpy.props'] = MagicMock()
sys.modules['bpy.context'] = MagicMock()
sys.modules['bpy.utils'] = MagicMock()

# Now we can import the addon's utils
# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the __package__ for utils
import physx_smoke_addon
physx_smoke_addon.__package__ = 'physx_smoke_addon'

from physx_smoke_addon import utils


class MockProps:
    """Mock properties object for testing validation."""
    def __init__(self):
        self.output_dir = "/tmp/test_output"
        self.frame_count = 60
        self.emitter_type = "sphere"
        self.mesh_object = None
        self.particle_system = None


class TestValidateSimulationInputs(unittest.TestCase):
    """Test the validate_simulation_inputs function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.props = MockProps()
        # Create a fake executable path
        self.test_exe_dir = tempfile.mkdtemp()
        self.test_exe_path = os.path.join(self.test_exe_dir, "flow_to_nvdb_minimal")
        # Create a dummy executable file
        with open(self.test_exe_path, 'w') as f:
            f.write("#!/bin/bash\necho test\n")
        os.chmod(self.test_exe_path, 0o755)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_exe_dir, ignore_errors=True)
    
    def test_valid_inputs(self):
        """Test that valid inputs pass validation."""
        with patch.object(utils, 'get_executable_path', return_value=self.test_exe_path):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
    
    def test_missing_output_dir(self):
        """Test that missing output directory fails validation."""
        self.props.output_dir = ""
        with patch.object(utils, 'get_executable_path', return_value=self.test_exe_path):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertFalse(is_valid)
            self.assertIn("Output directory", error_msg)
    
    def test_zero_frame_count(self):
        """Test that zero frame count fails validation."""
        self.props.frame_count = 0
        with patch.object(utils, 'get_executable_path', return_value=self.test_exe_path):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertFalse(is_valid)
            self.assertIn("Frame count", error_msg)
    
    def test_negative_frame_count(self):
        """Test that negative frame count fails validation."""
        self.props.frame_count = -10
        with patch.object(utils, 'get_executable_path', return_value=self.test_exe_path):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertFalse(is_valid)
            self.assertIn("Frame count", error_msg)
    
    def test_mesh_emitter_without_mesh_object(self):
        """Test that mesh emitter without mesh object fails validation."""
        self.props.emitter_type = "mesh"
        self.props.mesh_object = None
        with patch.object(utils, 'get_executable_path', return_value=self.test_exe_path):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertFalse(is_valid)
            self.assertIn("Mesh object", error_msg)
    
    def test_mesh_emitter_with_mesh_object(self):
        """Test that mesh emitter with mesh object passes validation."""
        self.props.emitter_type = "mesh"
        self.props.mesh_object = MagicMock()  # Simulate a mesh object
        with patch.object(utils, 'get_executable_path', return_value=self.test_exe_path):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
    
    def test_particles_emitter_without_particle_system(self):
        """Test that particles emitter without particle system fails validation."""
        self.props.emitter_type = "particles"
        self.props.particle_system = None
        with patch.object(utils, 'get_executable_path', return_value=self.test_exe_path):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertFalse(is_valid)
            self.assertIn("Particle system", error_msg)
    
    def test_particles_emitter_with_particle_system(self):
        """Test that particles emitter with particle system passes validation."""
        self.props.emitter_type = "particles"
        self.props.particle_system = MagicMock()  # Simulate a particle system
        with patch.object(utils, 'get_executable_path', return_value=self.test_exe_path):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
    
    def test_missing_executable(self):
        """Test that missing executable fails validation."""
        with patch.object(utils, 'get_executable_path', return_value=None):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertFalse(is_valid)
            self.assertIn("executable not found", error_msg.lower())
    
    def test_nonexistent_executable_path(self):
        """Test that nonexistent executable path fails validation."""
        with patch.object(utils, 'get_executable_path', return_value="/nonexistent/path/exe"):
            is_valid, error_msg = utils.validate_simulation_inputs(self.props)
            self.assertFalse(is_valid)
            self.assertIn("not found", error_msg.lower())


class TestCleanupBakedData(unittest.TestCase):
    """Test the cleanup_baked_data function."""
    
    def setUp(self):
        """Set up test fixtures with temporary directory and test files."""
        self.test_dir = tempfile.mkdtemp(prefix="physx_smoke_test_")
        self.prefix = "smoke_"
        
        # Create test .vdb files
        for i in range(5):
            filepath = os.path.join(self.test_dir, f"{self.prefix}{i}.vdb")
            with open(filepath, 'w') as f:
                f.write("test data")
        
        # Create test .nvdb files
        for i in range(3):
            filepath = os.path.join(self.test_dir, f"{self.prefix}{i}.nvdb")
            with open(filepath, 'w') as f:
                f.write("test data")
        
        # Create a non-matching file (should not be deleted)
        self.other_file = os.path.join(self.test_dir, "other_file.txt")
        with open(self.other_file, 'w') as f:
            f.write("should not be deleted")
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_cleanup_vdb_files(self):
        """Test that cleanup removes .vdb files with matching prefix."""
        count = utils.cleanup_baked_data(self.test_dir, self.prefix)
        self.assertEqual(count, 8)  # 5 .vdb + 3 .nvdb
        
        # Verify matching files are removed
        for i in range(5):
            filepath = os.path.join(self.test_dir, f"{self.prefix}{i}.vdb")
            self.assertFalse(os.path.exists(filepath))
        
        for i in range(3):
            filepath = os.path.join(self.test_dir, f"{self.prefix}{i}.nvdb")
            self.assertFalse(os.path.exists(filepath))
        
        # Verify non-matching file still exists
        self.assertTrue(os.path.exists(self.other_file))
    
    def test_cleanup_nonexistent_directory(self):
        """Test that cleanup handles nonexistent directory gracefully."""
        count = utils.cleanup_baked_data("/nonexistent/directory", self.prefix)
        self.assertIsNone(count)
    
    def test_cleanup_empty_directory(self):
        """Test that cleanup handles empty directory correctly."""
        empty_dir = tempfile.mkdtemp(prefix="physx_smoke_empty_")
        try:
            count = utils.cleanup_baked_data(empty_dir, self.prefix)
            self.assertEqual(count, 0)
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)
    
    def test_cleanup_different_prefix(self):
        """Test that cleanup only removes files with matching prefix."""
        count = utils.cleanup_baked_data(self.test_dir, "different_prefix_")
        self.assertEqual(count, 0)
        
        # Verify all original files still exist
        for i in range(5):
            filepath = os.path.join(self.test_dir, f"{self.prefix}{i}.vdb")
            self.assertTrue(os.path.exists(filepath))


class TestTempDir(unittest.TestCase):
    """Test the temp_dir context manager."""
    
    def test_temp_dir_creation_and_cleanup(self):
        """Test that temp_dir creates and cleans up directory."""
        temp_path = None
        with utils.temp_dir(prefix="test_physx_") as tmpdir:
            temp_path = tmpdir
            self.assertTrue(os.path.exists(tmpdir))
            self.assertTrue(os.path.isdir(tmpdir))
            self.assertIn("test_physx_", tmpdir)
            
            # Create a file inside
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
        
        # Verify directory is cleaned up
        self.assertFalse(os.path.exists(temp_path))
    
    def test_temp_dir_cleanup_on_exception(self):
        """Test that temp_dir cleans up even on exception."""
        temp_path = None
        try:
            with utils.temp_dir(prefix="test_physx_exc_") as tmpdir:
                temp_path = tmpdir
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify directory is still cleaned up
        if temp_path:
            self.assertFalse(os.path.exists(temp_path))


class TestGetAddonDirectory(unittest.TestCase):
    """Test the get_addon_directory function."""
    
    def test_get_addon_directory(self):
        """Test that get_addon_directory returns a valid path."""
        addon_dir = utils.get_addon_directory()
        self.assertTrue(os.path.isdir(addon_dir))
        self.assertIn("physx_smoke_addon", addon_dir)


class TestGetBundledPaths(unittest.TestCase):
    """Test the bundled path functions."""
    
    def test_get_bundled_bin_path(self):
        """Test that get_bundled_bin_path returns correct path."""
        bin_path = utils.get_bundled_bin_path()
        self.assertIn("bin", bin_path)
    
    def test_get_bundled_lib_path(self):
        """Test that get_bundled_lib_path returns correct path."""
        lib_path = utils.get_bundled_lib_path()
        self.assertIn("libs", lib_path)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
