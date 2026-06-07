import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--blend", required=True)
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data_collection in (
        bpy.data.armatures,
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.actions,
    ):
        for item in list(data_collection):
            data_collection.remove(item)


def make_material(name: str, color: tuple[float, float, float, float], roughness: float = 0.72):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness
    principled.inputs["Metallic"].default_value = 0.0
    return material


def add_edit_bone(
    armature_data,
    name: str,
    head: tuple[float, float, float],
    tail: tuple[float, float, float],
    parent=None,
    connected: bool = False,
):
    bone = armature_data.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.parent = parent
    bone.use_connect = connected and parent is not None
    return bone


def create_armature():
    data = bpy.data.armatures.new("CanonicalHumanoid")
    armature = bpy.data.objects.new("CanonicalHumanoid", data)
    bpy.context.collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    root = add_edit_bone(data, "Root", (0.0, 0.0, 0.0), (0.0, 0.0, 0.20))
    hips = add_edit_bone(data, "Hips", (0.0, 0.0, 0.92), (0.0, 0.0, 1.10), root)
    spine = add_edit_bone(data, "Spine", (0.0, 0.0, 1.10), (0.0, 0.0, 1.36), hips, True)
    chest = add_edit_bone(data, "Chest", (0.0, 0.0, 1.36), (0.0, 0.0, 1.61), spine, True)
    upper_chest = add_edit_bone(data, "UpperChest", (0.0, 0.0, 1.61), (0.0, 0.0, 1.80), chest, True)
    neck = add_edit_bone(data, "Neck", (0.0, 0.0, 1.80), (0.0, 0.0, 1.91), upper_chest, True)
    add_edit_bone(data, "Head", (0.0, 0.0, 1.91), (0.0, 0.0, 2.22), neck, True)

    left_shoulder = add_edit_bone(data, "LeftShoulder", (0.0, 0.0, 1.73), (0.22, 0.0, 1.73), upper_chest)
    left_upper_arm = add_edit_bone(data, "LeftUpperArm", (0.22, 0.0, 1.73), (0.58, 0.0, 1.62), left_shoulder, True)
    left_lower_arm = add_edit_bone(data, "LeftLowerArm", (0.58, 0.0, 1.62), (0.90, 0.0, 1.49), left_upper_arm, True)
    add_edit_bone(data, "LeftHand", (0.90, 0.0, 1.49), (1.05, 0.0, 1.43), left_lower_arm, True)

    right_shoulder = add_edit_bone(data, "RightShoulder", (0.0, 0.0, 1.73), (-0.22, 0.0, 1.73), upper_chest)
    right_upper_arm = add_edit_bone(data, "RightUpperArm", (-0.22, 0.0, 1.73), (-0.58, 0.0, 1.62), right_shoulder, True)
    right_lower_arm = add_edit_bone(data, "RightLowerArm", (-0.58, 0.0, 1.62), (-0.90, 0.0, 1.49), right_upper_arm, True)
    add_edit_bone(data, "RightHand", (-0.90, 0.0, 1.49), (-1.05, 0.0, 1.43), right_lower_arm, True)

    left_upper_leg = add_edit_bone(data, "LeftUpperLeg", (0.17, 0.0, 0.98), (0.17, 0.0, 0.54), hips)
    left_lower_leg = add_edit_bone(data, "LeftLowerLeg", (0.17, 0.0, 0.54), (0.17, 0.0, 0.13), left_upper_leg, True)
    left_foot = add_edit_bone(data, "LeftFoot", (0.17, 0.0, 0.13), (0.17, -0.22, 0.06), left_lower_leg, True)
    add_edit_bone(data, "LeftToes", (0.17, -0.22, 0.06), (0.17, -0.39, 0.06), left_foot, True)

    right_upper_leg = add_edit_bone(data, "RightUpperLeg", (-0.17, 0.0, 0.98), (-0.17, 0.0, 0.54), hips)
    right_lower_leg = add_edit_bone(data, "RightLowerLeg", (-0.17, 0.0, 0.54), (-0.17, 0.0, 0.13), right_upper_leg, True)
    right_foot = add_edit_bone(data, "RightFoot", (-0.17, 0.0, 0.13), (-0.17, -0.22, 0.06), right_lower_leg, True)
    add_edit_bone(data, "RightToes", (-0.17, -0.22, 0.06), (-0.17, -0.39, 0.06), right_foot, True)

    bpy.ops.object.mode_set(mode="OBJECT")
    armature.show_in_front = True
    armature["animation_profile_code"] = "humanoid_context_v1"
    armature["style_pack"] = "anime"
    return armature


