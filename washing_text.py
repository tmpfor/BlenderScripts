import bpy, bmesh
from addon_utils import enable
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

def glass_material(color=(1, 1, 1, 1), roughness=0.5):
    material = bpy.data.materials.new(name="Glass")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # glossy shader
    glass_node = nodes.new(type='ShaderNodeBsdfGlass')
    glass_node.inputs['Color'].default_value = color
    glass_node.inputs['Roughness'].default_value = roughness
    links.new(glass_node.outputs[0], output_node.inputs[0])
    return material

def glossy_material(color=(0.8, 0.8, 0.8, 1), roughness=0.5):
    material = bpy.data.materials.new(name="Glossy")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # glossy shader
    glossy_node = nodes.new(type='ShaderNodeBsdfGlossy')
    glossy_node.inputs['Color'].default_value = color
    glossy_node.inputs['Roughness'].default_value = roughness
    links.new(glossy_node.outputs[0], output_node.inputs[0])
    return material

def diffuse_material(color, roughness):
    material = bpy.data.materials.new(name="Diffuse")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # diffuse shader
    diffuse_node = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse_node.inputs['Color'].default_value = color
    diffuse_node.inputs['Roughness'].default_value = roughness
    links.new(diffuse_node.outputs[0], output_node.inputs[0])
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
    else:
        principled_node.inputs['Base Color'].default_value = color
    principled_node.inputs['Roughness'].default_value = roughness
    principled_node.inputs['Metallic'].default_value = metallic
    principled_node.inputs['Transmission Weight'].default_value = transmission
    links.new(principled_node.outputs[0], output_node.inputs[0])
    return material

def background_settings():
    #bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.5, 1)
    nodes = bpy.data.worlds["World"].node_tree.nodes
    links = bpy.data.worlds["World"].node_tree.links

    background = nodes["Background"]
    sky_node = nodes.new(type='ShaderNodeTexSky')
    sky_node.sky_type = 'HOSEK_WILKIE'
    links.new(sky_node.outputs[0], background.inputs['Color'])

def diffuse_glossy_material(diffuse_color, diffuse_roughness, glossy_color, glossy_roughness, blend):
    material = bpy.data.materials.new(name="diffuse_glossy")
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

    links.new(mix_node.outputs[0], output_node.inputs[0])
    return material

def math_node(nodes, operation):
    math_node = nodes.new(type='ShaderNodeMath')
    math_node.operation = operation
    return math_node

def washing_material(material):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    mix_node = nodes.new(type='ShaderNodeMixShader')
    transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
    attribute_node = nodes.new(type='ShaderNodeAttribute')
    attribute_node.attribute_name = 'dp_paintmap'
    greater_than = math_node(nodes, 'GREATER_THAN')
    greater_than.inputs[1].default_value = 0.1
    links.new(greater_than.inputs[0], attribute_node.outputs['Fac'])

    links.new(mix_node.inputs[0], greater_than.outputs[0])
    links.new(mix_node.inputs[1], nodes['Group.001'].outputs['Shader']) 
    links.new(mix_node.inputs[2], transparent_node.outputs[0])

    links.new(mix_node.outputs[0], nodes['Material Output'].inputs[0])
    return material

def create_plane(location=(0, 0, -0.03), size=100):
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=location, size=size)
    bpy.context.object.name = 'Floor'
    # add material
    material = principled_material(hex_to_rgb(0xb4b4b4), 0.2)
    bpy.context.object.data.materials.append(material)

def create_light(energy, shadow_soft_size=0.1):
    light = bpy.data.objects['Light']
    light.data.energy = energy
    light.data.shadow_soft_size = shadow_soft_size

def add_text(body, extrude, bevel_depth, bevel_resolution):
    bpy.ops.object.text_add()
    text = bpy.context.active_object
    text.data.body = body
    text.rotation_euler = mathutils.Euler((math.radians(90.0), 0.0, 0.0), 'XYZ')
    text.data.extrude = extrude
    text.data.bevel_depth = bevel_depth
    text.data.bevel_resolution = bevel_resolution

    return text

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

def join_collection(name, object):
        bpy.ops.object.select_all(action='DESELECT')

        Coll = bpy.data.collections[name]
        for obj in Coll.objects:
            if obj.type == 'MESH':
               obj.select_set(True)
        bpy.context.view_layer.objects.active = object
        bpy.ops.object.join()

