import bpy
import mathutils
from mathutils import Vector
import math

def eulerToDegree(euler):
    return ( (euler) / (2 * math.pi) ) * 360

def degreeToEuler(degree):
    return degree / 180 * math.pi

def srgb_to_linearrgb(c):
    if   c < 0:       return 0
    elif c < 0.04045: return c/12.92
    else:             return ((c+0.055)/1.055)**2.4

def hex_to_rgb(h,alpha=1):
    r = (h & 0xff0000) >> 16
    g = (h & 0x00ff00) >> 8
    b = (h & 0x0000ff)
    return tuple([srgb_to_linearrgb(c/0xff) for c in (r,g,b)] + [alpha])

def math_node(nodes, operation):
    math_node = nodes.new(type='ShaderNodeMath')
    math_node.operation = operation
    return math_node

def render(engine, frame_end, samples=32):
    scene = bpy.context.scene
    scene.frame_end = frame_end
    scene.render.fps = 30
    scene.frame_current = 1
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.engine = engine
    if (engine == 'CYCLES'):
        scene.cycles.preview_samples = samples
        scene.cycles.samples = samples

def background_settings(color=(0, 0, 0, 1), image_path="C:/Program Files/Blender Foundation/Blender 4.1/4.1/datafiles/studiolights/world/forest.exr", strength=1):
    nodes = bpy.data.worlds["World"].node_tree.nodes
    links = bpy.data.worlds["World"].node_tree.links

    background = nodes["Background"]
    background.inputs['Strength'].default_value = strength
    if (color == 'TexSky'):
        sky_node = nodes.new(type='ShaderNodeTexSky')
        sky_node.sky_type = 'HOSEK_WILKIE'
        links.new(sky_node.outputs[0], background.inputs['Color'])
    elif (color == 'TexEnvironment'):
        env_node = nodes.new(type='ShaderNodeTexEnvironment')
        image = bpy.data.images.load(image_path)
        env_node.image = image
        links.new(env_node.outputs[0], background.inputs['Color'])
    else:
        background.inputs[0].default_value = color

def chipped_material():
    material = bpy.data.materials.new(name="chipped")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node.inputs['Base Color'].default_value = hex_to_rgb(0xff0000)
    principled_node1 = nodes.new(type='ShaderNodeBsdfPrincipled')
    #principled_node1.inputs['Base Color'].default_value = chipped_color

    noise_node = material.node_tree.nodes.new(type='ShaderNodeTexNoise')
    noise_node.inputs['Scale'].default_value = 5
    # large value, edge jagged, rough, detail
    noise_node.inputs['Detail'].default_value = 10
    # animation
    noise_node.inputs['Scale'].default_value = 5
    noise_node.inputs['Detail'].default_value = 5
    noise_node.inputs['Scale'].keyframe_insert("default_value", frame=1)
    noise_node.inputs['Detail'].keyframe_insert("default_value", frame=1)
    noise_node.inputs['Scale'].default_value = 20
    noise_node.inputs['Detail'].default_value = 0
    noise_node.inputs['Scale'].keyframe_insert("default_value", frame=120)
    noise_node.inputs['Detail'].keyframe_insert("default_value", frame=120)
    noise_node.inputs['Scale'].default_value = 5
    noise_node.inputs['Detail'].default_value = 0
    noise_node.inputs['Scale'].keyframe_insert("default_value", frame=210)
    noise_node.inputs['Detail'].keyframe_insert("default_value", frame=210)

    greater_than = math_node(nodes, 'GREATER_THAN')
    # control chipped area, smaller value, more chipped area
    greater_than.inputs[1].default_value = 0.61

    maximum = math_node(nodes, 'MAXIMUM')
    # control how much flat area, large value, more flat area
    maximum.inputs[1].default_value = 0.6

    links.new(greater_than.inputs[0], noise_node.outputs['Fac'])
    links.new(maximum.inputs[0], noise_node.outputs['Fac'])

    minimum = math_node(nodes, 'MINIMUM')
    # control chipped area smoothness, larger value, chipped area will rough
    minimum.inputs[1].default_value = 0.61
    links.new(minimum.inputs[0], maximum.outputs[0])

    mix_node = nodes.new(type='ShaderNodeMixShader')
    links.new(mix_node.inputs[0], greater_than.outputs[0])
    links.new(mix_node.inputs[1], principled_node.outputs[0]) 
    links.new(mix_node.inputs[2], principled_node1.outputs[0])

    displacement_node = nodes.new(type='ShaderNodeDisplacement')
    # control depth, 0 would be flat
    displacement_node.inputs['Scale'].default_value = -5
    links.new(minimum.outputs[0], displacement_node.inputs['Height'])

    links.new(mix_node.outputs[0], output_node.inputs[0])
    links.new(displacement_node.outputs[0], output_node.inputs['Displacement'])
    return material

bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1.2, 1.2, 1.2))

material = chipped_material()
bpy.context.object.data.materials.append(material)
render('BLENDER_EEVEE', 210)
background_settings(color='TexSky')