def bind_to_bone(obj, armature, bone_name: str) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    group = obj.vertex_groups.new(name=bone_name)
    group.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new(name="CanonicalHumanoid", type="ARMATURE")
    modifier.object = armature
    obj.parent = armature
    obj["avatar_lod"] = 0
    obj["bone_binding"] = bone_name
    obj.select_set(False)


def set_material(obj, material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(material)


def create_sphere(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material,
    armature,
    bone_name: str,
    segments: int = 24,
    rings: int = 12,
):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    set_material(obj, material)
    bind_to_bone(obj, armature, bone_name)
    return obj


def create_cube(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material,
    armature,
    bone_name: str,
):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bevel = obj.modifiers.new(name="SoftEdges", type="BEVEL")
    bevel.width = min(scale) * 0.18
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    set_material(obj, material)
    bind_to_bone(obj, armature, bone_name)
    return obj


def create_cylinder_between(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    material,
    armature,
    bone_name: str,
    vertices: int = 16,
):
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    midpoint = (start_v + end_v) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=midpoint)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bevel = obj.modifiers.new(name="SoftEnds", type="BEVEL")
    bevel.width = radius * 0.35
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    set_material(obj, material)
    bind_to_bone(obj, armature, bone_name)
    return obj


def add_smile_shape(mouth) -> None:
    basis = mouth.shape_key_add(name="Basis")
    smile = mouth.shape_key_add(name="smile")
    concern = mouth.shape_key_add(name="concern")
    for index, vertex in enumerate(basis.data):
        local_x = vertex.co.x
        curve = abs(local_x) * 0.18
        smile.data[index].co.z += curve
        concern.data[index].co.z -= curve
    smile.value = 0.0
    concern.value = 0.0


