bl_info = {
	"name": "VF Delivery",
	"author": "John Einselen - Vectorform LLC",
	"version": (0, 7, 5),
	"blender": (3, 3, 1),
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
		combined = True if bpy.context.scene.vf_delivery_settings.file_grouping == "COMBINED" else False
		file_format = "." + format.lower()
		# Experimental UV map
		uvmap_experimental = bpy.context.scene.vf_delivery_settings.uvmap_experimental

		# Save current mode
		mode = bpy.context.active_object.mode

		# Override mode to OBJECT
		bpy.ops.object.mode_set(mode='OBJECT')

		# Check if an object is selected, if not, convert selected collection into object selection
		if bpy.context.object and bpy.context.object.select_get():
			file_name = bpy.context.active_object.name
		else:
			file_name = bpy.context.collection.name
			for obj in bpy.context.collection.all_objects:
				obj.select_set(True)

		if format != "CSV":
			# Push an undo state (seems easier than trying to re-select previously selected non-mesh objects)
			bpy.ops.ed.undo_push()

			# Deselect any non-mesh objects
			for obj in bpy.context.selected_objects:
				if obj.type != "MESH":
					obj.select_set(False)

		# Begin primary export section (formats that support UV maps)
		if format == "ABC" or format == "FBX" or format == "GLB":
			# Push an undo state (seems easier than trying to re-select previously selected non-MESH objects)
			# But this isn't working, right? Sigh...
			# Track number of undo steps to retrace after export is complete
			bpy.ops.ed.undo_push()
			undo_steps = 1

			if bpy.context.preferences.addons['VF_delivery'].preferences.enable_uvmap_experimental and uvmap_experimental:
				# Geometry Nodes (as of Blender 3.3) does not support UVMap export because they exist only as an incompatible named attribute
				# To work around this issue all modifiers must be applied to meshes and any "UVmap" named attribute converted into a valid UV map
				for obj in bpy.context.selected_objects:
					if obj.type == "MESH":
						# Set active
						bpy.context.view_layer.objects.active = obj

						# Apply all modifiers
						if len(obj.modifiers) > 0:
							bpy.ops.ed.undo_push()
							undo_steps += 1
							bpy.ops.object.apply_all_modifiers()

						# Convert "UVMap" attribute to UV map data type
						# If it exists and is selected by default...python API seems very limited here
						if obj.data.attributes.get("UVMap") and obj.data.attributes.active.name == "UVMap":
							bpy.ops.ed.undo_push()
							undo_steps += 1
							bpy.ops.geometry.attribute_convert(mode='UV_MAP')

			# Loop through each of the selected objects
			# But only set individual selections if file export is set to individual
			# Otherwise loop once and exit (see the if statement at the very end)
			for obj in bpy.context.selected_objects:
				if not combined:
					print("INDIVIDUAL")
					print("selected: " + str(len(bpy.context.selected_objects)))
					# deselect everything
					for selobj in bpy.context.selected_objects:
						selobj.select_set(False)
					# select individual object
					obj.select_set(True)
					file_name = obj.name
					print("selected: " + str(len(bpy.context.selected_objects)))

				if format == "ABC":
					print("EXPORT: ABC")
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

				elif format == "FBX":
					print("EXPORT: FBX")
					bpy.ops.export_scene.fbx(
						filepath=location + file_name + file_format,
						check_existing=False, # Always overwrite existing files (dangerous...designed specifically for Unity delivery!)
						use_selection=True,
						use_visible=True,
						use_active_collection=False, # This is now hardcoded, as we're converting collection selection into object selection manually above

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

				elif format == "GLB":
					print("EXPORT: GLB")
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

						use_selection=True,
						use_visible=True,
						use_renderable=True,
						use_active_collection=False, # This is hardcoded now, as collections are converted manually to object selections above
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
						export_optimize_animation_size=True, # Changed from default, may cause issues with stepped animations
						export_current_frame=False,
						export_skins=True,
						export_all_influences=False,

						export_morph=True,
						export_morph_normal=True,
						export_morph_tangent=False,

						export_lights=False,
						will_save_settings=False,
						filter_glob='*.glb;*.gltf')

				# Interrupt the loop if we're exporting all objects to the same file
				if combined:
					break

			# Undo the previously completed object modifications
			for i in range(undo_steps):
				bpy.ops.ed.undo()

		# End primary exprt section (formats that support UV maps)
		# Begin secondary export section (formats that do not support UV maps)

		elif format == "STL":
			batch = 'OFF' if combined else 'OBJECT'
			output = location + file_name + file_format if combined else location
			bpy.ops.export_mesh.stl(
				filepath=output,
				ascii=False,
				check_existing=False, # Dangerous!
				use_selection=True,
				batch_mode=batch,

				global_scale=1.0,
				use_scene_unit=False,
				use_mesh_modifiers=True,

				axis_forward='Y',
				axis_up='Z',
				filter_glob='*.stl')

		elif format == "CSV":
			# Save timeline position
			frame_current = bpy.context.scene.frame_current

			# Set variables
			frame_start = bpy.context.scene.frame_start
			frame_end = bpy.context.scene.frame_end
			space = bpy.context.scene.vf_delivery_settings.csv_position

			for obj in bpy.context.selected_objects:
				# Collect data
				array = [["x","y","z"]]
				for i in range(frame_start, frame_end + 1):
					bpy.context.scene.frame_set(i)
					loc, rot, scale = obj.matrix_world.decompose() if space == "WORLD" else obj.matrix_local.decompose()
					array.append([loc.x, loc.y, loc.z])

				# Save out CSV file
				np.savetxt(
					location + obj.name + file_format,
					array,
					delimiter =",",
					newline='\n',
					fmt ='% s'
					)

			# Reset timeline position
			bpy.context.scene.frame_set(frame_current)

		if format != "CSV":
			# Undo the previously completed non-mesh object deselection
			bpy.ops.ed.undo()

		# Reset to original mode
		bpy.ops.object.mode_set(mode=mode)

		# Done
		return {'FINISHED'}

###########################################################################
# Global user preferences and UI rendering class

class vfDeliveryPreferences(bpy.types.AddonPreferences):
	bl_idname = __name__

	# Global Variables
	enable_uvmap_experimental: bpy.props.BoolProperty(
		name='Enable experimental UVMap conversion',
		description='Attempts to convert the first named attribute output from a Geometry Nodes modifier into a UV map recognisable by file exporters',
		default=False)

	# User Interface
	def draw(self, context):
		layout = self.layout
		layout.prop(self, "enable_uvmap_experimental")

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
			('CSV', 'CSV — Position', 'Export CSV file of the selected object\'s position for all frames within the render range')
			],
		default='FBX')
	file_location: bpy.props.StringProperty(
		name="Delivery Location",
		description="Delivery location for all exported files",
		default="/",
		maxlen=4096,
		subtype="DIR_PATH")
	uvmap_experimental: bpy.props.BoolProperty(
		name="Convert UVMap Attribute",
		description="Attempts to export UVMap data by applying all modifiers and converting any \"UVMap\" named attributes to an actual UV map",
		default=False)
	file_grouping: bpy.props.EnumProperty(
		name='Grouping',
		description='Sets combined or individual file outputs',
		items=[
			('COMBINED', 'Combined', 'Export selection in one file'),
			('INDIVIDUAL', 'Individual', 'Export selection as individual files')
			],
		default='COMBINED')
	csv_position: bpy.props.EnumProperty(
		name='Position',
		description='Sets local or world space coordinates',
		items=[
			('WORLD', 'World', 'World space'),
			('LOCAL', 'Local', 'Local object space')
			],
		default='WORLD')
