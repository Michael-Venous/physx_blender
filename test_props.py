import bpy

class TestProps(bpy.types.PropertyGroup):
    test_vec1: bpy.props.FloatVectorProperty(subtype="VELOCITY")
    test_vec2: bpy.props.FloatVectorProperty(subtype="ACCELERATION")

bpy.utils.register_class(TestProps)