def create_avatar_meshes(armature) -> None:
    skin = make_material("Skin", (0.92, 0.62, 0.48, 1.0), 0.68)
    hair = make_material("HairInk", (0.035, 0.065, 0.13, 1.0), 0.42)
    eyes = make_material("EyeInk", (0.018, 0.035, 0.07, 1.0), 0.32)
    jacket = make_material("JacketCyan", (0.05, 0.62, 0.70, 1.0), 0.72)
    shirt = make_material("ShirtWarm", (0.96, 0.88, 0.70, 1.0), 0.82)
    trousers = make_material("TrousersInk", (0.035, 0.08, 0.16, 1.0), 0.78)
    shoes = make_material("ShoesCoral", (0.92, 0.22, 0.29, 1.0), 0.62)
    mouth_material = make_material("MouthCoral", (0.78, 0.10, 0.18, 1.0), 0.52)

    create_sphere("HipsMesh", (0.0, 0.0, 1.02), (0.31, 0.20, 0.20), trousers, armature, "Hips")
    create_sphere("TorsoMesh", (0.0, 0.0, 1.48), (0.38, 0.22, 0.48), jacket, armature, "Chest")
    create_cube("ShirtPanel", (0.0, -0.225, 1.49), (0.13, 0.025, 0.29), shirt, armature, "Chest")

    create_sphere("FaceMesh", (0.0, -0.01, 2.04), (0.29, 0.25, 0.33), skin, armature, "Head")
    create_sphere("HairCap", (0.0, 0.01, 2.17), (0.32, 0.28, 0.23), hair, armature, "Head")
    create_cylinder_between("HairSideLeft", (0.23, 0.02, 2.16), (0.26, 0.03, 1.88), 0.075, hair, armature, "Head")
    create_cylinder_between("HairSideRight", (-0.23, 0.02, 2.16), (-0.26, 0.03, 1.88), 0.075, hair, armature, "Head")
    create_cylinder_between("FringeLeft", (0.08, -0.23, 2.25), (0.12, -0.27, 2.03), 0.052, hair, armature, "Head")
    create_cylinder_between("FringeRight", (-0.08, -0.23, 2.25), (-0.12, -0.27, 2.03), 0.052, hair, armature, "Head")

    create_sphere("EyeLeft", (0.105, -0.253, 2.08), (0.045, 0.018, 0.064), eyes, armature, "Head", 16, 8)
    create_sphere("EyeRight", (-0.105, -0.253, 2.08), (0.045, 0.018, 0.064), eyes, armature, "Head", 16, 8)
    create_cube("Mouth", (0.0, -0.264, 1.94), (0.075, 0.012, 0.018), mouth_material, armature, "Head")

    create_cylinder_between("UpperArmLeft", (0.25, 0.0, 1.72), (0.58, 0.0, 1.62), 0.115, jacket, armature, "LeftUpperArm")
    create_cylinder_between("LowerArmLeft", (0.58, 0.0, 1.62), (0.90, 0.0, 1.49), 0.082, skin, armature, "LeftLowerArm")
    create_sphere("HandLeft", (0.96, 0.0, 1.46), (0.105, 0.085, 0.12), skin, armature, "LeftHand", 16, 8)

    create_cylinder_between("UpperArmRight", (-0.25, 0.0, 1.72), (-0.58, 0.0, 1.62), 0.115, jacket, armature, "RightUpperArm")
    create_cylinder_between("LowerArmRight", (-0.58, 0.0, 1.62), (-0.90, 0.0, 1.49), 0.082, skin, armature, "RightLowerArm")
    create_sphere("HandRight", (-0.96, 0.0, 1.46), (0.105, 0.085, 0.12), skin, armature, "RightHand", 16, 8)

    create_cylinder_between("UpperLegLeft", (0.17, 0.0, 0.97), (0.17, 0.0, 0.55), 0.14, trousers, armature, "LeftUpperLeg")
    create_cylinder_between("LowerLegLeft", (0.17, 0.0, 0.54), (0.17, 0.0, 0.14), 0.105, skin, armature, "LeftLowerLeg")
    create_cube("FootLeft", (0.17, -0.14, 0.09), (0.16, 0.25, 0.09), shoes, armature, "LeftFoot")

    create_cylinder_between("UpperLegRight", (-0.17, 0.0, 0.97), (-0.17, 0.0, 0.55), 0.14, trousers, armature, "RightUpperLeg")
    create_cylinder_between("LowerLegRight", (-0.17, 0.0, 0.54), (-0.17, 0.0, 0.14), 0.105, skin, armature, "RightLowerLeg")
    create_cube("FootRight", (-0.17, -0.14, 0.09), (0.16, 0.25, 0.09), shoes, armature, "RightFoot")


def reset_pose(armature) -> None:
    for pose_bone in armature.pose.bones:
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)


def key_pose(armature, frame: int, rotations=None, locations=None) -> None:
    rotations = rotations or {}
    locations = locations or {}
    reset_pose(armature)
    for bone_name, rotation in rotations.items():
        armature.pose.bones[bone_name].rotation_euler = rotation
    for bone_name, location in locations.items():
        armature.pose.bones[bone_name].location = location
    for pose_bone in armature.pose.bones:
        pose_bone.keyframe_insert("rotation_euler", frame=frame, group=pose_bone.name)
        pose_bone.keyframe_insert("location", frame=frame, group=pose_bone.name)


def finish_action(action, interpolation: str = "BEZIER") -> None:
    action.use_fake_user = True
    for fcurve in action.fcurves:
        for point in fcurve.keyframe_points:
            point.interpolation = interpolation


def create_action(armature, name: str, poses, interpolation: str = "BEZIER") -> None:
    action = bpy.data.actions.new(name)
    armature.animation_data.action = action
    for frame, rotations, locations in poses:
        key_pose(armature, frame, rotations, locations)
    finish_action(action, interpolation)
    armature.animation_data.action = None


