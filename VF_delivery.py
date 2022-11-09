bl_info = {
	"name": "VF Delivery",
	"author": "John Einselen - Vectorform LLC",
	"version": (0, 6, 2),
	"blender": (3, 2, 0),
	"location": "Scene > VF Tools > Delivery",
	"description": "Quickly export selected objects to a specified directory",
	"warning": "inexperienced developer, use at your own risk",
	"wiki_url": "",
	"tracker_url": "",
	"category": "3D View"}

import bpy
from bpy.app.handlers import persistent
import mathutils
import numpy as np

# With help from:
# https://stackoverflow.com/questions/54464682/best-way-to-undo-previous-steps-in-a-series-of-steps
# https://stackoverflow.com/questions/37335653/unable-to-completely-deselect-all-objects-in-blender-using-scripting-or-key-a
# https://blender.stackexchange.com/questions/200341/apply-modifiers-in-all-objects-at-once
# https://github.com/CheeryLee/blender_apply_modifiers/blob/master/apply_modifiers.py

###########################################################################
# Main class

class VFDELIVERY_OT_file(bpy.types.Operator):
	bl_idname = "vfdelivery.file"
	bl_label = "Deliver File"
	bl_description = "Quickly export selected objects or collection to a specified directory"
#	bl_options = {'REGISTER', 'UNDO'}
	
	def execute(self, context):
		# Set up local variables
		location = bpy.context.scene.vf_delivery_settings.file_location
		format = bpy.context.scene.vf_delivery_settings.file_type

		# Save current mode
		mode = bpy.context.active_object.mode

		# Override mode to OBJECT
		bpy.ops.object.mode_set(mode='OBJECT')

		# Check if an object is selected, if not, export collection instead
		if bpy.context.object and bpy.context.object.select_get():
			object_toggle = True
			collection_toggle = False
			file_name = bpy.context.active_object.name
		else:
			object_toggle = False
			collection_toggle = True
			file_name = bpy.context.collection.name

		# Create file format based on pipeline selection
		file_format = "." + format.lower()

		if format == "ABC":
			if collection_toggle:
				# Push an undo state (this was intended to reset the collection selection status, but doesn't really work)
				bpy.ops.ed.undo_push()
				for obj in bpy.context.collection.all_objects:
					obj.select_set(True)

			bpy.ops.wm.alembic_export(
				filepath=location + file_name + file_format,
				check_existing=False, # Always overwrite existing files
				start=0,
				end=0,
				xsamples=1,
				gsamples=1,
				selected=True,
				visible_objects_only=False,
				flatten=False,
				uvs=True,
				packuv=False, # Changed from default to prevent UV map alteration
				normals=True,
				vcolors=True, # Changed from default to include vertex colors
				orcos=True,
				face_sets=False,
				subdiv_schema=False,
				apply_subdiv=False,
				curves_as_mesh=False,
				use_instancing=True,
				global_scale=1.0,
				triangulate=False,
				quad_method='SHORTEST_DIAGONAL',
				ngon_method='BEAUTY',
				export_hair=True,
				export_particles=True,
				export_custom_properties=False, # Changed from default
				evaluation_mode='RENDER')

			if collection_toggle:
				# Undo the collection object selection status
				bpy.ops.ed.undo()

		elif format == "FBX":
			# Push an undo state (seems easier than trying to re-select previously selected non-MESH objects)
			bpy.ops.ed.undo_push()

			# Apply all modifiers to MESH objects and convert "UVmap" attribute to UV map
			for obj in bpy.context.selected_objects:
				if obj.type == "MESH":
					# Set active
					bpy.context.view_layer.objects.active = obj

					# Apply all modifiers
					bpy.ops.object.apply_all_modifiers()

					# Convert "UVMap" attribute to UV map data type (if it exists and is selected by default...python API seems pretty limited here?)
					if obj.data.attributes.get("UVMap") and obj.data.attributes.active.name == "UVMap":
						bpy.ops.geometry.attribute_convert(mode='UV_MAP')

			bpy.ops.export_scene.fbx(
				filepath=location + file_name + file_format,
				check_existing=False, # Always overwrite existing files (dangerous...designed specifically for Unity delivery!)
				use_selection=object_toggle, # If an object is selected, export only selected objects
				use_visible=True,
				use_active_collection=collection_toggle, # If an object isn't selected, export the active collection
				
				global_scale=1.0, # 1.0
				apply_unit_scale=True,
				apply_scale_options='FBX_SCALE_NONE', # FBX_SCALE_NONE = All Local
				use_space_transform=True,
				axis_forward='-Z',
				axis_up='Y',
				object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'},
				bake_space_transform=True, # True (this is "!experimental!")
				
				use_mesh_modifiers=True, # Come back to this...manually trigger application of mesh modifiers and convert attributes to UV maps
				use_mesh_modifiers_render=True,
				mesh_smooth_type='OFF', # OFF = Normals Only
				use_subsurf=False, # Seems unhelpful for realtime (until realtime supports live subdivision cross-platform)
				use_mesh_edges=False,
				use_tspace=False,
				use_triangles=True, # This wasn't included in the "perfect" Unity settings, but seems logical?
				use_custom_props=False,
				
				use_armature_deform_only=True, # True
				add_leaf_bones=False, # False
				primary_bone_axis='X', # X Axis
				secondary_bone_axis='Y', # Y Axis
				armature_nodetype='NULL',
				
				bake_anim=True,
				bake_anim_use_all_bones=True,
				bake_anim_use_nla_strips=True,
				bake_anim_use_all_actions=True,
				bake_anim_force_startend_keying=True, # Some recommend False, but Unity may not load animations nicely without starting keyframes
				bake_anim_step=1.0,
				bake_anim_simplify_factor=1.0,
				
				path_mode='AUTO',
				embed_textures=False,
				batch_mode='OFF',
				use_batch_own_dir=False,
				use_metadata=True)
			
			# Undo the previously completed object modifications
			bpy.ops.ed.undo()
			bpy.ops.ed.undo()

		elif format == "GLB":
			bpy.ops.export_scene.gltf(
				filepath=location + file_name + file_format,
				check_existing=False, # Always overwrite existing files (dangerous...designed specifically for ThreeJS delivery!)
				export_format='GLB',
				export_copyright='',
				
				export_image_format='JPEG',
				export_texcoords=True,
				export_normals=True,
				export_draco_mesh_compression_enable=True,
				export_draco_mesh_compression_level=6,
				export_draco_position_quantization=14,
				export_draco_normal_quantization=10,
				export_draco_texcoord_quantization=12,
				export_draco_color_quantization=10,
				export_draco_generic_quantization=12,
				
				export_tangents=False,
				export_materials='EXPORT',
				export_colors=True,
				use_mesh_edges=False,
				use_mesh_vertices=False,
				export_cameras=False,
				
				use_selection=object_toggle,
				use_visible=True,
				use_renderable=True,
				use_active_collection=collection_toggle,
				use_active_scene=False,
				
				export_extras=False,
				export_yup=True,
				export_apply=True,
				
				export_animations=True,
				export_frame_range=True,
				export_frame_step=1,
				export_force_sampling=True,
				export_nla_strips=True,
				export_def_bones=True, # Changed from default
				optimize_animation_size=True, # Changed from default, may cause issues with stepped animations
				export_current_frame=False,
				export_skins=True,
				export_all_influences=False,
				
				export_morph=True,
				export_morph_normal=True,
				export_morph_tangent=False,
				
				export_lights=False,
				will_save_settings=False,
				filter_glob='*.glb;*.gltf')

		elif format == "STL":
			# Push an undo state (seems easier than trying to re-select previously selected non-MESH objects)
			bpy.ops.ed.undo_push()

			# Deselect non-MESH objects first
			for obj in bpy.context.selected_objects:
				if obj.type != "MESH":
					obj.select_set(False)

			bpy.ops.export_mesh.stl(
				filepath=location,
				ascii=False,
				check_existing=False, # Dangerous!
				use_selection=True,
				batch_mode='OBJECT',

				global_scale=1.0,
				use_scene_unit=False,
				use_mesh_modifiers=True,

				axis_forward='Y',
				axis_up='Z',
				filter_glob='*.stl')
			
			# Undo the previously completed object deselection
			bpy.ops.ed.undo()

		elif format == "CSV":
			# Save timeline position
			frame_current = bpy.context.scene.frame_current

			# Set variables
			frame_start = bpy.context.scene.frame_start
			frame_end = bpy.context.scene.frame_end
			source_object = "something"
			file_output = "file location" + "file name" + ".csv"
			space = bpy.context.scene.vf_delivery_settings.csv_position

			# Collect data
			array = [["x","y","z"]]
			for i in range(frame_start, frame_end + 1):
				bpy.context.scene.frame_set(i)
				loc, rot, scale = bpy.context.object.matrix_world.decompose() if space == "WORLD" else bpy.context.object.matrix_local.decompose()
				array.append([loc.x, loc.y, loc.z])

			# Save out CSV file
			np.savetxt(
				location + file_name + file_format,
				array,
				delimiter =",",
				newline='\n',
				fmt ='% s'
				)

			# Reset timeline position
			bpy.context.scene.frame_set(frame_current)

		# Reset to original mode
		bpy.ops.object.mode_set(mode=mode)

		# Done
		return {'FINISHED'}

