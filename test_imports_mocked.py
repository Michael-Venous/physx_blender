#!/usr/bin/env python3
"""
Test script to verify PhysX Smoke addon module imports with a mocked bpy module.
This script creates a dummy bpy module and imports each addon module to check
for syntax errors and missing dependencies.
"""

import sys
import types
import importlib
import os

# Add the parent directory to the path so we can import physx_smoke_addon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_mock_bpy():
    """Create a comprehensive mock bpy module with all necessary submodules."""
    
    # Create the main bpy module
    bpy = types.ModuleType("bpy")
    
    # Create bpy.types
    bpy_types = types.ModuleType("bpy.types")
    
    # Mock base classes
    class MockPropertyGroup:
        pass
    
    class MockOperator:
        bl_idname = ""
        bl_label = ""
        bl_description = ""
        bl_options = set()
    
    class MockPanel:
        bl_label = ""
        bl_idname = ""
        bl_space_type = ""
        bl_region_type = ""
        bl_context = ""
        bl_category = ""
        bl_options = set()
        
        @classmethod
        def poll(cls, context):
            return True
    
    class MockAddonPreferences:
        bl_idname = ""
    
    bpy_types.PropertyGroup = MockPropertyGroup
    bpy_types.Operator = MockOperator
    bpy_types.Panel = MockPanel
    bpy_types.AddonPreferences = MockAddonPreferences
    
    # Mock bpy.types.PHYSICS_MT_add
    class MockMenu:
        @staticmethod
        def append(func):
            pass
        @staticmethod
        def remove(func):
            pass
    
    bpy_types.PHYSICS_MT_add = MockMenu()
    
    bpy.types = bpy_types
    
    # Create bpy.props
    bpy_props = types.ModuleType("bpy.props")
    
    def mock_property(**kwargs):
        return type('MockProperty', (), kwargs)
    
    bpy_props.EnumProperty = mock_property
    bpy_props.FloatProperty = mock_property
    bpy_props.FloatVectorProperty = mock_property
    bpy_props.IntProperty = mock_property
    bpy_props.StringProperty = mock_property
    bpy_props.PointerProperty = mock_property
    bpy_props.BoolProperty = mock_property
    
    bpy.props = bpy_props
    
    # Create bpy.context mock
    class MockPreferences:
        class MockAddonPrefs:
            executable_path = ""
            library_path = ""
        
        class MockAddonsDict(dict):
            def get(self, key, default=None):
                mock_addon = types.SimpleNamespace()
                mock_addon.preferences = self.MockAddonPrefs()
                return mock_addon
        
        addons = MockAddonsDict()
    
    class MockContext:
        preferences = MockPreferences()
        scene = None
    
    bpy.context = MockContext()
    
    # Create bpy.ops mock
    bpy_ops = types.ModuleType("bpy.ops")
    
    class MockOpsModule:
        def __getattr__(self, name):
            return self
        
        def __call__(self, **kwargs):
            return {'FINISHED'}
    
    bpy_ops.object = MockOpsModule()
    bpy_ops.wm = MockOpsModule()
    bpy.ops = bpy_ops
    
    # Create bpy.utils
    bpy_utils = types.ModuleType("bpy.utils")
    
    def register_class(cls):
        pass
    
    def unregister_class(cls):
        pass
    
    bpy_utils.register_class = register_class
    bpy_utils.unregister_class = unregister_class
    
    bpy.utils = bpy_utils
    
    return bpy


def test_imports():
    """Test importing all addon modules with mocked bpy."""
    
    print("=" * 60)
    print("Testing PhysX Smoke Addon Module Imports (Mocked bpy)")
    print("=" * 60)
    
    # Install mock bpy
    mock_bpy = create_mock_bpy()
    sys.modules["bpy"] = mock_bpy
    sys.modules["bpy.types"] = mock_bpy.types
    sys.modules["bpy.props"] = mock_bpy.props
    sys.modules["bpy.utils"] = mock_bpy.utils
    sys.modules["bpy.ops"] = mock_bpy.ops
    sys.modules["bpy.context"] = mock_bpy.context
    
    modules_to_test = [
        "physx_smoke_addon.properties",
        "physx_smoke_addon.ui",
        "physx_smoke_addon.utils",
        "physx_smoke_addon.exporters",
        "physx_smoke_addon.importers",
        "physx_smoke_addon.preferences",
        "physx_smoke_addon.operators",
        "physx_smoke_addon",  # __init__.py
    ]
    
    results = {}
    all_passed = True
    
    for module_name in modules_to_test:
        try:
            # Clear any cached imports
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            mod = importlib.import_module(module_name)
            results[module_name] = ("PASS", "Imported successfully")
            print(f"  [PASS] {module_name}")
        except SyntaxError as e:
            results[module_name] = ("FAIL", f"Syntax error: {e}")
            print(f"  [FAIL] {module_name} - Syntax error: {e}")
            all_passed = False
        except ImportError as e:
            results[module_name] = ("FAIL", f"Import error: {e}")
            print(f"  [FAIL] {module_name} - Import error: {e}")
            all_passed = False
        except Exception as e:
            results[module_name] = ("FAIL", f"Unexpected error: {type(e).__name__}: {e}")
            print(f"  [FAIL] {module_name} - {type(e).__name__}: {e}")
            all_passed = False
    
    print()
    print("=" * 60)
    if all_passed:
        print("RESULT: All modules imported successfully!")
    else:
        print("RESULT: Some modules failed to import. See details above.")
    print("=" * 60)
    
    return all_passed, results


if __name__ == "__main__":
    success, results = test_imports()
    sys.exit(0 if success else 1)
