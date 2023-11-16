bl_info = {
	"name": "VF Delivery",
	"author": "John Einselen - Vectorform LLC",
	"version": (0, 12, 2),
	"blender": (3, 3, 1),
	"location": "Scene > VF Tools > Delivery",
	"description": "Quickly export selected objects to a specified directory",
	"warning": "inexperienced developer, use at your own risk",
	"doc_url": "https://github.com/jeinselen/VF-BlenderDelivery",
	"tracker_url": "https://github.com/jeinselen/VF-BlenderDelivery/issues",
	"category": "3D View"}

import bpy
from bpy.app.handlers import persistent
import mathutils
import struct
import numpy as np
import os

# With help from:
# https://stackoverflow.com/questions/54464682/best-way-to-undo-previous-steps-in-a-series-of-steps
# https://stackoverflow.com/questions/37335653/unable-to-completely-deselect-all-objects-in-blender-using-scripting-or-key-a
# https://blender.stackexchange.com/questions/200341/apply-modifiers-in-all-objects-at-once
# https://github.com/CheeryLee/blender_apply_modifiers/blob/master/apply_modifiers.py
# https://blender.stackexchange.com/a/146573/123159

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
	
	def remap(self, val, start, stop):
		val = (val - start) / (stop - start)
		return val
	
	def execute(self, context):
		# Set up local variables
		location = bpy.path.abspath(bpy.context.scene.vf_delivery_settings.file_location)
		format = bpy.context.scene.vf_delivery_settings.file_type
		file_format = "." + format.lower().split("-")[0] # Get only the characters before a dash to support multiple variations of a single format
		combined = True if bpy.context.scene.vf_delivery_settings.file_grouping == "COMBINED" else False
		active_object = bpy.context.active_object
		
		# Create directory if it doesn't exist yet
		if not os.path.exists(location):
			os.makedirs(location)
		
		# Save then override the current mode to OBJECT
		if active_object is not None:
			object_mode = active_object.mode
			bpy.ops.object.mode_set(mode = 'OBJECT')
				
		# Check if at least one object is selected, if not, convert selected collection into object selection
		if bpy.context.object and bpy.context.object.select_get():
			file_name = active_object.name
		else:
			file_name = bpy.context.collection.name
			for obj in bpy.context.collection.all_objects:
				obj.select_set(True)
				
		if format != "CSV-1":
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
		
		elif format == "VF":
			# Define the data to be saved
			fourcc = "VF_V"  # Replace with the appropriate FourCC of either 'VF_F' for value or 'VF_V' for vec3
			
			# Name of the custom attribute
			attribute_name = 'field_vector'
			
			# Get the active selected object
			obj = bpy.context.object
			
			# Ensure the selected object is a mesh with equal to or fewer than 65536 vertices and the necessary properties and attributes
			if obj and obj.type == 'MESH' and len(obj.data.vertices) <= 65536 and obj.data.get('vf_point_grid_x') is not None and obj.data.get('vf_point_grid_y') is not None and obj.data.get('vf_point_grid_z') is not None:
				# Get evaluated object
				obj = bpy.context.evaluated_depsgraph_get().objects.get(obj.name)
				
				# Check if named attribute exists
				if attribute_name in obj.data.attributes:
					# Create empty array
					array = []
					
					# For each attribute entry, collect the results
					for data in obj.data.attributes[attribute_name].data:
						# Check if the attribute includes a value
						if hasattr(data, 'value'):
							array.append(data.value)
						# Check if the attribute includes a vector
						elif hasattr(data, 'vector'):
							# Swizzle XZY order for Blender to Unity coordinate conversion
							array.append((data.vector.x, data.vector.z, data.vector.y))
						else:
							print(f"Values not found in '{attribute_name}' attribute.")
							return {'CANCELLED'}
					
					# Set array size using custom properties
					size_x = obj.data["vf_point_grid_x"]
					size_y = obj.data["vf_point_grid_z"] # Swizzle XZY order for Unity coordinate system
					size_z = obj.data["vf_point_grid_y"] # Swizzle XZY order for Unity coordinate system
					
					# Calculate the stride based on the data type
					is_float_data = fourcc[3] == 'F'
					stride = 1 if is_float_data else 3
					
					# Create a new binary file for writing
					with open(location + obj.name + file_format, 'wb') as file:
						# Write the FourCC
						file.write(struct.pack('4s', fourcc.encode('utf-8')))
						
						# Write the volume size
						file.write(struct.pack('HHH', size_x, size_y, size_z))
						
						# Write the data
						for value in array:
							if is_float_data:
								file.write(struct.pack('f', value))
							else:
								file.write(struct.pack('fff', *value))
				else:
					print(f"Selected object does not contain '{attribute_name}' values.")
					return {'CANCELLED'}
				
			else:
				print(f"Selected object is not a mesh")
				
				# Cancel processing
				return {'CANCELLED'}
		
		elif format == "PNG":
			# Name of the custom attribute
			attribute_name = 'field_vector'
			
			# Get the active selected object
			obj = bpy.context.object
			
			# Ensure the selected object is a mesh with equal to or fewer than 65536 vertices and the necessary properties and attributes
			# The actual limit for 3D textures in Unity is 2048 x 2048 x 2048 = 8,589,934,592
			# However...that would result in an image over 4 million pixels wide, and I just don't want to deal with the ramifications of that right now
			if obj and obj.type == 'MESH' and len(obj.data.vertices) <= 65536 and obj.data.get('vf_point_grid_x') is not None and obj.data.get('vf_point_grid_y') is not None and obj.data.get('vf_point_grid_z') is not None:
				# Get evaluated object
				obj = bpy.context.evaluated_depsgraph_get().objects.get(obj.name)
				
				# Check if named attribute exists
				if attribute_name in obj.data.attributes:
					# Get remapping values
					start = context.scene.vf_delivery_settings.data_range[0]
					stop = context.scene.vf_delivery_settings.data_range[1]
					
					# Create empty array
					array = []
					
					# For each attribute entry, collect the results
					for data in obj.data.attributes[attribute_name].data:
						# Check if the attribute includes a value
						if hasattr(data, 'value'):
							# Instead of nested arrays, just create a flat list of values
							val = self.remap(data.value, start, stop)
							array.append(val)
							array.append(val)
							array.append(val)
							array.append(1.0)
						# Check if the attribute includes a vector
						elif hasattr(data, 'vector'):
							# Instead of nested arrays, just create a flat list of values
							array.append(self.remap(data.vector.x, start, stop))
							# Swizzle ZY order for Blender to Unity coordinate conversion
							array.append(self.remap(data.vector.z, start, stop))
							array.append(self.remap(data.vector.y, start, stop))
							array.append(1.0)
						else:
							print(f"Values not found in '{attribute_name}' attribute.")
							return {'CANCELLED'}
					
					# Get output sizes using custom properties
					grid_x = obj.data["vf_point_grid_x"]
					grid_y = obj.data["vf_point_grid_y"]
					grid_z = obj.data["vf_point_grid_z"]
					
					# Swizzle ZY order for Unity coordinate system
					image_width = grid_x * grid_y
					image_height = grid_z
					
					# Create image
					image = bpy.data.images.new("3DtextureOutput", width=image_width, height=image_height, alpha=False, float_buffer=True, is_data=True)
					
					# Image content
					# Swizzle ZY order for Unity coordinate system
					array = np.array(array).reshape((grid_x, grid_z, grid_y, 4))
					array = np.rot90(array, axes=(0, 1))
					image.pixels = array.flatten()
					
					# Save PNG
					image.filepath_raw = location + obj.name + file_format
					image.file_format = 'PNG'
					image.save()
				else:
					print(f"Selected object does not contain '{attribute_name}' values.")
					return {'CANCELLED'}
			else:
				print(f"Selected object is not a mesh")
				return {'CANCELLED'}
		
		elif format == "CSV-1":
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
		
		elif format == "CSV-2":
			for obj in bpy.context.selected_objects:
				# Get evaluated object
				obj = bpy.context.evaluated_depsgraph_get().objects.get(obj.name)
				
				# Collect data with temporary mesh conversion
				array = [["x","y","z"]]
				for v in obj.to_mesh().vertices:
					array.append([v.co.x, v.co.y, v.co.z])
				
				# Remove temporary mesh conversion
				obj.to_mesh_clear()
				
				# Save out CSV file
				np.savetxt(
					location + obj.name + file_format,
					array,
					delimiter = ",",
					newline = '\n',
					fmt = '% s'
					)
		
		if format != "CSV-1":
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
			('FBX', 'FBX — Unity 3D', 'Export FBX binary file for Unity 3D'),
			('GLB', 'GLB — ThreeJS', 'Export GLTF compressed binary file for ThreeJS'),
			('OBJ', 'OBJ — Element3D', 'Export OBJ file for VideoCopilot Element 3D'),
			('USDZ', 'USDZ — Xcode', 'Export USDZ file for Apple platforms including Xcode'),
			(None),
			('STL', 'STL — 3D Printing', 'Export individual STL file of each selected object for 3D printing'),
			(None),
			('VF', 'VF — Unity 3D Volume Field', 'Export volume field for Unity 3D'),
			('PNG', 'PNG — 3D Texture Strip', 'Export volume field as a PNG image strip for Godot, Unity 3D, or Unreal Engine'),
			(None),
			('CSV-1', 'CSV — Item Position', 'Export CSV file of the selected object\'s position for all frames within the render range'),
			('CSV-2', 'CSV — Point Position', 'Export CSV file of the selected object\'s points in object space')
			],
		default = 'FBX')
	file_location: bpy.props.StringProperty(
		name = "Delivery Location",
		description = "Delivery location for all exported files",
		default = "//",
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
	data_range: bpy.props.FloatVectorProperty(
		name='Range',
		description='Range of data to be normalised within 0-1 image values',
		size=2,
		default=(-1.0, 1.0),
		step=1,
		precision=2,
		soft_min=-1.0,
		soft_max= 1.0,
		min=-1000.0,
		max= 1000.0)
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
			file_format = "." + context.scene.vf_delivery_settings.file_type.lower().split("-")[0] # Get only the characters before a dash to support multiple variations of a single format
			button_enable = True
			button_icon = "FILE"
			button_title = ''
			info_box = ''
			show_group = True
			show_range = False
			show_csv = False
			object_count = 0
			
			# Check if at least one object is selected
			if bpy.context.object and bpy.context.object.select_get():
				# Volume Field: count only an active mesh with the necessary data elements
				# Does not check for named attributes, however, since that requires applying all modifiers
				if context.scene.vf_delivery_settings.file_type == "VF" or context.scene.vf_delivery_settings.file_type == "PNG":
					obj = bpy.context.object
					# Validate object data (doesn't check if the geometry nodes modifier actually includes a named attribute)
					if obj.type == 'MESH' and len(obj.data.vertices) <= 65536 and obj.data.get('vf_point_grid_x') is not None and obj.data.get('vf_point_grid_y') is not None and obj.data.get('vf_point_grid_z') is not None and ('field_vector' in obj.data.attributes or 'NODES' in [modifier.type for modifier in obj.modifiers]):
						object_count = 1
#						info_box = 'Volume export requires,"field_vector" attribute in,Geometry Node modifier'
						if context.scene.vf_delivery_settings.file_type == "PNG":
							info_box = 'Columns: ' + str(obj.data["vf_point_grid_y"])
					else:
						info_box = 'Volume export requires:,mesh with <=65536 points,"vf_point_grid..." properties,"field_vector" attribute'
				# CSV: count any items
				elif context.scene.vf_delivery_settings.file_type == "CSV-1":
					object_count = len(bpy.context.selected_objects)
				# Geometry: count only supported meshes and curves that are not hidden
				else:
					object_count = len([obj for obj in bpy.context.selected_objects if obj.type in VF_delivery_object_types])
				
				# Button title
				if (object_count > 1 and context.scene.vf_delivery_settings.file_grouping == "COMBINED" and not (context.scene.vf_delivery_settings.file_type == "CSV-1" or context.scene.vf_delivery_settings.file_type == "CSV-2")):
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
				
				# Button icon
				button_icon = "OUTLINER_OB_MESH"
			
			# Active collection fallback (except for Volume Field)
			elif not (context.scene.vf_delivery_settings.file_type == "VF" or context.scene.vf_delivery_settings.file_type == "PNG"):
				# Volume Field: requires an active mesh object, collections are not supported
				# CSV-1: count any items within the collection
				if context.scene.vf_delivery_settings.file_type == "CSV-1":
					object_count = len(bpy.context.collection.all_objects)
				# Geometry: count only supported data types (mesh, curve, etcetera) for everything else
				else:
					object_count = len([obj for obj in bpy.context.collection.all_objects if obj.type in VF_delivery_object_types])
				
				# Button title
				if context.scene.vf_delivery_settings.file_grouping == "COMBINED" and not (context.scene.vf_delivery_settings.file_type == "CSV-1" or context.scene.vf_delivery_settings.file_type == "CSV-2"):
					button_title = bpy.context.collection.name + file_format
				else:
					button_title = str(object_count) + " files"
				
				# Button icon
				button_icon = "OUTLINER_COLLECTION"
			
			# If no usable items (CSV-1) or meshes (everything else) are found, disable the button
			# Keeping the message generic allows this to be used universally
			if object_count == 0:
				button_enable = False
				button_icon = "X"
				if context.scene.vf_delivery_settings.file_type == "CSV-1":
					button_title = "Select item"
				else:
					button_title = "Select mesh"
			
			# Specific display cases
			if context.scene.vf_delivery_settings.file_type == "VF" or context.scene.vf_delivery_settings.file_type == "PNG":
				show_group = False
				show_csv = False
			
			if context.scene.vf_delivery_settings.file_type == "PNG":
				show_range = True
			
			if context.scene.vf_delivery_settings.file_type == "CSV-1":
				show_group = False
				show_csv = True
			
			if context.scene.vf_delivery_settings.file_type == "CSV-2":
				show_group = False
				show_csv = False
			
			# UI Layout
			layout = self.layout
			layout.use_property_decorate = False # No animation
			
			layout.prop(context.scene.vf_delivery_settings, 'file_location', text = '')
			layout.prop(context.scene.vf_delivery_settings, 'file_type', text = '')
			
			if show_group:
				layout.prop(context.scene.vf_delivery_settings, 'file_grouping', expand = True)
			
			if show_range:
				layout.prop(context.scene.vf_delivery_settings, 'data_range')
			
			if show_csv:
				layout.prop(context.scene.vf_delivery_settings, 'csv_position', expand = True)
			
			if button_enable:
				layout.operator(VFDELIVERY_OT_file.bl_idname, text = button_title, icon = button_icon)
			else:
				disabled = layout.row()
				disabled.active = False
				disabled.enabled = False
				disabled.operator(VFDELIVERY_OT_file.bl_idname, text = button_title, icon = button_icon)
			
			if info_box:
				box = layout.box()
				col = box.column(align=True)
				for line in info_box.split(','):
					col.label(text=line)
			
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
	