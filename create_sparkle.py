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

def emission_material(color, strength):
    material = bpy.data.materials.new(name="Emission")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # emission shader
    emission_node = nodes.new(type='ShaderNodeEmission')
    emission_node.inputs['Color'].default_value = color
    emission_node.inputs['Strength'].default_value = strength
    links.new(emission_node.outputs[0], output_node.inputs[0])
    return material

def glossy_material(roughness):
    material = bpy.data.materials.new(name="Glossy")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # glossy shader
    glossy_node = nodes.new(type='ShaderNodeBsdfGlossy')
    glossy_node.inputs['Roughness'].default_value = roughness
    links.new(glossy_node.outputs[0], output_node.inputs[0])
    return material

def add_text(body, extrude, bevel_depth, bevel_resolution):
    bpy.ops.object.text_add()
    text = bpy.context.active_object
    text.data.body = body
    text.rotation_euler = mathutils.Euler((math.radians(90.0), 0.0, 0.0), 'XYZ')
    text.data.extrude = extrude
    text.data.bevel_depth = bevel_depth
    text.data.bevel_resolution = bevel_resolution

    return text

# particle object
bpy.ops.mesh.primitive_ico_sphere_add(location=(100, 0, 0))
ico_sphere = bpy.context.active_object

material = emission_material(hex_to_rgb(0xe7c383), 2.0)
ico_sphere.data.materials.append(material)

# add animation to emitter
bpy.ops.mesh.primitive_uv_sphere_add()
uv_sphere = bpy.context.active_object
bpy.ops.object.shade_smooth()

bpy.context.scene.frame_end = 120
bpy.context.scene.render.fps = 30
bpy.context.scene.frame_current = 1
uv_sphere.location = Vector((4, 1.2, 4))
uv_sphere.keyframe_insert(data_path='location')

bpy.context.scene.frame_current = 60
uv_sphere.location = Vector((-1, 1.2, 2))
uv_sphere.keyframe_insert(data_path='location')

bpy.context.scene.frame_current = 100
uv_sphere.location = Vector((2, 1.2, 1))
uv_sphere.keyframe_insert(data_path='location')
bpy.context.scene.frame_current = 1

# add material to emitter
material = bpy.data.materials.new(name="Red")
material.use_nodes = True
node_tree = material.node_tree
nodes = material.node_tree.nodes
links = material.node_tree.links

nodes.clear()
output_node = nodes.new(type='ShaderNodeOutputMaterial')
# mix shader
diffuse_node = material.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')
diffuse_node.inputs['Color'].default_value = hex_to_rgb(0xe72100)
emission_node = material.node_tree.nodes.new(type='ShaderNodeEmission')
emission_node.inputs['Color'].default_value = hex_to_rgb(0xe72100)
layer_weight = material.node_tree.nodes.new(type='ShaderNodeLayerWeight')
layer_weight.inputs['Blend'].default_value = 0.03
mix_node = nodes.new(type='ShaderNodeMixShader')
links.new(mix_node.inputs[0], layer_weight.outputs['Facing'])
links.new(mix_node.inputs[1], diffuse_node.outputs[0]) 
links.new(mix_node.inputs[2], emission_node.outputs[0])

links.new(mix_node.outputs[0], output_node.inputs[0])
uv_sphere.data.materials.append(material)

# add particle system
uv_sphere.modifiers.new("sparkle", type='PARTICLE_SYSTEM')
sparkle = uv_sphere.particle_systems[0]

settings = sparkle.settings
settings.count = 1500
settings.frame_end = 100
# particles not disappare
settings.lifetime = 1000
settings.normal_factor = 0
settings.effector_weights.gravity = 0
settings.render_type = 'OBJECT'
settings.instance_object = bpy.data.objects['Icosphere']
settings.particle_size = 0.025
#uv_sphere.show_instancer_for_render = False
#uv_sphere.show_instancer_for_viewport = False
#settings.display_method = 'NONE'


tex = bpy.data.textures.new(name = 'tex', type = 'DISTORTED_NOISE')
tex.distortion = 5

mtex = settings.texture_slots.add()
mtex.blend_type = 'MULTIPLY'
mtex.texture = tex
mtex.texture_coords = 'STRAND'
mtex.use_map_time = False
mtex.use_map_size = True

# hide light
#bpy.data.objects["Light"].hide_render = True

# set world to black
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

# set camera
camera = bpy.data.objects['Camera']
camera.location = Vector((1, -20, 2))
camera.rotation_euler = mathutils.Euler((math.radians(90.0), 0.0, 0.0), 'XYZ')

# add compositing
bpy.context.scene.use_nodes = True
nodetree = bpy.context.scene.node_tree
links = nodetree.links
render_layers = nodetree.nodes['Render Layers']
composite = nodetree.nodes['Composite']
glare_node = nodetree.nodes.new('CompositorNodeGlare')
glare_node.streaks = 6
glare_node.threshold = 0.8
glare_node.angle_offset = math.radians(20)
links.new(glare_node.inputs['Image'], render_layers.outputs['Image'])
links.new(composite.inputs['Image'], glare_node.outputs['Image'])

# add text
text = add_text('Blender', 0.1, 0.02, 0)
material = glossy_material(0.1)
text.data.materials.append(material)

# add inter text
text = add_text('Blender', 0.1, 0.019, 2)
material = emission_material(hex_to_rgb(0xe7c383), 1.0)
text.data.materials.append(material)

# add plane
bpy.ops.mesh.primitive_plane_add(size=100)
plane = bpy.context.active_object
plane.location = Vector((0, 0, -0.25))
