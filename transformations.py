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
    else:
        principled_node.inputs['Base Color'].default_value = color
    principled_node.inputs['Roughness'].default_value = roughness
    links.new(principled_node.outputs[0], output_node.inputs[0])
    return material

def create_explode(size, frame_start, frame_end, physics_type, show_unborn, show_dead, color=hex_to_rgb(0x0000ff), location=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=location, rotation=(math.radians(90), 0, math.radians(90)), major_radius=1, minor_radius=0.25, abso_major_rad=1.25, abso_minor_rad=0.75)
    bpy.ops.transform.resize(value=size, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    bpy.ops.object.subdivision_set(level=3, relative=False)
    bpy.context.object.modifiers["Subdivision"].render_levels = 3
    bpy.ops.object.shade_smooth()
    bpy.ops.object.quick_explode(frame_start=1, frame_end=51)
    #settings = bpy.data.particles["ParticleSettings"]
    obj = bpy.context.object
    settings = obj.particle_systems[0].settings
    settings.count = 36000
    settings.frame_start = frame_start
    settings.frame_end = frame_end
    settings.normal_factor = 0
    settings.factor_random = 0
    settings.effector_weights.gravity = 0

    settings.physics_type = physics_type
    #psys = bpy.context.object.particle_systems[0]
    #bpy.ops.particle.new_target()
    #ptarget = psys.active_particle_target
    #ptarget.object = bpy.data.objects['Torus']

    bpy.context.object.modifiers["Explode"].show_unborn = show_unborn
    bpy.context.object.modifiers["Explode"].show_dead = show_dead
    bpy.context.object.modifiers["Explode"].use_edge_cut = False

    # particle from left to right
    tex = bpy.data.textures.new(name = 'tex', type = 'BLEND')
    #bpy.data.textures["Texture"].use_color_ramp = True

    mtex = settings.texture_slots.add()
    mtex.blend_type = 'MULTIPLY'
    mtex.texture = tex
    mtex.texture_coords = 'ORCO'

    # add material
    bpy.ops.object.material_slot_remove()
    material = principled_material(color, roughness=0.4)
    bpy.context.object.data.materials.append(material)

def create_turbulence():
    # make particle fly
    bpy.ops.object.effector_add(type='TURBULENCE', enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.field.strength = 0.5

def position_camera():
    camera = bpy.data.objects['Camera']
    camera.location = Vector((11, 0, 0))
    camera.rotation_euler = mathutils.Euler((math.radians(90.0), 0.0, math.radians(90.0)), 'XYZ')

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

def create_light(energy):
    light = bpy.data.objects['Light']
    light.data.energy = energy
    light.data.shadow_soft_size = 3

class transformations(bpy.types.Operator):
    bl_idname = "object.transformations"        # Unique identifier for buttons and menu items to reference.
    bl_label = "transformations"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def execute(self, context):        # execute() is called when running the operator.
        create_explode(size=(1.5, 1.5, 1.5), frame_start=10, frame_end=110, physics_type='NEWTON', show_unborn=True, show_dead=False)
        #create_explode(size=(0.75, 0.75, 0.75), frame_start=60, frame_end=160, physics_type='KEYED', show_unborn=False, show_dead=True)
        
        # blue to red
        create_explode(size=(0.75, 0.75, 0.75), frame_start=60, frame_end=160, physics_type='KEYED', show_unborn=False, show_dead=True, color=hex_to_rgb(0xff0000))
        
        # different location
        #create_explode(size=(1.5, 1.5, 1.5), frame_start=10, frame_end=110, physics_type='NEWTON', show_unborn=True, show_dead=False, location=(0, 1.5, 0))
        #create_explode(size=(1.5, 1.5, 1.5), frame_start=60, frame_end=160, physics_type='KEYED', show_unborn=False, show_dead=True, location=(0, -1.5, 0))

        create_turbulence()
        position_camera()
        render('BLENDER_EEVEE', 210)
        create_light(3000)
        # set world to black
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

def menu_func(self, context):
    self.layout.operator(transformations.bl_idname)

def register():
    bpy.utils.register_class(transformations)
    bpy.types.VIEW3D_MT_object.append(menu_func)  # Adds the new operator to an existing menu.

def unregister():
    bpy.utils.unregister_class(transformations)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()