#	csv_rotation: bpy.props.EnumProperty(
#		name='Rotation',
#		description='Sets the formatting of rotation values',
#		items=[
#			('RAD', 'Radians', 'Output rotation in radians'),
#			('DEG', 'Degrees', 'Output rotation in degrees')
#			],
#		default='RAD')

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
			button_enable = True
			button_icon = "FILE"
			button_title = ''
			show_group = True
			show_uvmap = bpy.context.preferences.addons['VF_delivery'].preferences.enable_uvmap_experimental
			show_csv = False
			object_count = 0

			# Update variables based on object selection status
			if bpy.context.object and bpy.context.object.select_get():
				# Count any items for CSV, count only meshes for everything else
				if context.scene.vf_delivery_settings.file_type == "CSV":
					object_count = len(bpy.context.selected_objects)
				else:
					object_count = [obj.type for obj in bpy.context.selected_objects].count("MESH")

				# Button icon
				button_icon = "OUTLINER_OB_MESH"

				# Button title
				if (object_count > 1 and context.scene.vf_delivery_settings.file_grouping == "COMBINED" and not context.scene.vf_delivery_settings.file_type == "CSV"):
					button_title = bpy.context.active_object.name + file_format
				elif object_count == 1:
					if bpy.context.active_object.type != "MESH" and context.scene.vf_delivery_settings.file_grouping == "INDIVIDUAL":
						for obj in bpy.context.selected_objects:
							if obj.type == "MESH":
								button_title = obj.name + file_format
					else:
						button_title = bpy.context.active_object.name + file_format
				else:
					button_title = str(object_count) + " files"

			# Update variables based on active collection if no object is selected
			else:
				# Count any items within the collection for CSV, count only meshes for everything else
				if context.scene.vf_delivery_settings.file_type == "CSV":
					object_count = len(bpy.context.collection.all_objects)
				else:
					object_count = [obj.type for obj in bpy.context.collection.all_objects].count("MESH")

				# Button icon
				button_icon = "OUTLINER_COLLECTION"

				# Button title
				if context.scene.vf_delivery_settings.file_grouping == "COMBINED" and not context.scene.vf_delivery_settings.file_type == "CSV":
					button_title = bpy.context.collection.name + file_format
				else:
					button_title = str(object_count) + " files"

			# If no usable items (CSV) or meshes (everything else) is found, disable the button
			# Keeping the message generic allows this to be used universally
			if object_count == 0:
				button_enable = False
				button_icon = "X"
