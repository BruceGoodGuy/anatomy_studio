"""Trích mesh cơ + xương thân trên (vai, cánh tay, cẳng tay, bàn tay — bên phải; lồng ngực hai bên)
từ FBX của Z-Anatomy. Chạy bằng Python có `bpy` (Blender dạng thư viện, cần Python 3.11):
    python tools/extract_zanatomy_upper.py MuscularSystem100.fbx SkeletalSystem100.fbx --out assets/zanat_upper.npz
rồi:  python -m pipeline.zbind_upper
"""
import argparse

import bpy
import numpy as np

MUSCLES = [
    "Clavicular part of deltoid muscle", "Acromial part of deltoid muscle", "Scapular spinal part of deltoid muscle",
    "Supraspinatus muscle", "Infraspinatus muscle", "Subscapularis muscle", "Teres minor muscle", "Teres major muscle",
    "Clavicular head of pectoralis major muscle", "Sternocostal head of pectoralis major muscle",
    "(Abdominal part of pectoralis major muscle)", "Latissimus dorsi muscle", "Coracobrachialis muscle",
    "Long head of triceps brachii", "Lateral head of triceps brachii", "Medial head of triceps brachii", "Anconeus muscle",
    "Long head of biceps brachii", "Short head of biceps brachii", "Brachialis muscle", "Brachioradialis muscle",
    "Supinator", "Superficial head of pronator teres", "Deep head of pronator teres", "Pronator quadratus",
    "Extensor carpi radialis longus", "Extensor carpi radialis brevis", "Humeral head of extensor carpi ulnaris",
    "Ulnar head of extensor carpi ulnaris", "Flexor carpi radialis", "Humeral head of flexor carpi ulnaris",
    "Ulnar head of flexor carpi ulnaris", "Palmaris longus muscle", "Humero-ulnar head of flexor digitorum superficialis",
    "Radial head of flexor digitorum superficialis", "Flexor digitorum profundus", "Extensor digitorum",
]
ORD = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth"]
THORAX = ([f"{o} rib.{s}" for o in ORD for s in "rl"] +
          [f"Costal cartilage of {o.lower()} rib.{s}" for o in ORD[:10] for s in "rl"] +
          ["Manubrium of sternum", "Body of sternum", "Xiphoid process"])
SHOULDER = ["Scapula.r", "Clavicle.r", "Scapula.l", "Clavicle.l"]
ARM = ["Humerus.r", "Ulna.r", "Radius.r"]
HAND = ["Scaphoid bone.r", "Lunate bone.r", "Triquetrum bone.r", "Pisiform bone.r", "Trapezium bone.r", "Trapezoid bone.r",
        "Capitate bone.r", "Hamate bone.r"] + \
       [f"{o} metacarpal bone.r" for o in ORD[:5]] + \
       [f"{k} phalanx of {f} finger of hand.r" for f in ["first", "second", "third", "fourth", "fifth"]
        for k in ["Proximal", "Middle", "Distal"]]


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
    out, missing = {}, []
    objs = load(args.muscles_fbx)
    for name in MUSCLES:
        if name + ".r" not in objs:
            missing.append(name)
            continue
        out[f"m:{name}:v"], out[f"m:{name}:f"] = mesh_arrays(objs[name + ".r"])
    objs = load(args.skeleton_fbx)
    for name in THORAX + SHOULDER + ARM + HAND:
        if name not in objs:
            missing.append(name)
            continue
        out[f"b:{name}:v"], out[f"b:{name}:f"] = mesh_arrays(objs[name])
    np.savez_compressed(args.out, **out)
    print(f"OK -> {args.out}; thiếu: {missing}")


if __name__ == "__main__":
    main()
