import bpy, bmesh
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

def principled_material(color=(0.8, 0.8, 0.8, 1), roughness=0.5, metallic=0, transmission=0):
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
    if (color == 'TexChecker'):
        checker_node = nodes.new(type='ShaderNodeTexChecker')
        checker_node.inputs['Color1'].default_value = (1, 1, 1, 1)
        checker_node.inputs['Color2'].default_value = (0, 0, 0, 1)
        checker_node.inputs['Scale'].default_value = 100
        links.new(checker_node.outputs[0], principled_node.inputs['Base Color'])
    else:
        principled_node.inputs['Base Color'].default_value = color
    principled_node.inputs['Roughness'].default_value = roughness
    principled_node.inputs['Metallic'].default_value = metallic
    principled_node.inputs['Transmission Weight'].default_value = transmission
    links.new(principled_node.outputs[0], output_node.inputs[0])
    return material

def select_object(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

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

def create_plane(location=(0, 0, 0), size=100):
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=location, size=size)
    bpy.context.object.name = 'Floor'
    # add material
    material = principled_material(color='TexChecker', roughness=0.1)
    bpy.context.object.data.materials.append(material)

def create_stairs(location):
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=location, scale=(0.1, 0.1, 0.1))
    bpy.ops.object.modifier_add(type='ARRAY')
    bpy.context.object.modifiers["Array"].count = 8
    bpy.ops.object.modifier_add(type='ARRAY')
    bpy.context.object.modifiers["Array.001"].count = 8
    bpy.context.object.modifiers["Array.001"].relative_offset_displace[0] = 0
    bpy.context.object.modifiers["Array.001"].relative_offset_displace[1] = 1
    bpy.context.object.modifiers["Array.001"].relative_offset_displace[2] = 1

def create_building(location=(0, 0, 0), scale=(0.1, 0.1, 0.1), x=8, y=8, z=16, wireframe=True, smooth=True):
    # the building
    #bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(0.1, 0.1, 0.1))
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=location, scale=(1, 1, 1))
    bpy.ops.transform.resize(value=scale, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    obj = bpy.context.object

    bpy.ops.object.modifier_add(type='ARRAY')
    bpy.context.object.modifiers["Array"].count = x
    bpy.ops.object.modifier_add(type='ARRAY')
    bpy.context.object.modifiers["Array.001"].count = y
    bpy.context.object.modifiers["Array.001"].relative_offset_displace[0] = 0
    bpy.context.object.modifiers["Array.001"].relative_offset_displace[1] = 1
    bpy.ops.object.modifier_add(type='ARRAY')
    bpy.context.object.modifiers["Array.002"].count = z
    bpy.context.object.modifiers["Array.002"].relative_offset_displace[0] = 0
    bpy.context.object.modifiers["Array.002"].relative_offset_displace[2] = 1
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.object.modifiers["Solidify"].thickness = 1
    if (wireframe):
        bpy.ops.object.modifier_add(type='WIREFRAME')
        bpy.context.object.modifiers["Wireframe"].thickness = 0.2

    if (smooth):
        bpy.ops.object.shade_smooth()

create_plane(location=(0, 0, -0.2))
create_stairs(location=(0.7, -1.7, 0))
#material = principled_material(hex_to_rgb(0xe757cf))
material = principled_material(color=(1, 1, 1, 1), metallic=1)
bpy.context.object.data.materials.append(material)

create_building(scale=(0.2, 0.2, 0.2), z=4, smooth=False)
material = principled_material(hex_to_rgb(0x70ccf3), metallic=1)
bpy.context.object.data.materials.append(material)

create_building(location=(0, 0, 1.6), scale=(0.2, 0.2, 0.2), wireframe=False, smooth=False)
# add material
#material = principled_material(hex_to_rgb(0x70ccf3), metallic=1)
bpy.context.object.data.materials.append(material)
#material = principled_material(hex_to_rgb(0xff0000), metallic=0)
material = emission_material(hex_to_rgb(0xff0000), 20)
bpy.context.object.data.materials.append(material)
bpy.context.object.modifiers["Solidify"].material_offset = 1

bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
bpy.ops.dpaint.type_toggle(type='CANVAS')
bpy.context.object.modifiers["Dynamic Paint"].canvas_settings.canvas_surfaces["Surface"].surface_type = 'WEIGHT'

# make surface reappear
bpy.context.object.modifiers["Dynamic Paint"].canvas_settings.canvas_surfaces["Surface"].use_dissolve = True
bpy.context.object.modifiers["Dynamic Paint"].canvas_settings.canvas_surfaces["Surface"].dissolve_speed = 50
bpy.context.object.modifiers["Dynamic Paint"].canvas_settings.canvas_surfaces["Surface"].use_dissolve_log = False

bpy.ops.dpaint.output_toggle(output='A')
bpy.ops.object.modifier_add(type='MASK')
bpy.context.object.modifiers["Mask"].vertex_group = "dp_weight"
bpy.context.object.modifiers["Mask"].invert_vertex_group = True

# the particles emitter
#location=(0.7, 0.7, 1.5+1.6)
bpy.ops.mesh.primitive_uv_sphere_add(enter_editmode=False, align='WORLD', location=(1.4, 1.4, 4.5), scale=(1, 1, 1))
#bpy.ops.transform.resize(value=(0.5, 0.5, 0.5), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
bpy.ops.object.particle_system_add()
bpy.data.particles["ParticleSettings"].count = 100
bpy.data.particles["ParticleSettings"].effector_weights.gravity = 0
bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
bpy.context.object.modifiers["Dynamic Paint"].ui_type = 'BRUSH'
bpy.ops.dpaint.type_toggle(type='BRUSH')
bpy.context.object.modifiers["Dynamic Paint"].brush_settings.paint_source = 'PARTICLE_SYSTEM'
bpy.context.object.modifiers["Dynamic Paint"].brush_settings.particle_system = bpy.data.objects["Sphere"].particle_systems["ParticleSystem"]
#bpy.context.object.hide_viewport = True
#bpy.context.object.hide_render=True

background_settings(color=(0, 0, 0, 1))
create_light(5000)
background_settings(color='TexEnvironment', image_path=bpy.utils.resource_path('LOCAL') + "/datafiles/studiolights/world/forest.exr", strength=1)
# set camera
camera = bpy.data.objects['Camera']
#camera.location = Vector((11, -10, 9.4))
camera.location = Vector((19, -16, 16))
camera.rotation_euler = mathutils.Euler((math.radians(64), 0, math.radians(46)), 'XYZ')
render('BLENDER_EEVEE', 240)
