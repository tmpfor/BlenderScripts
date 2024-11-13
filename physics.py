import bpy, bmesh
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

def principled_material(color=(0.8, 0.8, 0.8, 1), roughness=0.5, metallic=0):
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
    links.new(principled_node.outputs[0], output_node.inputs[0])
    return material

def create_plane():
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, 0, -3.2), size=100)
    obj = bpy.context.object
    obj.name = 'Floor'

    mesh = obj.data
    # select top edge
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action = 'DESELECT')
    # we need to switch from Edit mode to Object mode so the selection gets updated
    bpy.ops.object.mode_set(mode='OBJECT')
    verts = [v for v in mesh.vertices if v.co[0] < 0]
    for v in verts:
        v.select = True
    """
    for v in mesh.vertices:
        if v.co[0] < 0:
            v.select = True
    """
    bpy.ops.object.mode_set(mode='EDIT')

    # extrude z 50
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 50), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    
    # select top edge
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action = 'DESELECT')
    # we need to switch from Edit mode to Object mode so the selection gets updated
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in mesh.vertices:
        if v.co[0] < 0 and v.co[2] < 1:
            v.select = True

    bpy.ops.object.mode_set(mode='EDIT')  
    bpy.ops.mesh.bevel(offset=10, offset_pct=0, segments=10, affect='EDGES')

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()

    # add material
    material = principled_material()
    bpy.context.object.data.materials.append(material)

def create_rigid_body_passive(collision_shape = 'CONVEX_HULL'):
    bpy.ops.rigidbody.object_add()
    obj = bpy.context.object
    obj.rigid_body.type = 'PASSIVE'
    obj.rigid_body.collision_shape = collision_shape
    obj.rigid_body.friction = 1
    obj.rigid_body.restitution = 1

def create_rigid_body_active():
    bpy.ops.rigidbody.object_add()
    obj = bpy.context.object
    obj.rigid_body.type = 'ACTIVE'
    obj.rigid_body.friction = 1
    obj.rigid_body.restitution = 0.2

def add_bevel():
    bpy.ops.object.modifier_add(type='BEVEL')
    settings = bpy.context.object.modifiers["Bevel"]
    settings.width = 0.01
    settings.segments = 2

def rigid_body_passive():
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(0.8, 0.1, 3))
    add_bevel()
    create_rigid_body_passive()
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 4.8, 0), scale=(0.8, 0.1, 3))
    add_bevel()
    create_rigid_body_passive()
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 2.5, -3.1), scale=(2, 3, 0.1))
    add_bevel()
    create_rigid_body_passive()
    
    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', location=(0.2, 2, 2), scale=(0.1, 0.1, 2), rotation=(math.radians(75), 0, 0))
    create_rigid_body_passive()
    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', location=(-0.2, 2, 2), scale=(0.1, 0.1, 2), rotation=(math.radians(75), 0, 0))
    create_rigid_body_passive()

    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', location=(0.2, 2.8, 0.5), scale=(0.1, 0.1, 2), rotation=(math.radians(100), 0, 0))
    create_rigid_body_passive()
    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', location=(-0.2, 2.8, 0.5), scale=(0.1, 0.1, 2), rotation=(math.radians(100), 0, 0))
    create_rigid_body_passive()

    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', location=(0.2, 2, -1), scale=(0.1, 0.1, 2), rotation=(math.radians(75), 0, 0))
    create_rigid_body_passive()
    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', location=(-0.2, 2, -1), scale=(0.1, 0.1, 2), rotation=(math.radians(75), 0, 0))
    create_rigid_body_passive()

    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', location=(0.2, 2.8, -2.5), scale=(0.1, 0.1, 2), rotation=(math.radians(100), 0, 0))
    create_rigid_body_passive()
    bpy.ops.mesh.primitive_cylinder_add(enter_editmode=False, align='WORLD', location=(-0.2, 2.8, -2.5), scale=(0.1, 0.1, 2), rotation=(math.radians(100), 0, 0))
    create_rigid_body_passive()

