import bpy
import mathutils
from mathutils import Vector
import math

def srgb_to_linearrgb(c):
    if   c < 0:       return 0
    elif c < 0.04045: return c/12.92
    else:             return ((c+0.055)/1.055)**2.4

def hex_to_rgb(h,alpha=1):
    r = (h & 0xff0000) >> 16
    g = (h & 0x00ff00) >> 8
    b = (h & 0x0000ff)
    return tuple([srgb_to_linearrgb(c/0xff) for c in (r,g,b)] + [alpha])

bpy.ops.mesh.primitive_monkey_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
monkey = bpy.context.active_object
bpy.ops.object.subdivision_set(level=2, relative=False)
bpy.ops.object.shade_smooth()
hex_to_rgb(0xff7800)

material = bpy.data.materials.new(name="Hole")
material.use_nodes = True
node_tree = material.node_tree
nodes = material.node_tree.nodes
links = material.node_tree.links

nodes.clear()
output_node = nodes.new(type='ShaderNodeOutputMaterial')
# mix shader
diffuse_node = material.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')
diffuse_node.inputs['Color'].default_value = hex_to_rgb(0xff7800)
glossy_node = nodes.new(type='ShaderNodeBsdfGlossy')
glossy_node.inputs['Roughness'].default_value = 0.1
layer_weight = material.node_tree.nodes.new(type='ShaderNodeLayerWeight')
layer_weight.inputs['Blend'].default_value = 0.1
mix_node = nodes.new(type='ShaderNodeMixShader')
links.new(mix_node.inputs[0], layer_weight.outputs['Facing'])
links.new(mix_node.inputs[1], diffuse_node.outputs[0]) 
links.new(mix_node.inputs[2], glossy_node.outputs[0])

noise_node = material.node_tree.nodes.new(type='ShaderNodeTexNoise')
# hole in the right
noise_node.noise_dimensions = '2D'
noise_node.inputs['Scale'].default_value = 1
# hole in the left
#noise_node.noise_dimensions = '3D'
#noise_node.inputs['Scale'].default_value = 1.1
noise_node.inputs['Detail'].default_value = 16.0

math_node = material.node_tree.nodes.new(type='ShaderNodeMath')
math_node.operation = 'GREATER_THAN'
# greater this value will use transparent node, cause holes
#math_node.inputs[1].default_value = 0.65
math_node.inputs[1].default_value = 0.68
math_node.inputs[1].keyframe_insert("default_value", frame=1)
math_node.inputs[1].default_value = 0.54
math_node.inputs[1].keyframe_insert("default_value", frame=100)
links.new(math_node.inputs[0], noise_node.outputs['Color'])

transparent_node = material.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
hole = nodes.new(type='ShaderNodeMixShader')
links.new(hole.inputs[0], math_node.outputs[0])
links.new(hole.inputs[1], mix_node.outputs[0]) 
links.new(hole.inputs[2], transparent_node.outputs[0])

links.new(hole.outputs[0], output_node.inputs[0])
monkey.data.materials.append(material)
bpy.context.object.active_material.blend_method = 'HASHED'

bpy.ops.object.modifier_add(type='SOLIDIFY')
bpy.context.object.modifiers["Solidify"].thickness = 0.05
# add wireframe in the middle
bpy.ops.object.modifier_add(type='WIREFRAME')
bpy.context.object.modifiers["Wireframe"].use_even_offset = False
bpy.context.object.modifiers["Wireframe"].use_replace = False
bpy.context.object.modifiers["Wireframe"].offset = -1
bpy.context.object.modifiers["Wireframe"].thickness = 0.05/2

bpy.context.scene.frame_end = 120
bpy.context.scene.render.fps = 30
bpy.context.scene.frame_current = 1
monkey.rotation_euler = mathutils.Euler((0.0, 0.0, 0.0), 'XYZ')
monkey.keyframe_insert(data_path='rotation_euler')
bpy.context.scene.frame_current = 90
monkey.rotation_euler = mathutils.Euler((0.0, 0.0, math.radians(-90)), 'XYZ')
monkey.keyframe_insert(data_path='rotation_euler')
bpy.context.scene.frame_current = 120
monkey.rotation_euler = mathutils.Euler((0.0, 0.0, math.radians(-270)), 'XYZ')
monkey.keyframe_insert(data_path='rotation_euler')
bpy.context.scene.frame_current = 1

# change interpolation to BEZIER
fcurves = monkey.animation_data.action.fcurves
for fcurve in fcurves:
    for kf in fcurve.keyframe_points:
        kf.interpolation = 'BEZIER'

# set world to black
#bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = hex_to_rgb(0x4C5124)

# set camera
camera = bpy.data.objects['Camera']
camera.location = Vector((7, 0, 0))
camera.rotation_euler = mathutils.Euler((math.radians(90.0), 0.0, math.radians(90.0)), 'XYZ')