def create_animations(armature) -> None:
    armature.animation_data_create()
    create_action(
        armature,
        "idle",
        [
            (1, {"Spine": (0.0, 0.0, -0.025), "Head": (0.0, 0.0, 0.025)}, {}),
            (25, {"Spine": (0.0, 0.0, 0.025), "Head": (0.0, 0.0, -0.025)}, {"Hips": (0.0, 0.0, 0.012)}),
            (49, {"Spine": (0.0, 0.0, -0.025), "Head": (0.0, 0.0, 0.025)}, {}),
        ],
    )
    create_action(
        armature,
        "walk",
        [
            (1, {"LeftUpperLeg": (0.45, 0.0, 0.0), "RightUpperLeg": (-0.45, 0.0, 0.0), "LeftUpperArm": (-0.35, 0.0, 0.0), "RightUpperArm": (0.35, 0.0, 0.0)}, {}),
            (13, {"LeftUpperLeg": (0.0, 0.0, 0.0), "RightUpperLeg": (0.0, 0.0, 0.0)}, {"Hips": (0.0, 0.0, 0.025)}),
            (25, {"LeftUpperLeg": (-0.45, 0.0, 0.0), "RightUpperLeg": (0.45, 0.0, 0.0), "LeftUpperArm": (0.35, 0.0, 0.0), "RightUpperArm": (-0.35, 0.0, 0.0)}, {}),
            (37, {"LeftUpperLeg": (0.0, 0.0, 0.0), "RightUpperLeg": (0.0, 0.0, 0.0)}, {"Hips": (0.0, 0.0, 0.025)}),
            (49, {"LeftUpperLeg": (0.45, 0.0, 0.0), "RightUpperLeg": (-0.45, 0.0, 0.0), "LeftUpperArm": (-0.35, 0.0, 0.0), "RightUpperArm": (0.35, 0.0, 0.0)}, {}),
        ],
        "LINEAR",
    )
    sit_pose = {
        "LeftUpperLeg": (-1.18, 0.0, 0.0),
        "RightUpperLeg": (-1.18, 0.0, 0.0),
        "LeftLowerLeg": (1.22, 0.0, 0.0),
        "RightLowerLeg": (1.22, 0.0, 0.0),
        "LeftUpperArm": (-0.20, 0.0, 0.12),
        "RightUpperArm": (-0.20, 0.0, -0.12),
    }
    create_action(armature, "sit", [(1, sit_pose, {}), (49, sit_pose, {})])
    create_action(
        armature,
        "phone",
        [
            (1, {"RightUpperArm": (1.10, 0.0, -0.22), "RightLowerArm": (-1.72, 0.0, -0.12), "Head": (0.0, 0.08, -0.04)}, {}),
            (25, {"RightUpperArm": (1.16, 0.0, -0.18), "RightLowerArm": (-1.78, 0.0, -0.08), "Head": (0.0, 0.12, -0.02)}, {}),
            (49, {"RightUpperArm": (1.10, 0.0, -0.22), "RightLowerArm": (-1.72, 0.0, -0.12), "Head": (0.0, 0.08, -0.04)}, {}),
        ],
    )
    create_action(
        armature,
        "talk",
        [
            (1, {"LeftUpperArm": (0.0, -0.20, 0.28), "RightUpperArm": (0.0, 0.25, -0.32), "Head": (0.0, 0.0, -0.03)}, {}),
            (17, {"LeftUpperArm": (0.0, 0.15, 0.38), "RightUpperArm": (0.0, -0.10, -0.20), "Head": (0.0, 0.08, 0.02)}, {}),
            (33, {"LeftUpperArm": (0.0, -0.05, 0.20), "RightUpperArm": (0.0, 0.18, -0.42), "Head": (0.0, -0.06, -0.01)}, {}),
            (49, {"LeftUpperArm": (0.0, -0.20, 0.28), "RightUpperArm": (0.0, 0.25, -0.32), "Head": (0.0, 0.0, -0.03)}, {}),
        ],
    )


def export_avatar(armature, output_path: Path, blend_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.fps = 24
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 49
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.view_layer.objects.active = armature
    reset_pose(armature)
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(
        filepath=str(output_path),
        export_format="GLB",
        export_yup=True,
        export_skins=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_morph=True,
        export_morph_animation=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_extras=True,
        export_apply=False,
    )


def main() -> None:
    args = parse_args()
    clear_scene()
    armature = create_armature()
    create_avatar_meshes(armature)
    create_animations(armature)
    export_avatar(armature, Path(args.output).resolve(), Path(args.blend).resolve())
    print(f"CANONICAL_ANIME_AVATAR_EXPORTED={Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
