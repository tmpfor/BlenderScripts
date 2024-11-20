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

def background_settings():
    nodes = bpy.data.worlds["World"].node_tree.nodes
    links = bpy.data.worlds["World"].node_tree.links

    background = nodes["Background"]
    background.inputs['Strength'].default_value = 2.5
    env_node = nodes.new(type='ShaderNodeTexEnvironment')
    forest = bpy.data.images.load(bpy.utils.resource_path('LOCAL') + "/datafiles/studiolights/world/forest.exr")
    env_node.image = forest
    links.new(env_node.outputs[0], background.inputs['Color'])

def principled_material(color=(0.8, 0.8, 0.8, 1), roughness=0.5):
    material = bpy.data.materials.new(name="Principled")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # principled shader
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    if (color == 'TexSky'):
        sky_node = nodes.new(type='ShaderNodeTexSky')
        sky_node.sky_type = 'HOSEK_WILKIE'
        links.new(sky_node.outputs[0], principled_node.inputs['Base Color'])
    if (color == 'TexMagic'):
        magic_node = nodes.new(type='ShaderNodeTexMagic')
        magic_node.turbulence_depth = 6
        magic_node.inputs['Scale'] = 10
        magic_node.inputs['Distortion'] = 2
        links.new(magic_node.outputs[0], principled_node.inputs['Base Color'])
    else:
        principled_node.inputs['Base Color'].default_value = color
    principled_node.inputs['Roughness'].default_value = roughness
    principled_node.inputs['Metallic'].default_value = 1
    links.new(principled_node.outputs[0], output_node.inputs[0])
    return material

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

def bubbles_material(color=(0.8, 0.8, 0.8, 1), roughness=0):
    material = bpy.data.materials.new(name="Principled")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # principled shader
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    if (color == 'TexSky'):
        sky_node = nodes.new(type='ShaderNodeTexSky')
        sky_node.sky_type = 'HOSEK_WILKIE'
        links.new(sky_node.outputs[0], principled_node.inputs['Base Color'])
    if (color == 'TexMagic'):
        magic_node = nodes.new(type='ShaderNodeTexMagic')
        magic_node.turbulence_depth = 6
        magic_node.inputs['Scale'].default_value = 10
        magic_node.inputs['Distortion'].default_value = 2
        links.new(magic_node.outputs[0], principled_node.inputs['Base Color'])
    else:
        principled_node.inputs['Base Color'].default_value = color
    principled_node.inputs['Roughness'].default_value = roughness
    principled_node.inputs['Metallic'].default_value = 1

    mix_node = nodes.new(type='ShaderNodeMixShader')
    transparent_node = material.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
    fresnel_node = material.node_tree.nodes.new(type='ShaderNodeFresnel')
    fresnel_node.inputs['IOR'].default_value = 1.15
    minimum = math_node(nodes, 'MINIMUM')
    minimum.inputs[1].default_value = 0.5
    links.new(minimum.inputs[0], fresnel_node.outputs[0])
    links.new(mix_node.inputs[0], minimum.outputs[0])
    links.new(mix_node.inputs[1], transparent_node.outputs[0]) 
    links.new(mix_node.inputs[2], principled_node.outputs[0])

    links.new(mix_node.outputs[0], output_node.inputs[0])
    return material

bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

bpy.ops.object.metaball_add(type='BALL', radius=2, enter_editmode=False, align='WORLD', location=(0, 0, -10), scale=(1, 1, 1))
bpy.context.object.data.resolution = 0.02
bpy.context.object.data.render_resolution = 0.01
material = bubbles_material(color='TexMagic')
bpy.context.object.data.materials.append(material)
bpy.context.object.active_material.blend_method = 'HASHED'

bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(0.2, 0.2, 0.2))
obj = bpy.context.object
# add particle system
obj.modifiers.new("bubbles", type='PARTICLE_SYSTEM')
#bubbles = obj.particle_systems[0]

#settings = bubbles.settings
settings = obj.particle_systems[0].settings
settings.count = 10
settings.frame_end = 1
# particles not disappare
settings.lifetime = 1000
# particles inside object
bpy.data.particles["ParticleSettings"].emit_from = 'VOLUME'
obj.show_instancer_for_render = False
obj.show_instancer_for_viewport = False

bpy.data.particles["ParticleSettings"].physics_type = 'BOIDS'
# prevent bubbles move too fast
bpy.data.particles["ParticleSettings"].boids.air_speed_max = 1

# Copy the current context
context_override = bpy.context.copy()
# Override the wanted property
context_override["particle_settings"] = settings
with bpy.context.temp_override(**context_override):
    # Call the operators
    bpy.ops.boid.rule_del()
    bpy.ops.boid.rule_del()
    #continue with boid brain settings in correct order with override  
    bpy.ops.boid.rule_add(type='SEPARATE')
    bpy.ops.boid.rule_add(type='GOAL')
settings.boids.states['State'].rules['Goal'].object = bpy.data.objects['Empty']

settings.render_type = 'OBJECT'
settings.instance_object = bpy.data.objects["Mball"]
settings.particle_size = 0.1
settings.size_random = 0.5

camera = bpy.data.objects['Camera']
camera.data.lens = 300
background_settings()
render('BLENDER_EEVEE', 210)
