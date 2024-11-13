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

def background_settings():
    #bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.5, 1)
    nodes = bpy.data.worlds["World"].node_tree.nodes
    links = bpy.data.worlds["World"].node_tree.links

    background = nodes["Background"]
    sky_node = nodes.new(type='ShaderNodeTexSky')
    sky_node.sky_type = 'HOSEK_WILKIE'
    links.new(sky_node.outputs[0], background.inputs['Color'])

def cracks_material(diffuse_color=hex_to_rgb(0x777777), diffuse_roughness=0, glossy_color=hex_to_rgb(0xffffff), glossy_roughness=0.01, blend=0.1, cracks_amount=1, cracks_detail=10, cracks_color=hex_to_rgb(0x999999), cracks_width=0.01, cracks_depth=50):
    material = bpy.data.materials.new(name="cracks")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    # mix shader
    diffuse_node = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse_node.inputs['Color'].default_value = diffuse_color
    diffuse_node.inputs['Roughness'].default_value = diffuse_roughness
    glossy_node = nodes.new(type='ShaderNodeBsdfGlossy')
    glossy_node.inputs['Color'].default_value = glossy_color
    glossy_node.inputs['Roughness'].default_value = glossy_roughness
    layer_weight = material.node_tree.nodes.new(type='ShaderNodeLayerWeight')
    layer_weight.inputs['Blend'].default_value = blend
    mix_node = nodes.new(type='ShaderNodeMixShader')
    links.new(mix_node.inputs[0], layer_weight.outputs['Facing'])
    links.new(mix_node.inputs[1], diffuse_node.outputs[0]) 
    links.new(mix_node.inputs[2], glossy_node.outputs[0])

    # create cracks
    noise_node = material.node_tree.nodes.new(type='ShaderNodeTexNoise')
    #noise_node.noise_dimensions = '2D'
    # small value, less and large cracks
    noise_node.inputs['Scale'].default_value = cracks_amount
    """
    # animation
    noise_node.inputs['Scale'].default_value = 0
    noise_node.inputs['Scale'].keyframe_insert("default_value", frame=10)
    noise_node.inputs['Scale'].default_value = 5
    noise_node.inputs['Scale'].keyframe_insert("default_value", frame=240)
    """
    # large value, cracks edge jagged, rough, detail
    noise_node.inputs['Detail'].default_value = cracks_detail

    subtract0 = math_node(nodes, 'SUBTRACT')
    subtract0.inputs[1].default_value = 0.5

    subtract1 = math_node(nodes, 'SUBTRACT')
    subtract1.inputs[0].default_value = 0.5

    links.new(subtract0.inputs[0], noise_node.outputs['Color'])
    links.new(subtract1.inputs[1], noise_node.outputs['Color'])

    maximum = math_node(nodes, 'MAXIMUM')
    links.new(maximum.inputs[0], subtract0.outputs[0])
    links.new(maximum.inputs[1], subtract1.outputs[0])

    minimum = math_node(nodes, 'MINIMUM')
    # control cracks width
    minimum.inputs[1].default_value = cracks_width
    links.new(minimum.inputs[0], maximum.outputs[0])

    multiply = math_node(nodes, 'MULTIPLY')
    # control cracks depth, 0 cracks will flat
    multiply.inputs[1].default_value = cracks_depth
    links.new(multiply.inputs[0], minimum.outputs[0])

    # control cracks material
    mix_node1 = nodes.new(type='ShaderNodeMixShader')
    diffuse_node1 = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse_node1.inputs['Color'].default_value = cracks_color
    diffuse_node1.inputs['Roughness'].default_value = 0

    less_than = math_node(nodes, 'LESS_THAN')
    less_than.inputs[1].default_value = cracks_width
    links.new(less_than.inputs[0], maximum.outputs[0])

    links.new(mix_node1.inputs[0], less_than.outputs[0])
    links.new(mix_node1.inputs[1], mix_node.outputs[0]) 
    links.new(mix_node1.inputs[2], diffuse_node1.outputs[0])

    #links.new(mix_node.outputs[0], output_node.inputs[0])
    links.new(mix_node1.outputs[0], output_node.inputs[0])
    links.new(multiply.outputs[0], output_node.inputs['Displacement'])
    return material

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(2, 2, 2))
bpy.ops.object.shade_smooth()
material = cracks_material(diffuse_color=hex_to_rgb(0x000000), diffuse_roughness=0, glossy_color=hex_to_rgb(0x0000ff), glossy_roughness=0.01, blend=0.1, cracks_amount=5, cracks_detail=2, cracks_color=hex_to_rgb(0x0000ff), cracks_width=0.01, cracks_depth=50)
bpy.context.object.data.materials.append(material)

render('BLENDER_EEVEE', 240)
background_settings()
