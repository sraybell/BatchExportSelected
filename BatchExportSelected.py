import bpy  # pylint: disable=import-error
import os


bl_info = {
    'name': 'Batch Export', # change name to match new feature(s)
    'author': 'Steven Raybell',
    'description': 'Provides batched and merged export operations for OBJ and STL.',
    'version': (0, 5, 2),
    'blender': (3, 4, 0),
    'location': 'File > Export',
    'category': 'Import-Export'
}


PROPS = [
    ('as_batch_chk', bpy.props.BoolProperty(
        name='As Batch', default=True,
        description='Batch or merge all objects for export.')),
    ('as_collection', bpy.props.BoolProperty(
        name='As Collection', default=False,
        description='Use the selected object''s collection for export')),
    ('export_normals_chk', bpy.props.BoolProperty(
        name='Include Normals (OBJ)', default=False,
        description='Write normal vector information for the mesh')),
    ('export_uvs_chk', bpy.props.BoolProperty(
        name='Include UVs (OBJ)', default=False,
        description='Writes UVs for the mesh')),
    ('export_materials_chk', bpy.props.BoolProperty(name='Export Materials (OBJ)',
     default=False, description='Exports an associated .mtl')),
    ('apply_modifiers_chk', bpy.props.BoolProperty(name='Apply Modifiers (OBJ, STL)',
     default=True, description='Whether to apply the viewport modifiers on export')),
    ('export_dir', bpy.props.StringProperty(name='',
     default='exports', description='The sub directory to write the files to.'))
]


def check_export(self, context, output_dir):
    blend_file = context.blend_data
    if blend_file.is_saved is False:
        self.report({'ERROR'}, 'The file has not been saved. ' +
                    'Unable to determine where to export files!')
        return False, ''
    else:
        basedir = bpy.path.abspath(f'//{output_dir}\\')
        os.makedirs(basedir, exist_ok=True)

        return True, basedir


def batch_export_stl(self, context):
    (result, basedir) = check_export(self, context, context.scene.export_dir)
    if result is False:
        return

    if context.scene.as_batch_chk:
        bpy.ops.export_mesh.stl(
            filepath=basedir,
            check_existing=False,
            use_selection=True,
            use_mesh_modifiers=context.scene.apply_modifiers_chk,
            batch_mode='OBJECT',
            axis_forward='Y',
            axis_up='Z'
        )

        bpy.ops.object.select_all(action='DESELECT')

        self.report({'INFO'}, f'The operation has completed! Check in: {basedir}')
        
        return

    else:
        if context.scene.as_collection:
            collection_list = []

            objs = context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')

            meshes = filter(lambda var: var.type == 'MESH', objs)
            for mesh in meshes:
                collections = mesh.users_collection
                for collection in collections:
                    if collection.name in collection_list:
                        continue
                    else:
                        collection_list.append(collection.name)
                        for obj in collection.all_objects:
                            obj.select_set(True)

            fname = collection_list[0]

        else:

            fname = bpy.path.display_name_from_filepath(bpy.context.blend_data.filepath)

        bpy.ops.export_mesh.stl(
            filepath=f'{basedir}\\{fname}.stl',
            check_existing=False,
            use_selection=True,
            use_mesh_modifiers=context.scene.apply_modifiers_chk,
            batch_mode='OFF',
            axis_forward='Y',
            axis_up='Z'
        )

        bpy.ops.object.select_all(action='DESELECT')

        self.report({'INFO'}, f'The operation has completed! Check in: {basedir}')
        
        return
    


def batch_export_obj(self, context):
    (result, basedir) = check_export(self, context, context.scene.export_dir)
    if result is False:
        return

    # store selection
    objs = context.selected_objects

    bpy.ops.object.select_all(action='DESELECT')

    meshes = filter(lambda var: var.type == 'MESH', objs)
    for mesh in meshes:
        mesh.select_set(True)

        bpy.ops.wm.obj_export(
            filepath=os.path.join(basedir, f'{mesh.name}.obj'),
            export_selected_objects=True,
            export_materials=context.scene.export_materials_chk,
            export_uv=context.scene.export_uvs_chk,
            export_normals=context.scene.export_normals_chk,
            apply_modifiers=context.scene.apply_modifiers_chk,
            export_eval_mode='DAG_EVAL_VIEWPORT',
            forward_axis='NEGATIVE_Z'
        )
        # Deselect the object and move on to another if any more are left
        mesh.select_set(False)

    self.report({'INFO'}, f'The operation has completed! Check in: {basedir}')


class ExportSelectedAsObjOperator(bpy.types.Operator):
    '''Exports all selected objects as individual OBJ files using the object's name'''
    bl_idname = 'batchexport.exportobjs'
    bl_label = 'Batch Export Selected Objects as OBJ'
    bl_options = {'REGISTER'}

    def execute(self, context):
        batch_export_obj(self, context)
        return {'FINISHED'}


class ExportSelectedAsStlOperator(bpy.types.Operator):
    '''Exports all selected objects as individual STL files using the object's name'''
    bl_idname = 'batchexport.exportstls'
    bl_label = 'Batch Export Selected Objects as STL'
    bl_options = {'REGISTER'}

    def execute(self, context):
        batch_export_stl(self, context)
        return {'FINISHED'}


class BatchExportPanel(bpy.types.Panel):
    bl_label = 'Batch Export Tools'
    bl_idname = 'BATCHEXPORT_PT_exports_1'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_context = '.objectmode'

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):

        col = self.layout.column()
        for (prop_name, _) in PROPS:
            row = col.row()
            row.prop(context.scene, prop_name)

        row = col.row()
        row.operator(
            ExportSelectedAsStlOperator.bl_idname,
            icon_value=674,
            text='Selected as STL')

        row = col.row()
        row.operator(
            ExportSelectedAsObjOperator.bl_idname,
            icon_value=674,
            text='Selected as OBJ')


def register():
    for (prop_name, prop_value) in PROPS:
        setattr(bpy.types.Scene, prop_name, prop_value)

    bpy.utils.register_class(ExportSelectedAsObjOperator)
    bpy.utils.register_class(ExportSelectedAsStlOperator)
    bpy.utils.register_class(BatchExportPanel)


def unregister():
    for (prop_name, _) in PROPS:
        delattr(bpy.types.Scene, prop_name)

    bpy.utils.unregister_class(ExportSelectedAsObjOperator)
    bpy.utils.unregister_class(ExportSelectedAsStlOperator)
    bpy.utils.unregister_class(BatchExportPanel)


if __name__ == '__main__':
    register()
