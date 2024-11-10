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

def principled_material():
    material = bpy.data.materials.new(name="Principled")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # principled shader
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    sky_node = nodes.new(type='ShaderNodeTexSky')
    sky_node.sky_type = 'HOSEK_WILKIE'
    links.new(sky_node.outputs[0], principled_node.inputs['Base Color'])
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

def create_pipe():
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0), major_radius=0.5, minor_radius=0.3, abso_major_rad=1.25, abso_minor_rad=0.75)

    # get created object
    obj = bpy.context.object
    obj.name = 'Pipe'
    # get the mesh data
    mesh = obj.data

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.rotate(value=math.radians(90.0), orient_axis='X')
    bpy.ops.transform.resize(value=(0.6, 0.6, 0.6))

    bm = bmesh.from_edit_mesh(mesh)
    # delete vertices
    verts = [v for v in bm.verts if v.co[0] > 0.001 or v.co[2] > 0.001]
    bmesh.ops.delete(bm, geom=verts, context="VERTS")
    verts = [v for v in bm.verts if v.co[2] > -0.001]

    # select top circle
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action = 'DESELECT')
    # we need to switch from Edit mode to Object mode so the selection gets updated
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in mesh.vertices:
        if v.co[2] > -0.001:
            v.select = True
    bpy.ops.object.mode_set(mode='EDIT')

    # extrude and scale it
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.resize(value=(1.1, 1.1, 1.1), constraint_axis=(False, False, False))

    # extrude z 0.2
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 0.2), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})

    # extrude and scale it
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.resize(value=(0.9, 0.9, 0.9), constraint_axis=(False, False, False))

    # extrude z -0.2
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, -0.2), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})

    # select right circle (TODO: make it method)
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action = 'DESELECT')
    # we need to switch from Edit mode to Object mode so the selection gets updated
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in mesh.vertices:
        if v.co[0] > -0.001:
            v.select = True
    bpy.ops.object.mode_set(mode='EDIT')

    # extrude and scale it
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.resize(value=(1.1, 1.1, 1.1), constraint_axis=(False, False, False))

    # extrude x 0.2
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0.2, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})

    # extrude and scale it
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.resize(value=(0.9, 0.9, 0.9), constraint_axis=(False, False, False))

    bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    # extrude x 0.05
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0.05, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    # extrude x 3
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(3.0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})

    bmesh.update_edit_mesh(mesh)

    # add subdivision
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.subdivision_set(level=2, relative=False)
    bpy.ops.object.shade_smooth()

    # add material
    material = glossy_material(hex_to_rgb(0xe7966b), 0.4)#0.15
    obj.data.materials.append(material)
    material = glossy_material(roughness=0.35)#0.05
    obj.data.materials.append(material)

    # assign material to face
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_all(action = 'DESELECT')
    # we need to switch from Edit mode to Object mode so the selection gets updated
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in mesh.polygons:
        if v.center[0] > 0.22 and v.center[0] < 0.3:
            v.select = True
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.context.object.active_material_index = 1
    bpy.ops.object.material_slot_assign()

    # add more geometry
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action = 'DESELECT')
    # we need to switch from Edit mode to Object mode so the selection gets updated
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in mesh.vertices:
        if v.co[0] > 0.22 and v.co[0] < 0.3:
            v.select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_nth()
    bpy.ops.transform.translate(value=(0.05, 0, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":519, "mesh_select_mode_init":(True, False, False)}, TRANSFORM_OT_edge_slide={"value":0.99, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})

    # add depth
    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":503, "mesh_select_mode_init":(True, False, False)}, TRANSFORM_OT_edge_slide={"value":-1, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})
    bpy.ops.transform.resize(value=(1.02, 1.02, 1.02), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":563, "mesh_select_mode_init":(True, False, False)}, TRANSFORM_OT_edge_slide={"value":-0.9, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})

    # add loopcut sharp edge
    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":343, "mesh_select_mode_init":(True, False, False)}, TRANSFORM_OT_edge_slide={"value":0.95, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})
    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":347, "mesh_select_mode_init":(True, False, False)}, TRANSFORM_OT_edge_slide={"value":-0.95, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})
    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":395, "mesh_select_mode_init":(True, False, False)}, TRANSFORM_OT_edge_slide={"value":0.95, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})

    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":434, "mesh_select_mode_init":(True, False, False)}, TRANSFORM_OT_edge_slide={"value":0.95, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})
    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":675, "mesh_select_mode_init":(True, False, False)}, TRANSFORM_OT_edge_slide={"value":-0.95, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "correct_uv":True, "release_confirm":False, "use_accurate":False})

def create_domain():
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(-0.3, 0, 0.7), scale=(1.5, 1.5, 1.5))
    bpy.context.object.name = 'Water'
    bpy.ops.object.modifier_add(type='FLUID')
    fluid = bpy.context.object.modifiers["Fluid"]
    fluid.fluid_type = 'DOMAIN'
    fluid.domain_settings.domain_type = 'LIQUID'
    fluid.domain_settings.use_mesh = True
    fluid.domain_settings.cache_frame_end = 120
    #fluid.domain_settings.cache_type = 'ALL'

    bpy.ops.object.shade_smooth()
    # add material
    material = glass_material(color=(1, 1, 1, 1), roughness=0)
    bpy.context.object.data.materials.append(material)
    
    # fix water too much
    bpy.ops.transform.translate(value=(0, 0, -0.45), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

def create_inflow():
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(-0.3, 0, -0.05), scale=(0.15, 0.15, 0.15))
    bpy.context.object.name = 'Inflow'
    bpy.ops.object.modifier_add(type='FLUID')
    fluid = bpy.context.object.modifiers["Fluid"]
    fluid.fluid_type = 'FLOW'
    fluid.flow_settings.flow_type = 'LIQUID'
    fluid.flow_settings.flow_behavior = 'INFLOW'
    fluid.flow_settings.use_initial_velocity = True
    fluid.flow_settings.velocity_coord[2] = 5.5

def add_text(body, extrude, bevel_depth, bevel_resolution):
    bpy.ops.object.text_add()
    text = bpy.context.active_object
    text.data.body = body
    text.rotation_euler = mathutils.Euler((math.radians(90.0), 0.0, 0.0), 'XYZ')
    text.data.extrude = extrude
    text.data.bevel_depth = bevel_depth
    text.data.bevel_resolution = bevel_resolution

    return text

def add_fcurve_noise(fcurve, scale, strength, offset):
    fcurve.modifiers.new('NOISE')
    fcurve.modifiers['Noise'].scale = scale
    fcurve.modifiers['Noise'].strength = strength
    fcurve.modifiers['Noise'].offset = offset
    fcurve.modifiers['Noise'].use_restricted_range = True
    fcurve.modifiers['Noise'].frame_start = 10
    fcurve.modifiers['Noise'].frame_end = 120

def create_effector():
    text = add_text("Blender", 0.1, 0.02, 3)
    # make text as fluid collision
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.modifier_add(type='FLUID')
    fluid = bpy.context.object.modifiers["Fluid"]
    fluid.fluid_type = 'EFFECTOR'
    # position text
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.translate(value=(-1.5, 0, 0.02), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.transform.translate(value=(-0.3, 0, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

    # add animation
    #bpy.context.scene.frame_current = 10
    bpy.ops.anim.keyframe_insert_by_name(type="BUILTIN_KSI_LocRot")
    fcurves = text.animation_data.action.fcurves
    # location z
    add_fcurve_noise(fcurves[2], 10, 0.5, 0)
    # location y
    add_fcurve_noise(fcurves[1], 10, 0.1, 5)
    # location x
    add_fcurve_noise(fcurves[0], 10, 0.1, 10)
    # rotation x
    add_fcurve_noise(fcurves[3], 10, 0.5, 15)
    # rotation y
    add_fcurve_noise(fcurves[4], 10, 0.5, 20)
    # rotation z
    add_fcurve_noise(fcurves[5], 10, 0.5, 25)

    # add material
    material = diffuse_glossy_material(hex_to_rgb(0x9c0000), 0, (0.8, 0.8, 0.8, 1), 0.05, 0.1)
    text.data.materials.append(material)
    bpy.ops.object.modifier_add(type='EDGE_SPLIT')

def create_pan():
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(-0.3, 0, 0.7), scale=(1.5, 1.5, 0.135))
    bpy.ops.object.mode_set(mode='EDIT')
    # get created object
    obj = bpy.context.object
    obj.name = 'Pan'
    # get the mesh data
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    # delete top face
    bm.faces.ensure_lookup_table()
    faces = bm.faces[5]
    bmesh.ops.delete(bm, geom=[faces], context="FACES")

    # select top edge
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action = 'DESELECT')
    # we need to switch from Edit mode to Object mode so the selection gets updated
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in mesh.vertices:
        if v.co[2] > 0:
            v.select = True
    bpy.ops.object.mode_set(mode='EDIT')

    # extrude and scale it
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.resize(value=(1.05, 1.05, 1.05), constraint_axis=(False, False, False))
    # extrude z -0.07
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, -0.07), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    # extrude and scale it
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.resize(value=(0.97, 0.97, 0.97), constraint_axis=(False, False, False))

    # bevel edge
    bpy.ops.mesh.select_all(action = 'SELECT')
    bpy.ops.mesh.bevel(offset=0.01, offset_pct=0, affect='EDGES')

    bmesh.update_edit_mesh(mesh)
    # add subdivision
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.subdivision_set(level=3, relative=False)
    bpy.context.object.modifiers["Subdivision"].render_levels = 3
    bpy.ops.object.shade_smooth()
    bpy.ops.transform.translate(value=(-0, -0, -1.3), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    # add material
    material = glossy_material(roughness=0.3)
    bpy.context.object.data.materials.append(material)

    # fix water too much
    bpy.ops.transform.resize(value=(1, 1, 3), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.transform.translate(value=(0, 0, -0.27), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

def create_light():
    light = bpy.data.objects['Light']
    light.data.energy = 5000
    light.data.shadow_soft_size = 3

def cycles_render(samples):
    bpy.context.scene.frame_end = 120
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_current = 1
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.preview_samples = samples
    bpy.context.scene.cycles.samples = samples

def create_plane():
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, 0, -0.74), size=100)
    bpy.context.object.name = 'Floor'
    # add material
    material = principled_material()
    bpy.context.object.data.materials.append(material)
    bpy.ops.transform.translate(value=(-0, -0, -0.54), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

def position_camera():
    #camera = bpy.data.objects['Camera']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['Camera'].select_set(True)
    bpy.ops.transform.rotate(value=math.radians(-20), orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.transform.translate(value=(-3.4, -1, -0.4), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

    # fix water too much
    bpy.ops.transform.translate(value=(-0, -0, -0.2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.transform.translate(value=(0, 0, 1.7), orient_type='LOCAL', orient_matrix=((0.893435, 0.449193, 0), (-0.200013, 0.397821, 0.895396), (0.402206, -0.799977, 0.445271)), orient_matrix_type='LOCAL', constraint_axis=(True, True, True), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

class WaterBalancing(bpy.types.Operator):
    bl_idname = "object.water_balancing"        # Unique identifier for buttons and menu items to reference.
    bl_label = "water balancing"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def execute(self, context):        # execute() is called when running the operator.
        create_pipe()
        create_domain()
        create_inflow()
        create_effector()
        create_pan()
        create_light()
        cycles_render(50)
        create_plane()
        background_settings()
        position_camera()

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

def menu_func(self, context):
    self.layout.operator(WaterBalancing.bl_idname)

def register():
    bpy.utils.register_class(WaterBalancing)
    bpy.types.VIEW3D_MT_object.append(menu_func)  # Adds the new operator to an existing menu.

def unregister():
    bpy.utils.unregister_class(WaterBalancing)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
