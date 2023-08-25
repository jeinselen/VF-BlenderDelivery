bl_info = {
	"name": "VF Delivery",
	"author": "John Einselen - Vectorform LLC",
	"version": (0, 10, 0),
	"blender": (3, 3, 1),
	"location": "Scene > VF Tools > Delivery",
	"description": "Quickly export selected objects to a specified directory",
	"warning": "inexperienced developer, use at your own risk",
	"doc_url": "https://github.com/jeinselenVF/VF-BlenderDelivery",
	"tracker_url": "https://github.com/jeinselenVF/VF-BlenderDelivery/issues",
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

# Define allowed object types
VF_delivery_object_types = ['CURVE', 'MESH', 'META', 'SURFACE', 'FONT']
# Not all types are supported by all exporters, see the GitHub documentation for more details

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
		active_object = bpy.context.active_object
		
		# Save then override the current mode to OBJECT
		if active_object is not None:
			object_mode = active_object.mode
			bpy.ops.object.mode_set(mode = 'OBJECT')
				
		# Check if an object is selected, if not, convert selected collection into object selection
		if bpy.context.object and bpy.context.object.select_get():
			file_name = active_object.name
		else:
			file_name = bpy.context.collection.name
			for obj in bpy.context.collection.all_objects:
				obj.select_set(True)
				
		if format != "CSV":
			# Push an undo state (seems easier than trying to re-select previously selected non-mesh objects)
			bpy.ops.ed.undo_push()
			
			# Deselect any non-mesh objects
			for obj in bpy.context.selected_objects:
				if obj.type not in VF_delivery_object_types:
					obj.select_set(False)
					
		# Begin primary export section (formats that support UV maps)
		if format == "FBX" or format == "GLB" or format == "OBJ" or format == "USDZ":
			# Push an undo state (easier than trying to re-select previously selected non-MESH objects?)
			bpy.ops.ed.undo_push()
			# Track number of undo steps to retrace after export is complete
			undo_steps = 1
			
			# Loop through each of the selected objects
			# But only set individual selections if file export is set to individual
			# Otherwise loop once and exit (see the if statement at the very end)
			for obj in bpy.context.selected_objects:
				if not combined:
					# deselect everything
					for selobj in bpy.context.selected_objects:
						selobj.select_set(False)
					# select individual object
					obj.select_set(True)
					file_name = obj.name
					# Note to future self; you probably missed the comment block just above. Please stop freaking out. When combined is true the loop is exited after the first export pass. You can stop frantically scrolling for multi-export errors, you'll just get to the end of this section and figure out the solution is already implemented. Again.
				
				elif format == "FBX":
					bpy.ops.export_scene.fbx(
						filepath = location + file_name + file_format,
						check_existing = False, # Always overwrite existing files
						use_selection = True,
						use_visible = True,
						use_active_collection = False, # This is now hardcoded, as we're converting collection selection into object selection manually above

						global_scale = 1.0, # 1.0
						apply_unit_scale = True,
						apply_scale_options = 'FBX_SCALE_NONE', # FBX_SCALE_NONE = All Local
						use_space_transform = True,
						axis_forward = '-Z',
						axis_up = 'Y',
						object_types = {'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'},
						bake_space_transform = True, # True (this is "!experimental!")

						use_mesh_modifiers = True, # Come back to this...manually trigger application of mesh modifiers and convert attributes to UV maps
						use_mesh_modifiers_render = True,
						mesh_smooth_type = 'OFF', # OFF = Normals Only
						use_subsurf = False, # Seems unhelpful for realtime (until realtime supports live subdivision cross-platform)
						use_mesh_edges = False,
						use_tspace = False,
						use_triangles = True, # This wasn't included in the "perfect" Unity settings, but seems logical?
						use_custom_props = False,

						use_armature_deform_only = True, # True
						add_leaf_bones = False, # False
						primary_bone_axis = 'X', # X Axis
						secondary_bone_axis = 'Y', # Y Axis
						armature_nodetype = 'NULL',

						bake_anim = True,
						bake_anim_use_all_bones = True,
						bake_anim_use_nla_strips = True,
						bake_anim_use_all_actions = True,
						bake_anim_force_startend_keying = True, # Some recommend False, but Unity may not load animations nicely without starting keyframes
						bake_anim_step = 1.0,
						bake_anim_simplify_factor = 1.0,

						path_mode = 'AUTO',
						embed_textures = False,
						batch_mode = 'OFF',
						use_batch_own_dir = False,
						use_metadata = True)
					
				elif format == "GLB":
					bpy.ops.export_scene.gltf(
						filepath = location + file_name + file_format,
						check_existing = False, # Always overwrite existing files
						export_format = 'GLB',
						export_copyright = '',

						export_image_format = 'JPEG',
						export_texcoords = True,
						export_normals = True,
						export_draco_mesh_compression_enable = True,
						export_draco_mesh_compression_level = 6,
						export_draco_position_quantization = 14,
						export_draco_normal_quantization = 10,
						export_draco_texcoord_quantization = 12,
						export_draco_color_quantization = 10,
						export_draco_generic_quantization = 12,

						export_tangents = False,
						export_materials = 'EXPORT',
						export_colors = True,
						use_mesh_edges = False,
						use_mesh_vertices = False,
						export_cameras = False,

						use_selection = True,
						use_visible = True,
						use_renderable = True,
						use_active_collection = False, # This is hardcoded now, as collections are converted manually to object selections above
						use_active_scene = False,

						export_extras = False,
						export_yup = True,
						export_apply = True,

						export_animations = True,
						export_frame_range = True,
						export_frame_step = 1,
						export_force_sampling = True,
						export_nla_strips = True,
						export_def_bones = True, # Changed from default
						export_optimize_animation_size = True, # Changed from default, may cause issues with stepped animations
						export_current_frame = False,
						export_skins = True,
						export_all_influences = False,

						export_morph = True,
						export_morph_normal = True,
						export_morph_tangent = False,

						export_lights = False,
						will_save_settings = False,
						filter_glob = '*.glb;*.gltf')
					
				elif format == "OBJ":
					bpy.ops.export_scene.obj(
						filepath = location + file_name + file_format,
						check_existing = False, # Always overwrite existing files
						filter_glob = '*.obj;*.mtl',
						
						use_selection = True,
						use_animation = False,
						use_mesh_modifiers = True,
						use_edges = False, # Changed from default
						use_smooth_groups = False,
						use_smooth_groups_bitflags = False,
						use_normals = True,
						use_uvs = True,
						use_materials = True,
						use_triangles = True, # Changed from default
						use_nurbs = False,
						use_vertex_groups = False,
						use_blen_objects = True,
						group_by_object = False,
						group_by_material = False,
						keep_vertex_order = True, # Changed from default
						global_scale = 100.0,
						path_mode = 'AUTO',
						axis_forward = '-Z',
						axis_up = 'Y')
				
				elif format == "USDZ":
					bpy.ops.wm.usd_export(
						filepath = location + file_name + file_format,
						check_existing = False, # Changed from default
						# Removed GUI options
						selected_objects_only = True, # Changed from default
						visible_objects_only = True,
						export_animation = False, # May need to add an option for enabling animation exports depending on the project
						export_hair = False,
						export_uvmaps = True, # Need to test this: USD uses "st" as the default uv map name, and the exporter apparently doesn't convert Blender's default "UVmap" automatically?
						export_normals = True,
						export_materials = True,
						use_instancing = False,
						evaluation_mode = 'RENDER',
						generate_preview_surface = True,
						export_textures = True,
						overwrite_textures = True, # Changed from default
						relative_paths = True)
					
				# Interrupt the loop if we're exporting all objects to the same file
				if combined:
					break
					
			# Undo the previously completed object modifications
			for i in range(undo_steps):
				bpy.ops.ed.undo()
				
		# End primary export section (formats that support UV maps)
		# Begin secondary export section (formats that do not support UV maps)
		
		elif format == "STL":
			batch = 'OFF' if combined else 'OBJECT'
			output = location + file_name + file_format if combined else location
			bpy.ops.export_mesh.stl(
				filepath = output,
				ascii = False,
				check_existing = False, # Dangerous!
				use_selection = True,
				batch_mode = batch,
				
				global_scale = 1.0,
				use_scene_unit = False,
				use_mesh_modifiers = True,
				
				axis_forward = 'Y',
				axis_up = 'Z',
				filter_glob = '*.stl')
			
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
					delimiter = ",",
					newline = '\n',
					fmt = '% s'
					)
					
			# Reset timeline position
			bpy.context.scene.frame_set(frame_current)
			
		if format != "CSV":
			# Undo the previously completed non-mesh object deselection
			bpy.ops.ed.undo()
			
		# Reset to original mode
		if active_object is not None:
			bpy.ops.object.mode_set(mode = object_mode)
		
		# Done
		return {'FINISHED'}

