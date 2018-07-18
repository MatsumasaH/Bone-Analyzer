# ターゲットが外部オブジェクトの場合バグるので修正/修正済み
# 大きさが小さいボーンを探す
# Chiled == 0 and Being Targeted == 0 のボーンを探す

import bpy
from bpy.props import *
import bmesh
import mathutils

# ここも、不完全なので、あとで直す
# サイトにまとめたりする
bl_info = {
    "name": "Bone Analyzer",
    "category": "3D View",
    "description": "Set short cut key for in like Q"
}

# Enumを返す。動的ではないが、その場で作る
def type_call_back(self, context):
    type = ["CAMERA_SOLVER", "FOLLOW_TRACK", "OBJECT_SOLVER", "COPY_LOCATION", "COPY_ROTATION", "COPY_SCALE",
            "COPY_TRANSFORMS", "LIMIT_DISTANCE", "LIMIT_LOCATION", "LIMIT_ROTATION", "LIMIT_SCALE", "MAINTAIN_VOLUME",
            "TRANSFORM", "CLAMP_TO", "DAMPED_TRACK", "IK", "LOCKED_TRACK", "SPLINE_IK", "STRETCH_TO", "TRACK_TO",
            "ACTION", "CHILD_OF", "FLOOR", "FOLLOW_PATH", "PIVOT", "RIGID_BODY_JOINT", "SHRINKWRAP"]
    items = []
    counter = 1
    for i in type:
        # identifier, name, description, number
        u = (i, i, "", counter)
        counter += 1
        items.append(u)
    return items

class BoneAnalyzer(bpy.types.Operator):
    """Analyze Bone"""  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.bone_analyzer"  # unique identifier for buttons and menu items to reference.
    bl_label = "Analyze Bone"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    # Options after excuted the tool
    # you can add by making class instance or by excuting class or something
    my_c = bpy.props.BoolProperty(name="Child")
    my_p = bpy.props.BoolProperty(name="Parent")
    my_tt = bpy.props.BoolProperty(name="Targeting to")
    my_bt = bpy.props.BoolProperty(name="Being Targeted")
    my_db = bpy.props.BoolProperty(name="Deformation Bones")
    my_dtb = bpy.props.BoolProperty(name="Constraint Bones")
    my_enum = bpy.props.EnumProperty(items=type_call_back, name="Constraint")

    @classmethod
    def poll(cls, context):
        return bpy.context.selected_pose_bones is not None

    def execute(self, context):  # execute() is called by blender when running the operator.

        print("Starting Script...")

        analyze_bone(self)

        # trigger viewport update---------------------------------------------------------
        bpy.context.scene.objects.active = bpy.context.scene.objects.active
        # --------------------------------------------------------------------------------

        print("End of Script...")

        return {'FINISHED'}  # this lets blender know the operator finished successfully.


def analyze_bone(self):
    if self.my_c is True:
        select_child()
    if self.my_p is True:
        select_parent()
    if self.my_tt is True:
        select_targeting_bones(self)
    if self.my_bt is True:
        select_bones_targeting_self()
    if self.my_db is True:
        select_def_bones()
    if self.my_dtb is True:
        select_constraint_bone(self)


def to_edit_mode(name):
    # オブジェクトモードへ移動
    bpy.ops.object.mode_set(mode='OBJECT')
    # 自身以外を非選択にし自身を選択
    for element in bpy.context.selected_objects:
        element.select = False
    bpy.context.scene.objects.active = bpy.data.objects[name]
    bpy.data.objects[name].select = True
    # その後EDITモードへ
    bpy.ops.object.mode_set(mode='EDIT')


bone_dict = {}


# ディクショナリーオブジェクトを作成
# key   : bone name
# value : driver information
def driver(t_bone_dict):
    for bone in bpy.context.object.pose.bones:
        found_drivers = []
        if hasattr(bpy.context.object.animation_data, "drivers") is not False:
            for d in bpy.context.object.animation_data.drivers:
                # pose.bones["Bone.002"].scale
                if ('"%s"' % bone.name) in d.data_path:
                    found_drivers.append(d)

            if found_drivers:
                t_bone_dict[bone.name] = found_drivers


