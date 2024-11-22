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

def emission_diffuse_material(emission_color, emission_strength, diffuse_color, diffuse_roughness, blend):
    material = bpy.data.materials.new(name="emission_diffuse")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    # mix shader
    diffuse_node = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse_node.inputs['Color'].default_value = diffuse_color
    diffuse_node.inputs['Roughness'].default_value = diffuse_roughness
    emission_node = nodes.new(type='ShaderNodeEmission')
    emission_node.inputs['Color'].default_value = emission_color
    emission_node.inputs['Strength'].default_value = emission_strength
    layer_weight = material.node_tree.nodes.new(type='ShaderNodeLayerWeight')
    layer_weight.inputs['Blend'].default_value = blend
    mix_node = nodes.new(type='ShaderNodeMixShader')
    links.new(mix_node.inputs[0], layer_weight.outputs['Facing'])
    links.new(mix_node.inputs[1], emission_node.outputs[0]) 
    links.new(mix_node.inputs[2], diffuse_node.outputs[0])

    links.new(mix_node.outputs[0], output_node.inputs[0])
    return material

bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['Plane'].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['Plane']
bpy.ops.transform.resize(value=(10, 10, 10), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
bpy.ops.object.modifier_apply(modifier="Decimate")
# following the contours of the terrain
bpy.ops.object.modifier_add(type='COLLISION')

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, -3), scale=(1, 1, 1))
bpy.ops.object.shade_smooth()
# add material
material = emission_diffuse_material(hex_to_rgb(0xff9959), 20, (0,0,0,1), 0, 0.7)
bpy.context.object.data.materials.append(material)

bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, -5, 0), scale=(1, 1, 1))
bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(8, 6.5, 0), size=2)
obj = bpy.context.object
# add particle system
obj.modifiers.new("following_orbs", type='PARTICLE_SYSTEM')
settings = obj.particle_systems[0].settings
settings.count = 10
settings.frame_end = 1
# particles not disappare
settings.lifetime = 1000
obj.show_instancer_for_render = False
obj.show_instancer_for_viewport = False

bpy.data.particles["ParticleSettings"].physics_type = 'BOIDS'
bpy.data.particles["ParticleSettings"].boids.use_flight = False
bpy.data.particles["ParticleSettings"].boids.use_land = True
bpy.data.particles["ParticleSettings"].boids.land_personal_space = 1.5

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
    #bpy.ops.boid.rule_add(type='GOAL')
    bpy.ops.boid.rule_add(type='FOLLOW_LEADER')

settings.boids.states['State'].rules['Follow Leader'].object = bpy.data.objects['Empty']

settings.render_type = 'OBJECT'
settings.instance_object = bpy.data.objects["Sphere"]
settings.particle_size = 0.3

render('CYCLES', 300, 10)
# set camera
camera = bpy.data.objects['Camera']
camera.location = Vector((23, -1, 5.4))
camera.rotation_euler = mathutils.Euler((math.radians(78), 0, math.radians(86)), 'XYZ')
