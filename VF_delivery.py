bl_info = {
	"name": "VF Delivery",
	"author": "John Einselen - Vectorform LLC",
	"version": (0, 2),
	"blender": (2, 80, 0),
	"location": "Scene > VF Tools > Delivery",
	"description": "Quickly export selected objects to a specified directory",
	"warning": "inexperienced developer, use at your own risk",
	"wiki_url": "",
	"tracker_url": "",
	"category": "3D View"}

import bpy
from bpy.app.handlers import persistent
import mathutils

###########################################################################
# Main class

class VFDELIVERY_OT_fbx(bpy.types.Operator):
	bl_idname = "vfdelivery.fbx"
	bl_label = "Deliver FBX"
	bl_description = "Quickly export selected objects or collection to a specified directory"
#	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
#		self.report({'INFO'}, f"This is {self.bl_idname}")

		if not bpy.context.view_layer.objects.active.data.vertices:
			return {'CANCELLED'}

		# Set up local variables
		location = bpy.context.scene.vf_delivery_settings.file_location

		# Save current mode
		mode = bpy.context.active_object.mode

		# Override mode to OBJECT
		bpy.ops.object.mode_set(mode='OBJECT')

		# Check if an object is selected, if not, export collection instead
		if bpy.context.object.select_get():
			object_toggle = True
			collection_toggle = False
			file_name = bpy.context.active_object.name
		else:
			object_toggle = False
			collection_toggle = True
			file_name = bpy.context.collection.name

		bpy.ops.export_scene.fbx(
			filepath=location + file_name + ".fbx",
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

		# Reset to original mode
		bpy.ops.object.mode_set(mode=mode)

		# Done
		return {'FINISHED'}

class VFDELIVERY_OT_glb(bpy.types.Operator):
	bl_idname = "vfdelivery.glb"
	bl_label = "Deliver GLB"
	bl_description = "Quickly export selected objects or collection to a specified directory"
#	bl_options = {'REGISTER', 'UNDO'}
	
	def execute(self, context):
#		self.report({'INFO'}, f"This is {self.bl_idname}")

		if not bpy.context.view_layer.objects.active.data.vertices:
			return {'CANCELLED'}

		# Set up local variables
		location = bpy.context.scene.vf_delivery_settings.file_location

		# Save current mode
		mode = bpy.context.active_object.mode

		# Override mode to OBJECT
		bpy.ops.object.mode_set(mode='OBJECT')

		# Check if an object is selected, if not, export collection instead
		if bpy.context.object.select_get():
			object_toggle = True
			collection_toggle = False
			file_name = bpy.context.active_object.name
		else:
			object_toggle = False
			collection_toggle = True
			file_name = bpy.context.collection.name

		bpy.ops.export_scene.gltf(
			filepath=location + file_name + ".glb",
			check_existing=False, # Always overwrite existing files (dangerous...designed specifically for ThreeJS delivery!)
			export_format='GLB',
#			ui_tab='GENERAL',
#			export_copyright='',

			export_image_format='JPEG',
#			export_texture_dir='',
#			export_keep_originals=False,
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
			export_apply=False,

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
			export_displacement=False,
			will_save_settings=False,
			filter_glob='*.glb;*.gltf')

		# Reset to original mode
		bpy.ops.object.mode_set(mode=mode)
		
		# Done
		return {'FINISHED'}

class VFDELIVERY_OT_file(bpy.types.Operator):
	bl_idname = "vfdelivery.file"
	bl_label = "Deliver File"
	bl_description = "Quickly export selected objects or collection to a specified directory"
#	bl_options = {'REGISTER', 'UNDO'}
	
	def execute(self, context):
#		self.report({'INFO'}, f"This is {self.bl_idname}")
		
		if not bpy.context.view_layer.objects.active.data.vertices:
			return {'CANCELLED'}
		
		# Set up local variables
		location = bpy.context.scene.vf_delivery_settings.file_location
		format = bpy.context.scene.vf_delivery_settings.file_type
		
		# Save current mode
		mode = bpy.context.active_object.mode
		
		# Override mode to OBJECT
		bpy.ops.object.mode_set(mode='OBJECT')
		
		# Check if an object is selected, if not, export collection instead
		if bpy.context.object.select_get():
			object_toggle = True
			collection_toggle = False
			file_name = bpy.context.active_object.name
		else:
			object_toggle = False
			collection_toggle = True
			file_name = bpy.context.collection.name

		file_format = "." + format.lower()

		if format == "FBX":
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
		elif format == "GLB":
			bpy.ops.export_scene.gltf(
				filepath=location + file_name + file_format,
				check_existing=False, # Always overwrite existing files (dangerous...designed specifically for ThreeJS delivery!)
				export_format='GLB',
	#			ui_tab='GENERAL',
	#			export_copyright='',
				
				export_image_format='JPEG',
	#			export_texture_dir='',
	#			export_keep_originals=False,
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
				export_displacement=False,
				will_save_settings=False,
				filter_glob='*.glb;*.gltf')
		elif format == "GLB":
			print("STL not implemented yet")

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
			('FBX', 'Unity FBX', 'Export FBX binary file for Unity'),
			('GLB', 'ThreeJS GLB', 'Export GLTF compressed binary file for ThreeJS'),
			('STL', 'Printing STL', 'Export individual STL file of each selected object for 3D printing')
			],
		default='FBX')
	file_location: bpy.props.StringProperty(
		name="Delivery Location",
		description="Delivery location for all exported files",
		default="/",
		maxlen=4096,
		subtype="DIR_PATH")

class VFTOOLS_PT_delivery(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'VF Tools'
	bl_order = 0
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
			layout = self.layout
			layout.use_property_decorate = False # No animation
#			layout.prop(context.scene.vf_delivery_settings, 'file_type')
			layout.prop(context.scene.vf_delivery_settings, 'file_location', text='')

			file_format = "." + context.scene.vf_delivery_settings.file_type.lower()
			file_icon="FILE"

			if bpy.context.object.select_get():
				file_name = bpy.context.active_object.name + file_format
				file_icon = "OUTLINER_OB_MESH"
			else:
				file_name = bpy.context.collection.name + file_format
				file_icon = "OUTLINER_COLLECTION"

			split = layout.split(factor=0.25, align=True)
			col = split.column()
			col.label(text="Pipeline:")
			col.label(text="Export:")

			col = split.column()
			col.prop(context.scene.vf_delivery_settings, 'file_type', text='')
			col.operator(VFDELIVERY_OT_file.bl_idname, text=file_name, icon=file_icon)

#			if context.scene.vf_delivery_settings.file_type == "FBX":
#				col.operator(VFDELIVERY_OT_fbx.bl_idname, text=file_name, icon=file_icon)
#			elif context.scene.vf_delivery_settings.file_type == "GLB":
#				col.operator(VFDELIVERY_OT_glb.bl_idname, text=file_name, icon=file_icon)
#			elif context.scene.vf_delivery_settings.file_type == "STL":
#				col.operator(VFDELIVERY_OT_file.bl_idname, text=file_name, icon=file_icon)
		
		except Exception as exc:
			print(str(exc) + " | Error in VF Delivery panel")

classes = (VFDELIVERY_OT_fbx, VFDELIVERY_OT_glb, VFDELIVERY_OT_file, vfDeliverySettings, VFTOOLS_PT_delivery)

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
	