###########################################################################
# Project settings and UI rendering classes

class vfDeliverySettings(bpy.types.PropertyGroup):
	file_type: bpy.props.EnumProperty(
		name = 'Pipeline',
		description = 'Sets the format for delivery output',
		items = [
			('FBX', 'FBX — Unity3D', 'Export FBX binary file for Unity'),
			('GLB', 'GLB — ThreeJS', 'Export GLTF compressed binary file for ThreeJS'),
			('OBJ', 'OBJ — Element3D', 'Export OBJ file for VideoCopilot Element 3D'),
			('USDZ', 'USDZ — Xcode', 'Export USDZ file for Apple platforms including Xcode'),
			(None),
			('STL', 'STL — 3D Printing', 'Export individual STL file of each selected object for 3D printing'),
			(None),
			('CSV', 'CSV — Position', 'Export CSV file of the selected object\'s position for all frames within the render range')
			],
		default = 'FBX')
	file_location: bpy.props.StringProperty(
		name = "Delivery Location",
		description = "Delivery location for all exported files",
		default = "/",
		maxlen = 4096,
		subtype = "DIR_PATH")
	file_grouping: bpy.props.EnumProperty(
		name = 'Grouping',
		description = 'Sets combined or individual file outputs',
		items = [
			('COMBINED', 'Combined', 'Export selection in one file'),
			('INDIVIDUAL', 'Individual', 'Export selection as individual files')
			],
		default = 'COMBINED')
	csv_position: bpy.props.EnumProperty(
		name = 'Position',
		description = 'Sets local or world space coordinates',
		items = [
			('WORLD', 'World', 'World space'),
			('LOCAL', 'Local', 'Local object space')
			],
		default = 'WORLD')