def select_object(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

create_plane()
create_plane(location=(1.5, -1.5, -0.09), size=4)
bpy.ops.object.modifier_add(type='FLUID')
bpy.context.object.modifiers["Fluid"].fluid_type = 'EFFECTOR'
bpy.context.object.modifiers["Fluid"].effector_settings.use_plane_init = True

# clean text
add_text('Blender', 0.1, 0.02, 2)
bpy.context.object.data.offset = -0.01
bpy.ops.transform.resize(value=(1, 0.7, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

bpy.ops.object.modifier_add(type='EDGE_SPLIT')
material = principled_material(hex_to_rgb(0xe47f00), 0, 0)
bpy.context.object.data.materials.append(material)
bpy.ops.object.convert(target='MESH')
bpy.ops.object.modifier_add(type='FLUID')
bpy.context.object.modifiers["Fluid"].fluid_type = 'EFFECTOR'
#bpy.context.object.modifiers["Fluid"].effector_settings.use_plane_init = True


create_light(3000, 3)
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)

# dirty text
add_text('Blender', 0.1, 0.02, 2)
obj = bpy.context.object
bpy.ops.object.modifier_add(type='EDGE_SPLIT')
bpy.ops.object.modifier_add(type='REMESH')
bpy.context.object.modifiers["Remesh"].mode = 'SHARP'
bpy.context.object.modifiers["Remesh"].use_remove_disconnected = False
bpy.context.object.modifiers["Remesh"].use_smooth_shade = True
bpy.context.object.modifiers["Remesh"].octree_depth = 7
bpy.ops.object.convert(target='MESH')

#material = principled_material(hex_to_rgb(0xe47f00), 0, 0)
#bpy.context.object.data.materials.append(material)
filepath = "./material/materials1.blend"
with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
    data_to.materials = data_from.materials
crackit_tree_red = bpy.data.materials['crackit_tree_red']
material = washing_material(crackit_tree_red)
bpy.context.object.data.materials.append(material)
bpy.context.object.active_material.blend_method = 'HASHED'

# crack it
# make sure cell fracture is enabled
enable("object_fracture_cell")
bpy.ops.object.add_fracture_cell_objects(source_limit=100, collection_name="dirty")
# delete original text
select_object(obj)
bpy.ops.object.delete(use_global=False)
# join all cells
join_collection("dirty", bpy.data.objects["Text.001_cell"])

# set canvas
bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
bpy.ops.dpaint.type_toggle(type='CANVAS')
bpy.ops.dpaint.output_toggle(output='A')

# fluid domain
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(1.5, -1.5, 0.7), scale=(2, 2, 1))
bpy.ops.object.shade_smooth()
bpy.ops.object.modifier_add(type='FLUID')
bpy.context.object.modifiers["Fluid"].fluid_type = 'DOMAIN'
bpy.context.object.modifiers["Fluid"].domain_settings.domain_type = 'LIQUID'
bpy.context.object.modifiers["Fluid"].domain_settings.resolution_max = 64
bpy.context.object.modifiers["Fluid"].domain_settings.use_collision_border_front = False
bpy.context.object.modifiers["Fluid"].domain_settings.use_collision_border_back = False
bpy.context.object.modifiers["Fluid"].domain_settings.use_collision_border_right = False
bpy.context.object.modifiers["Fluid"].domain_settings.use_collision_border_left = False
bpy.context.object.modifiers["Fluid"].domain_settings.use_collision_border_top = False
bpy.context.object.modifiers["Fluid"].domain_settings.use_collision_border_bottom = False
bpy.context.object.modifiers["Fluid"].domain_settings.use_mesh = True
bpy.context.object.modifiers["Fluid"].domain_settings.cache_frame_end = 150

material = principled_material(roughness=0, transmission=1)
bpy.context.object.data.materials.append(material)

# set brush
bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
bpy.context.object.modifiers["Dynamic Paint"].ui_type = 'BRUSH'
bpy.ops.dpaint.type_toggle(type='BRUSH')
bpy.context.object.modifiers["Dynamic Paint"].brush_settings.paint_source = 'DISTANCE'
bpy.context.object.modifiers["Dynamic Paint"].brush_settings.paint_distance = 0.02

# water source
bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(-0.1, -3, 0.34), size=0.3, rotation=(math.radians(90), 0, 0))
obj = bpy.context.object
bpy.ops.object.modifier_add(type='FLUID')
obj.modifiers["Fluid"].fluid_type = 'FLOW'
settings = obj.modifiers["Fluid"].flow_settings
settings.flow_type = 'LIQUID'
obj.modifiers["Fluid"].flow_settings.flow_behavior = 'INFLOW'
obj.modifiers["Fluid"].flow_settings.use_plane_init = True
obj.modifiers["Fluid"].flow_settings.use_initial_velocity = True
settings.velocity_coord[1] = 15
settings.velocity_coord[2] = -2
settings.keyframe_insert(data_path='velocity_coord', frame=1)
settings.keyframe_insert(data_path='velocity_coord', frame=60)
settings.velocity_coord[1] = 15
settings.velocity_coord[2] = 2
settings.keyframe_insert(data_path='velocity_coord', frame=61)
settings.keyframe_insert(data_path='velocity_coord', frame=120)
settings.velocity_coord[1] = 0
settings.velocity_coord[2] = 0
settings.keyframe_insert(data_path='velocity_coord', frame=121)

bpy.context.scene.frame_current = 1
obj.keyframe_insert(data_path='location')

bpy.context.scene.frame_current = 60
obj.location = Vector((3.3, -3, 0.34))
obj.keyframe_insert(data_path='location')

bpy.context.scene.frame_current = 120
obj.location = Vector((-0.1, -3, 0.34))
obj.keyframe_insert(data_path='location')

render('CYCLES', 150, 10)
# set camera
camera = bpy.data.objects['Camera']
camera.location = Vector((1.5, -6, 3.5))
camera.rotation_euler = mathutils.Euler((math.radians(60), 0, 0), 'XYZ')
