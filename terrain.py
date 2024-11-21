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

def render(engine, frame_end, samples=32, fps=30):
    scene = bpy.context.scene
    scene.frame_end = frame_end
    scene.render.fps = fps
    scene.frame_current = 1
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.engine = engine
    if (engine == 'CYCLES'):
        scene.cycles.preview_samples = samples
        scene.cycles.samples = samples

def create_light(energy, shadow_soft_size=0.1):
    light = bpy.data.objects['Light']
    light.data.energy = energy
    light.data.shadow_soft_size = shadow_soft_size

def background_settings(color=(0, 0, 0, 1), image_path=bpy.utils.resource_path('LOCAL') + "/datafiles/studiolights/world/forest.exr", strength=1):
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

def terrain_material(color=(0.8, 0.8, 0.8, 1), roughness=0):
    material = bpy.data.materials.new(name="terrain")
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
        principled_node.inputs['Base Color'].default_value = hex_to_rgb(0x3a2b24)
    principled_node.inputs['Roughness'].default_value = 1
    #principled_node.inputs['Metallic'].default_value = 0

    principled_node1 = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node1.inputs['Base Color'].default_value = hex_to_rgb(0xffbe9f)
    principled_node1.inputs['Roughness'].default_value = 1
    #principled_node1.inputs['Metallic'].default_value = 0

    texcoord_node = nodes.new(type='ShaderNodeTexCoord')
    noise_node = nodes.new(type='ShaderNodeTexNoise')
    noise_node.inputs['Scale'].default_value = 5
    noise_node.inputs['Detail'].default_value = 16
    links.new(noise_node.inputs['Vector'], texcoord_node.outputs['Object'])

    wave_node = nodes.new(type='ShaderNodeTexWave')
    links.new(wave_node.inputs['Scale'], noise_node.outputs['Color'])

    multiply = math_node(nodes, 'MULTIPLY')
    multiply.inputs[1].default_value = 10
    links.new(multiply.inputs[0], wave_node.outputs['Color'])

    displacement_node = nodes.new(type='ShaderNodeDisplacement')
    displacement_node.inputs['Scale'].default_value = 0.1
    displacement_node.inputs['Midlevel'].default_value = 0
    links.new(multiply.outputs[0], displacement_node.inputs['Height'])

    mix_node = nodes.new(type='ShaderNodeMixShader')

    geometry_node = nodes.new(type='ShaderNodeNewGeometry')
    multiply = math_node(nodes, 'MULTIPLY')
    multiply.inputs[1].default_value = 10
    links.new(multiply.inputs[0], geometry_node.outputs['Pointiness'])

    add = math_node(nodes, 'ADD')
    add.inputs[1].default_value = -4.8
    links.new(add.inputs[0], multiply.outputs[0])

    links.new(mix_node.inputs[0], add.outputs[0])
    links.new(mix_node.inputs[1], principled_node.outputs[0]) 
    links.new(mix_node.inputs[2], principled_node1.outputs[0])

    links.new(mix_node.outputs[0], output_node.inputs[0])
    links.new(displacement_node.outputs[0], output_node.inputs['Displacement'])
    return material

bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), size=2)
obj = bpy.context.object

bpy.ops.object.modifier_add(type='SUBSURF')
subsurf_settings = bpy.context.object.modifiers["Subdivision"]
subsurf_settings.levels = 9
subsurf_settings.render_levels = 9
subsurf_settings.subdivision_type = 'SIMPLE'

bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
bpy.ops.dpaint.type_toggle(type='CANVAS')
canvas_settings = bpy.context.object.modifiers["Dynamic Paint"].canvas_settings
canvas_settings.canvas_surfaces["Surface"].surface_type = 'WAVE'
bpy.ops.object.shade_smooth()
material = terrain_material()
bpy.context.object.data.materials.append(material)

# source
bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, 0, 1), size=2)
obj = bpy.context.object
#obj.modifiers.new("source", type='PARTICLE_SYSTEM')
bpy.ops.object.particle_system_add()
# do not show particles
bpy.context.object.show_instancer_for_render = False
bpy.context.object.show_instancer_for_viewport = False
bpy.data.particles["ParticleSettings"].render_type = 'NONE'
bpy.data.particles["ParticleSettings"].display_method = 'NONE'

#bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
obj.modifiers.new("brush", type='DYNAMIC_PAINT')
obj.modifiers['brush'].ui_type = 'BRUSH'
bpy.ops.dpaint.type_toggle(type='BRUSH')

brush_settings = bpy.context.object.modifiers["brush"].brush_settings
brush_settings.paint_source = 'PARTICLE_SYSTEM'
brush_settings.particle_system = obj.particle_systems["ParticleSystem"]
brush_settings.solid_radius = 0.05

render('CYCLES', 120, 10, 3)
create_light(2000)
background_settings(color='TexEnvironment', image_path=bpy.utils.resource_path('LOCAL') + "/datafiles/studiolights/world/night.exr", strength=1)

# set camera
camera = bpy.data.objects['Camera']
camera.location = Vector((1.2, 0.1, 0.1))
camera.rotation_euler = mathutils.Euler((math.radians(81), 0, math.radians(92)), 'XYZ')
