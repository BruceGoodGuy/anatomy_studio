"""Trích mesh cơ + xương thân dưới (bên phải) từ file FBX của Z-Anatomy.

Chỉ cần khi muốn đổi/thêm cơ Z-Anatomy. Chạy bằng Python có cài `bpy`
(Blender dạng thư viện: pip install bpy):
    python tools/extract_zanatomy.py MuscularSystem100.fbx SkeletalSystem100.fbx --out assets/zanat_lowerlimb.npz
rồi:  python -m pipeline.zbind

Kết quả là toạ độ gốc của Z-Anatomy (mét, trục Z hướng lên, bên phải cơ thể là x < 0).
"""
import argparse

import bpy
import numpy as np

# Tên mesh trong Z-Anatomy (bên phải, hậu tố .r)
MUSCLES = [
    "Gluteus maximus muscle", "Gluteus medius muscle", "Gluteus minimus muscle",
    "Tensor fasciae latae", "Piriformis muscle", "Iliacus muscle", "Psoas major",
    "Sartorius muscle", "Rectus femoris muscle", "Vastus lateralis muscle",
    "Vastus medialis muscle", "Vastus intermedius muscle",
    "Long head of biceps femoris", "Short head of biceps femoris",
    "Semimembranosus muscle", "Semitendinosus muscle",
    "Adductor magnus", "(Adductor minimus)", "Adductor longus", "Adductor brevis",
    "Gracilis muscle", "Lateral head of gastrocnemius", "Medial head of gastrocnemius",
    "Soleus muscle",
]
BONES = ["Hip bone.r", "Hip bone.l", "Sacrum", "Femur.r", "Patella.r", "Tibia.r", "Fibula.r"]


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    return {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}


def mesh_arrays(obj):
    me = obj.data
    me.calc_loop_triangles()
    mw = np.array(obj.matrix_world)
    v = np.array([vt.co[:] for vt in me.vertices], dtype=np.float64)
    v = v @ mw[:3, :3].T + mw[:3, 3]
    f = np.array([t.vertices[:] for t in me.loop_triangles], dtype=np.int32)
    return v, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("muscles_fbx")
    ap.add_argument("skeleton_fbx")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = {}
    objs = load(args.muscles_fbx)
    for name in MUSCLES:
        v, f = mesh_arrays(objs[name + ".r"])
        out[f"m:{name}:v"], out[f"m:{name}:f"] = v, f
    objs = load(args.skeleton_fbx)
    for name in BONES:
        v, f = mesh_arrays(objs[name])
        out[f"b:{name}:v"], out[f"b:{name}:f"] = v, f
    np.savez_compressed(args.out, **out)
    print(f"OK: {len(MUSCLES)} cơ, {len(BONES)} xương -> {args.out}")


if __name__ == "__main__":
    main()