#				button_title = "No useable selection"
#				button_title = "select item(s)"
				if context.scene.vf_delivery_settings.file_type == "CSV":
					button_title = "Select object"
				else:
					button_title = "Select mesh"

			# Specific display cases
			if context.scene.vf_delivery_settings.file_type == "CSV":
				show_group = False
				show_uvmap = False
				show_csv = True
			elif context.scene.vf_delivery_settings.file_type == "STL":
				show_uvmap = False

			# UI Layout
			layout = self.layout
			layout.use_property_decorate = False # No animation

			layout.prop(context.scene.vf_delivery_settings, 'file_location', text='')
			layout.prop(context.scene.vf_delivery_settings, 'file_type', text='')

			if show_uvmap:
				layout.prop(context.scene.vf_delivery_settings, 'uvmap_experimental')

			if show_group:
				layout.prop(context.scene.vf_delivery_settings, 'file_grouping', expand=True)

			if show_csv:
				layout.prop(context.scene.vf_delivery_settings, 'csv_position', expand=True)

			if button_enable:
				layout.operator(VFDELIVERY_OT_file.bl_idname, text=button_title, icon=button_icon)
			else:
				disabled = layout.row()
				disabled.active = False
				disabled.enabled = False
				disabled.operator(VFDELIVERY_OT_file.bl_idname, text=button_title, icon=button_icon)

		except Exception as exc:
			print(str(exc) + " | Error in VF Delivery panel")

classes = (VFDELIVERY_OT_file, vfDeliveryPreferences, vfDeliverySettings, VFTOOLS_PT_delivery)

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