#	csv_rotation: bpy.props.EnumProperty(
#		name = 'Rotation',
#		description = 'Sets the formatting of rotation values',
#		items = [
#			('RAD', 'Radians', 'Output rotation in radians'),
#			('DEG', 'Degrees', 'Output rotation in degrees')
#			],
#		default = 'RAD')

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
			show_csv = False
			object_count = 0
			
			# Update variables based on object selection status
			if bpy.context.object and bpy.context.object.select_get():
				# Count any items for CSV, count only meshes for everything else
				if context.scene.vf_delivery_settings.file_type == "CSV":
					object_count = len(bpy.context.selected_objects)
				else:
					object_count = len([obj for obj in bpy.context.selected_objects if obj.type in VF_delivery_object_types])
				
				# Button icon
				button_icon = "OUTLINER_OB_MESH"
				
				# Button title
				if (object_count > 1 and context.scene.vf_delivery_settings.file_grouping == "COMBINED" and not context.scene.vf_delivery_settings.file_type == "CSV"):
					button_title = bpy.context.active_object.name + file_format
				elif object_count == 1:
					if bpy.context.active_object.type not in VF_delivery_object_types and context.scene.vf_delivery_settings.file_grouping == "INDIVIDUAL":
						for obj in bpy.context.selected_objects:
							if obj.type in VF_delivery_object_types:
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
					object_count = len([obj for obj in bpy.context.collection.all_objects if obj.type in VF_delivery_object_types])
				
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
				if context.scene.vf_delivery_settings.file_type == "CSV":
					button_title = "Select object"
				else:
					button_title = "Select mesh"
					
			# Specific display cases
			if context.scene.vf_delivery_settings.file_type == "CSV":
				show_group = False
				show_csv = True
				
			# UI Layout
			layout = self.layout
			layout.use_property_decorate = False # No animation
			
			layout.prop(context.scene.vf_delivery_settings, 'file_location', text = '')
			layout.prop(context.scene.vf_delivery_settings, 'file_type', text = '')
			
			if show_group:
				layout.prop(context.scene.vf_delivery_settings, 'file_grouping', expand = True)
				
			if show_csv:
				layout.prop(context.scene.vf_delivery_settings, 'csv_position', expand = True)
				
			if button_enable:
				layout.operator(VFDELIVERY_OT_file.bl_idname, text = button_title, icon = button_icon)
			else:
				disabled = layout.row()
				disabled.active = False
				disabled.enabled = False
				disabled.operator(VFDELIVERY_OT_file.bl_idname, text = button_title, icon = button_icon)
				
		except Exception as exc:
			print(str(exc) + " | Error in VF Delivery panel")
			
classes = (VFDELIVERY_OT_file, vfDeliverySettings, VFTOOLS_PT_delivery)

###########################################################################
# Addon registration functions

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Scene.vf_delivery_settings = bpy.props.PointerProperty(type = vfDeliverySettings)
	
def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.vf_delivery_settings
	
if __name__ == "__main__":
	register()