###########################################################################
# Project settings and UI rendering classes

class vfDeliverySettings(bpy.types.PropertyGroup):
	file_type: bpy.props.EnumProperty(
		name='Pipeline',
		description='Sets the format for delivery output',
		items=[
			('ABC', 'ABC — Static', 'Export Alembic binary file from frame 0'),
			('FBX', 'FBX — Unity3D', 'Export FBX binary file for Unity'),
			('GLB', 'GLB — ThreeJS', 'Export GLTF compressed binary file for ThreeJS'),
			('STL', 'STL — 3D Printing', 'Export individual STL file of each selected object for 3D printing'),
			('CSV', 'CSV — Data Vis', 'Export CSV file of the selected object\'s position, rotation, and scale for all frames within the render range')
			],
		default='FBX')
	file_location: bpy.props.StringProperty(
		name="Delivery Location",
		description="Delivery location for all exported files",
		default="/",
		maxlen=4096,
		subtype="DIR_PATH")
	csv_position: bpy.props.EnumProperty(
		name='Position',
		description='Sets local or world space coordinates',
		items=[
			('WORLD', 'World', 'World space'),
			('LOCAL', 'Local', 'Local object space')
			],
		default='WORLD')
	csv_rotation: bpy.props.EnumProperty(
		name='Rotation',
		description='Sets the formatting of rotation values',
		items=[
			('RAD', 'Radians', 'Output rotation in radians'),
			('DEG', 'Degrees', 'Output rotation in degrees')
			],
		default='RAD')

