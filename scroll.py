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

def scroll_material(color=(0.8, 0.8, 0.8, 1), roughness=0.5, metallic=0, transmission=0):
    material = bpy.data.materials.new(name="Scroll")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # principled shader
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    image_node = nodes.new(type='ShaderNodeTexImage')
    if (color == 'TexSky'):
        sky_node = nodes.new(type='ShaderNodeTexSky')
        sky_node.sky_type = 'HOSEK_WILKIE'
        links.new(sky_node.outputs[0], principled_node.inputs['Base Color'])
    elif (color == 'TexMagic'):
        magic_node = nodes.new(type='ShaderNodeTexMagic')
        magic_node.turbulence_depth = 6
        magic_node.inputs['Scale'] = 10
        magic_node.inputs['Distortion'] = 2
        links.new(magic_node.outputs[0], principled_node.inputs['Base Color'])
    elif (type(color) == type((0,0,0,0))):
        principled_node.inputs['Base Color'].default_value = color
    else:
        video = bpy.data.images.load(color)
        image_node.image = video
        image_node.image_user.frame_duration = 200
        image_node.image_user.frame_start = 20
        image_node.image_user.use_auto_refresh = True

    principled_node.inputs['Roughness'].default_value = roughness
    principled_node.inputs['Metallic'].default_value = metallic
    principled_node.inputs['Transmission Weight'].default_value = transmission

    # video only show on front
    geometry_node = nodes.new(type='ShaderNodeNewGeometry')
    mixrgb_node = nodes.new(type='ShaderNodeMixRGB')
    mixrgb_node.inputs['Color2'].default_value = hex_to_rgb(0xd0c0b0)
    
    links.new(geometry_node.outputs['Backfacing'], mixrgb_node.inputs['Fac'])
    links.new(image_node.outputs['Color'], mixrgb_node.inputs['Color1'])

    links.new(mixrgb_node.outputs[0], principled_node.inputs['Base Color'])
    
    links.new(principled_node.outputs[0], output_node.inputs[0])
    return material

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

def create_plane(location=(0, 0, 0), size=100):
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=location, size=size)
    bpy.context.object.name = 'Floor'
    # add material
    material = principled_material(hex_to_rgb(0xb4b4b4), 0.2)
    bpy.context.object.data.materials.append(material)

# add floor
create_plane(location=(0, 0, 0.2), size=8)
bpy.ops.object.modifier_add(type='COLLISION')
bpy.context.object.collision.thickness_outer = 0.001

#bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0.5), scale=(0.05, 0.05, 1.5), rotation=(math.radians(90), 0, 0))
#bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0, 0, 0.5), scale=(0.05, 0.05, 1.5), rotation=(math.radians(90), 0, 0))
#bpy.ops.object.shade_smooth()
#bpy.ops.transform.translate(value=(0.7, 0, -0.05), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0.3, -0.4, 0.45), scale=(0.05, 0.05, 1.5), rotation=(math.radians(90), 0, 0))
obj = bpy.context.object
bpy.ops.object.modifier_add(type='COLLISION')
bpy.context.object.collision.thickness_outer = 0.001
bpy.context.scene.frame_current = 20
obj.keyframe_insert(data_path='location')
obj.keyframe_insert(data_path='rotation_euler')

bpy.context.scene.frame_current = 100
obj.rotation_euler = mathutils.Euler((math.radians(90), math.radians(-360), 0.0), 'XYZ')
obj.location = Vector((-0.9, -0.4, 0.45))
obj.keyframe_insert(data_path='location')
obj.keyframe_insert(data_path='rotation_euler')

#bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(-0.4, -0, -0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, True, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":False, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0.7, -0.4, 0.45), scale=(0.05, 0.05, 1.5), rotation=(math.radians(90), 0, 0))
obj = bpy.context.object
bpy.ops.object.modifier_add(type='COLLISION')
bpy.context.object.collision.thickness_outer = 0.001
bpy.context.scene.frame_current = 20
obj.keyframe_insert(data_path='location')
obj.keyframe_insert(data_path='rotation_euler')

bpy.context.scene.frame_current = 100
obj.rotation_euler = mathutils.Euler((math.radians(90), math.radians(360), 0.0), 'XYZ')
obj.location = Vector((1.9, -0.4, 0.45))
obj.keyframe_insert(data_path='location')
obj.keyframe_insert(data_path='rotation_euler')

# add spiral
bpy.ops.curve.spirals(align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0), spiral_type='ARCH', turns=3, dif_radius=1)
bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
bpy.ops.transform.rotate(value=math.radians(-90), orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

bpy.ops.curve.duplicate_move(CURVE_OT_duplicate={}, TRANSFORM_OT_translate={"value":(8, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, True, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
obj = bpy.context.object
bpy.ops.curve.select_all(action='DESELECT')
obj.data.splines[0].points[-1].select=True
obj.data.splines[1].points[-1].select=True
bpy.ops.curve.make_segment()
bpy.ops.curve.select_all(action='SELECT')
bpy.ops.transform.resize(value=(0.05, 0.05, 0.05), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
bpy.ops.transform.translate(value=(-3.75, 0, 0.44), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.object.hide_viewport = True
bpy.context.object.hide_render=True

# plane
bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
bpy.ops.object.editmode_toggle()
bpy.ops.transform.resize(value=(2, 1, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
bpy.ops.mesh.select_all(action = 'DESELECT')
# we need to switch from Edit mode to Object mode so the selection gets updated
bpy.ops.object.mode_set(mode='OBJECT')
obj = bpy.context.object
mesh = obj.data
mesh.edges[1].select = True
mesh.edges[3].select = True
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=40)

bpy.ops.mesh.select_all(action = 'DESELECT')
bm = bmesh.from_edit_mesh(mesh)
for edge in bm.edges:
    if edge.calc_length() > 1.9:
        edge.select = True
bmesh.update_edit_mesh(mesh)
bpy.ops.mesh.subdivide(number_cuts=20)
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.modifier_add(type='CURVE')
bpy.context.object.modifiers["Curve"].object = bpy.data.objects["Spiral"]
bpy.ops.transform.translate(value=(2.55, 0, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

bpy.ops.object.modifier_add(type='CLOTH')
bpy.context.object.modifiers["Cloth"].settings.quality = 10
bpy.context.object.modifiers["Cloth"].collision_settings.use_self_collision = True
bpy.ops.object.modifier_add(type='SUBSURF')
bpy.context.object.modifiers["Subdivision"].levels = 2
bpy.ops.object.shade_smooth()

# add material
material = scroll_material(color="./video.mp4")
bpy.context.object.data.materials.append(material)

render('BLENDER_EEVEE', 150)
create_light(3000, 3)

# set camera
camera = bpy.data.objects['Camera']
camera.location = Vector((0.48, -4.8, 4))
camera.rotation_euler = mathutils.Euler((math.radians(50), 0.0, 0.0), 'XYZ')