def driver_targets(input_pose_bone):
    # return value
    targets = []
    # bone name
    bone_name = input_pose_bone
    if bone_name in bone_dict.keys():
        # Driver Array
        active_bone_drivers = bone_dict[bone_name]
        for d in active_bone_drivers:
            # Driver
            for var in d.driver.variables:
                # Variables
                for target in var.targets:
                    # Target
                    if target.data_path != "":
                        # pose.bones["Bone.002"].scale
                        # pose.bones["thigh.fk.R"]["stretch_length"]
                        print(target.data_path.split('"')[1])
                        targets.append(target.data_path.split('"')[1])
    return targets


def find_bones_targeting_to():
    driver(bone_dict)
    for bone in bpy.context.object.data.bones:
        for target in driver_targets(bone.name):
            if target == bpy.context.active_bone.name:
                bone.select = True


def select_driver_target():
    driver(bone_dict)
    for target in driver_targets(bpy.context.active_bone.name):
        bpy.context.object.data.bones[target].select = True


def select_parent():
    if bpy.context.active_pose_bone.parent is not None:
        name = bpy.context.active_pose_bone.parent.name
        bpy.context.object.data.bones[name].select = True


def select_child():
    sname = bpy.context.active_pose_bone
    for bone in bpy.context.object.pose.bones:
        if bone.parent is not None:
            if bone.parent.name == sname.name:
                print(bone.parent)
                bpy.context.object.data.bones[bone.name].select = True


def select_bones_targeting_self():
    count = 0
    find_bones_targeting_to()
    bonename = bpy.context.active_pose_bone.name;
    bonelist = []
    for bone in bpy.context.object.pose.bones:
        for constraint in bone.constraints:
            if hasattr(constraint, 'subtarget'):
                if constraint.subtarget == bonename:
                    bonelist.append(bone)
    for bone in bonelist:
        print(bone.name)
        bpy.context.object.data.bones[bone.name].select = True
        count += 1
    return count


def select_targeting_bones(self):
    select_driver_target()
    bonename = bpy.context.active_pose_bone.name
    bonelist = []
    objectlist = []
    for constraint in bpy.context.active_pose_bone.constraints:
        if hasattr(constraint, 'subtarget'):
            bonelist.append(constraint.subtarget)
            objectlist.append(constraint.target)
    for bone, object in zip(bonelist, objectlist):
        print(bone)
        # ここで、もし対象が外部の場合バグるので、まず、ディクショナリーにキーが存在するかどうかを問い合わせ
        # 存在する場合だけ実行。そうでなければ無視
        # ではなくエラーメッセージ
        if bone in bpy.context.object.data.bones:
            bpy.context.object.data.bones[bone].select = True
        else:
            if bone == "":
                self.report({'INFO'}, "The target was outside of the bone structure. <%s>" % object.name)
            else:
                self.report({'INFO'}, "The target was outside of the bone structure. <%s/%s>" % (object.name, bone))


# ここで、Deformationに関するBone、つまり
# Vertex Groupが存在するものを選択する
# と思ったけど、ちょっと難しい？
# すべてのオブジェクトをチェックして、
def select_def_bones():
    # まずオブジェクトを探し
    main_ob = None
    for ob in bpy.data.objects:
        for mod in ob.modifiers:
            if hasattr(mod, "object"):
                if mod.object == bpy.context.object:
                    main_ob = ob

    if main_ob is not None:
        array = {}
        for vg in main_ob.vertex_groups:
                array[str(vg.index)] = vg.name

        array_2 = {}
        # bpy.context.object.data.vertices[20000].groups[0].weight
        for v in main_ob.data.vertices:
            for g in v.groups:
                if g.weight != 0.0:
                    array_2[g.group] = True

        array_3 = []
        for key in array_2.keys():
            array_3.append(array[str(key)])

        for bone in bpy.context.object.pose.bones:
            if array_3.count(bone.name) != 0:
                bpy.context.object.data.bones[bone.name].select = True


# ここで、Damped Trackがついているものを選択する
# いや、ここで、色々な種類のコンストレイントを選べるようにする
# enum型を使う感じで
def select_constraint_bone(self):
    print(self.my_enum)
    for bone in bpy.context.object.pose.bones:
        for con in bone.constraints:
            if con.type == self.my_enum:
                bpy.context.object.data.bones[bone.name].select = True

def menu_draw(self, context):
    self.layout.operator("object.bone_analyzer")


def register():
    bpy.utils.register_class(BoneAnalyzer)
    bpy.types.VIEW3D_MT_pose_specials.append(menu_draw)


def unregister():
    bpy.utils.unregister_class(BoneAnalyzer)
    bpy.types.VIEW3D_MT_pose_specials.remove(menu_draw)


register()
if __name__ == "__main__":
    register()