class VFTOOLS_PT_delivery(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'VF Tools'
	bl_order = 0
	bl_options = {'DEFAULT_CLOSED'}
	bl_label = "Delivery"
	bl_idname = "VFTOOLS_PT_delivery"

	@classmethod
	def poll(cls, context):
		return True

	def draw_header(self, context):
		try:
			layout = self.layout
		except Exception as exc:
			print(str(exc) + " | Error in VF Delivery panel header")

	def draw(self, context):
		try:
			# Set up variables
			file_format = "." + context.scene.vf_delivery_settings.file_type.lower()
			file_icon="FILE"

			if bpy.context.object and bpy.context.object.select_get():
				file_name = bpy.context.active_object.name + file_format
				file_icon = "OUTLINER_OB_MESH"
			else:
				file_name = bpy.context.collection.name + file_format
				file_icon = "OUTLINER_COLLECTION"

			# UI Layout
			layout = self.layout
			layout.use_property_decorate = False # No animation
			layout.prop(context.scene.vf_delivery_settings, 'file_location', text='')

			layout.prop(context.scene.vf_delivery_settings, 'file_type', text='')
			if context.scene.vf_delivery_settings.file_type == "STL":
				object_count = [obj.type for obj in bpy.context.selected_objects].count("MESH")
				if object_count == 0:
					hold = layout.row()
					hold.active = False
					hold.enabled = False
					hold.operator(VFDELIVERY_OT_file.bl_idname, text="No mesh selected", icon="X")
				elif object_count == 1:
					layout.operator(VFDELIVERY_OT_file.bl_idname, text=file_name, icon=file_icon)
				else:
					layout.operator(VFDELIVERY_OT_file.bl_idname, text=str(object_count) + " files", icon=file_icon)
			elif context.scene.vf_delivery_settings.file_type == "CSV":
				layout.prop(context.scene.vf_delivery_settings, 'csv_position', expand=True)
				if len(bpy.context.selected_objects) == 1:
					layout.operator(VFDELIVERY_OT_file.bl_idname, text=file_name, icon=file_icon)
				else:
					hold = layout.row()
					hold.active = False
					hold.enabled = False
					hold.operator(VFDELIVERY_OT_file.bl_idname, text="select one object", icon="X")
			else:
				layout.operator(VFDELIVERY_OT_file.bl_idname, text=file_name, icon=file_icon)

		except Exception as exc:
			print(str(exc) + " | Error in VF Delivery panel")

classes = (VFDELIVERY_OT_file, vfDeliverySettings, VFTOOLS_PT_delivery)

###########################################################################
# Addon registration functions

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Scene.vf_delivery_settings = bpy.props.PointerProperty(type=vfDeliverySettings)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.vf_delivery_settings

if __name__ == "__main__":
	register()
	