def rigid_body_active():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 1, 3), scale=(0.3, 0.3, 0.3))
    bpy.ops.object.shade_smooth()
    create_rigid_body_active()
    material = principled_material(hex_to_rgb(0xff0000), roughness = 0.3, metallic = 0.3)
    bpy.context.object.data.materials.append(material)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 2, 4), scale=(0.3, 0.3, 0.3))
    bpy.ops.object.shade_smooth()
    create_rigid_body_active()
    material = principled_material(hex_to_rgb(0x000000), roughness = 0.3, metallic = 0.3)
    bpy.context.object.data.materials.append(material)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 3.5, 3.5), scale=(0.3, 0.3, 0.3))
    bpy.ops.object.shade_smooth()
    create_rigid_body_active()
    material = principled_material(hex_to_rgb(0x0000ff), roughness = 0.3, metallic = 0.3)
    bpy.context.object.data.materials.append(material)

def join_passive():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['Cube'].select_set(True)
    bpy.data.objects['Cube.001'].select_set(True)
    bpy.data.objects['Cube.002'].select_set(True)
    bpy.data.objects['Cylinder'].select_set(True)
    bpy.data.objects['Cylinder.001'].select_set(True)
    bpy.data.objects['Cylinder.002'].select_set(True)
    bpy.data.objects['Cylinder.003'].select_set(True)
    bpy.data.objects['Cylinder.004'].select_set(True)
    bpy.data.objects['Cylinder.005'].select_set(True)
    bpy.data.objects['Cylinder.006'].select_set(True)
    bpy.data.objects['Cylinder.007'].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Cylinder']
    bpy.ops.object.join()
    bpy.context.object.rigid_body.type = 'ACTIVE'
    bpy.context.object.rigid_body.collision_shape = 'MESH'
    bpy.context.object.rigid_body.mass = 10
    bpy.context.scene.rigidbody_world.substeps_per_frame = 3

def large_ball():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, -12, 0), scale=(3, 3, 3))
    bpy.ops.object.shade_smooth()
    create_rigid_body_active()
    create_rigid_body_active()
    material = principled_material(hex_to_rgb(0xE87D45))
    bpy.context.object.data.materials.append(material)
    obj = bpy.context.object
    obj.rigid_body.friction = 1
    obj.rigid_body.restitution = 1
    obj.rigid_body.collision_shape = 'SPHERE'
    obj.rigid_body.mass = 10
    obj.rigid_body.kinematic = True

    bpy.context.scene.frame_current = 61
    bpy.ops.transform.translate(value=(-0, -5, -0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.anim.keyframe_insert_by_name(type="Location")

    bpy.context.scene.frame_current = 64
    bpy.ops.transform.translate(value=(-0, 5, -0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.anim.keyframe_insert_by_name(type="Location")
    obj.keyframe_insert('rigid_body.kinematic')

    bpy.context.scene.frame_current = 65
    bpy.context.object.rigid_body.kinematic = False
    obj.keyframe_insert('rigid_body.kinematic')

def rigid_world():
    scene = bpy.context.scene
    scene.rigidbody_world.enabled = True
    scene.rigidbody_world.time_scale = 2.5
    bpy.context.scene.rigidbody_world.substeps_per_frame = 3

def create_light(energy):
    light = bpy.data.objects['Light']
    light.data.energy = energy
    light.data.shadow_soft_size = 3

rigid_body_passive()
rigid_body_active()
rigid_world()
create_plane()
create_rigid_body_passive(collision_shape='MESH')

join_passive()
large_ball()

# set camera
camera = bpy.data.objects['Camera']
camera.location = Vector((25, 10, 5))
camera.rotation_euler = mathutils.Euler((math.radians(80), 0, math.radians(108)), 'XYZ')

render('BLENDER_EEVEE', 150)
create_light(3000)
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = hex_to_rgb(0x828282)
#material = bpy.data.materials.get('WoodP')
#bpy.context.object.data.materials.append(material)

#bpy.ops.material.new()
#wood = bpy.context.scene.matlib.materials['wood']
#bpy.context.scene.matlib.mat_index = 30
#bpy.ops.object.make_local(type='SELECT_OBDATA_MATERIAL')


