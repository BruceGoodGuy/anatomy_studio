"""Gắn mesh cơ + xương Z-Anatomy THÂN TRÊN vào mô hình — CHẠY MỘT LẦN, dùng cho mọi bài.

Giống pipeline/zbind.py (thân dưới), khác ở chỗ:
  * Xương: lồng ngực (sườn, sụn sườn, xương ức) gắn vào thân; cánh tay, xương trụ, xương quay, bàn tay
    gắn vào xương OpenSim tương ứng. Bả vai và xương đòn là hai "xương ảo" (scapula_r, clavicle_r):
    ở tư thế nghỉ trùng với thân, khi chạy thì xoay theo nhịp vai–cánh tay của MoBL-ARMS
    (pipeline/upper.py), nên delta, chóp xoay, tam đầu đầu dài… đi đúng theo bả vai khi giơ tay.
  * Màu mỗi vùng cơ lấy theo bó cơ MoBL-ARMS cùng tên (delta 3 bó, ngực lớn 3 phần, lưng xô 3 bó…).
  * TRỌNG SỐ XƯƠNG THEO ĐƯỜNG LỰC, không theo khoảng cách: ở tư thế giải phẫu tay buông sát thân, nên
    trường điều hoà theo khoảng cách (cách làm của thân dưới) gán phần dưới cơ ngực / lưng xô cho xương
    cánh tay chỉ vì chúng nằm cạnh nhau → giơ tay là cơ bị kéo phồng (đo: lật 1 428 tam giác, kéo dài
    x65). Ở đây mỗi điểm của cơ lấy xương theo vị trí của nó DỌC ĐƯỜNG CƠ MoBL-ARMS (mỗi điểm của đường
    cơ thuộc một xương: lưng xô đi dọc thân rồi mới tới xương cánh tay; nhị đầu: bả vai → chỏm và thân
    xương cánh tay → xương quay), làm mượt theo chiều dài (Gauss, LINE_SIGMA) và trên bề mặt cơ
    (LINE_SMOOTH vòng), rồi làm mượt QUA MẶT TIẾP GIÁP giữa các cơ kề nhau (cross_smooth).
    Chỉnh riêng (đã dò bằng QA): LABEL_OVERRIDE (lưng xô qua bả vai coi là bám thân; bụng đầu ngắn nhị đầu
    không theo xương quay; cơ cẳng tay phía trụ), SIGMA_OVERRIDE (tròn lớn), SOLO (tròn lớn, tròn bé không
    làm mượt chéo). Kết quả ở các động tác thử (giơ tay 170°, dang 150°, chống đẩy, curl 135°) và 14 mẫu
    thân trên: lật ≤ 8 tam giác, kéo dài ≤ x4.6, xuyên ≤ 7.5 mm.
    Đường cơ MoBL dùng ở đây đã được chuyển sang xương đang hiển thị (pipeline/upper.py, to_torso).

Đầu vào: assets/zanat_upper.npz (tools/extract_zanatomy_upper.py), assets/upper_align.json
Đầu ra:  assets/zanat_upper.json  (sau khi chạy: dựng lại các bài, chạy QA + tools/validate_muscles.py)
Chạy:    python -m pipeline.zbind_upper        (cần: pip install pyamg pymeshlab)
"""
import json
import math
import os

import numpy as np
import trimesh
from scipy.spatial import cKDTree

from .common import ASSETS, GEOMETRY_DIR, Poser, load_model
from .geometry import read_vtp
from .skin import FieldSet, WeightField
from .zbind import (GRID_H, MARGIN, JOINT_GAP, b64, body_matrices, closest_on_polyline, decimate, drop_joint_surfaces,
                    line_geometry, remesh, remesh_adaptive, solve_harmonic, to_osim, xf7)

ORD = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth"]
THORAX = ([f"{o} rib.{s}" for o in ORD for s in "rl"] +
          [f"Costal cartilage of {o.lower()} rib.{s}" for o in ORD[:10] for s in "rl"] +
          ["Manubrium of sternum", "Body of sternum", "Xiphoid process"])
SHOULDER = ["Scapula.r", "Clavicle.r", "Scapula.l", "Clavicle.l"]
HAND = ["Scaphoid bone.r", "Lunate bone.r", "Triquetrum bone.r", "Pisiform bone.r", "Trapezium bone.r", "Trapezoid bone.r",
        "Capitate bone.r", "Hamate bone.r"] + [f"{o} metacarpal bone.r" for o in ORD[:5]] + \
       [f"{k} phalanx of {f} finger of hand.r" for f in ["first", "second", "third", "fourth", "fifth"]
        for k in ["Proximal", "Middle", "Distal"] if not (f == "first" and k == "Middle")]
HAND_VTP = [f"{n}_rvs.vtp" for n in ["capitate", "hamate", "lunate", "pisiform", "scaphoid", "trapezium", "trapezoid", "triquetrum",
                                     "metacarpal1", "metacarpal2", "metacarpal3", "metacarpal4", "metacarpal5",
                                     "thumb_proximal", "thumb_distal"]] + \
           [f"{f}_{k}_rvs.vtp" for f in ["index", "middle", "ring", "little"] for k in ["proximal", "medial", "distal"]]

# nhóm căn khớp: tên → (body OpenSim, mesh Z-Anatomy, mesh OpenSim đích, cho phép co giãn?)
# Xương tay dài bằng nhau giữa hai nguồn (cánh tay 0.318 m cả hai) → căn CỨNG: ICP có co giãn tự thu nhỏ
# hình nguồn (đã đo: 0.70 với xương cánh tay) vì đó là cách "rẻ" nhất để giảm khoảng cách.
REG_GROUPS = {
    "thorax": ("torso", THORAX + SHOULDER, ["hat_ribs_scap.vtp"], True),
    "humerus": ("humerus_r", ["Humerus.r"], ["humerus_rv.vtp"], False),
    "ulna": ("ulna_r", ["Ulna.r"], ["ulna_rv.vtp"], False),
    "radius": ("radius_r", ["Radius.r"], ["radius_rv.vtp"], False),
    "hand": ("hand_r", HAND, HAND_VTP, False),
}
# xương hiển thị: tên → (body, nhóm căn khớp, mesh Z-Anatomy, số mặt, thay hình OpenSim của body?)
DISPLAY = {
    "ribs": ("torso", "thorax", THORAX, 9000, False),
    "scapula": ("scapula_r", "thorax", ["Scapula.r"], 2500, True),
    "clavicle": ("clavicle_r", "thorax", ["Clavicle.r"], 800, True),
    "humerus": ("humerus_r", "humerus", ["Humerus.r"], 3000, True),
    "ulna": ("ulna_r", "ulna", ["Ulna.r"], 2000, True),
    "radius": ("radius_r", "radius", ["Radius.r"], 2000, True),
    "hand": ("hand_r", "hand", HAND, 4000, True),
}
# biên của trường trọng số: body → (nhóm căn khớp, mesh Z-Anatomy) hoặc (None, mesh OpenSim)
FIELD = {
    "torso": [("thorax", THORAX), (None, ["hat_spine.vtp"])],
    "scapula_r": [("thorax", ["Scapula.r"])],
    "clavicle_r": [("thorax", ["Clavicle.r"])],
    "humerus_r": [("humerus", ["Humerus.r"])],
    "ulna_r": [("ulna", ["Ulna.r"])],
    "radius_r": [("radius", ["Radius.r"])],
    "hand_r": [("hand", HAND)],
}
VIRTUAL = ("scapula_r", "clavicle_r")          # xương ảo, tư thế nghỉ = thân
# Khe khớp riêng: xương đòn mảnh và nằm sát sườn/bả vai, khe chung 25 mm xoá sạch bề mặt của nó.
GAPS = {"clavicle_r": 0.006, "scapula_r": 0.012}
# Hai trường riêng (mỗi cơ chỉ theo các xương của vùng mình): cơ cánh tay / cẳng tay KHÔNG nhận trọng số
# của lồng ngực dù lúc đứng nghỉ chúng nằm sát sườn (nếu nhận, khi dang tay phần cơ đó bị kéo ở lại thân).
ARM = ("scapula_r", "humerus_r", "ulna_r", "radius_r", "hand_r")
SHOULDER_G = ("torso", "clavicle_r", "scapula_r", "humerus_r")
JOINT_RADII = {"humerus_r": 0.04, "ulna_r": 0.035, "hand_r": 0.025}
SEGMENT_DISKS = {"humerus_r": ("humerus_r", "ulna_r", 0.5, 0.09)}

# MoBL-ARMS đặt các điểm đường cơ cẳng tay phía trụ trong hệ trục xương QUAY (tiện cho tính toán). Về giải phẫu
# các cơ này bám và nằm dọc xương TRỤ — gán theo xương quay thì khi sấp cẳng tay chúng bị xoắn theo.
LABEL_OVERRIDE = {n: {"radius_r": "ulna_r"} for n in ("FCU", "ECU", "FDPM", "FDSM", "PL")}
# Lưng xô chỉ lướt qua góc dưới bả vai; phần lớn tấm cơ nằm trên lồng ngực và cân ngực–thắt lưng. Đoạn đường cơ MoBL
# đi qua bả vai được coi là bám thân — nếu không, cả tấm lưng xô xoay theo bả vai và bung ra như cánh khi giơ tay.
LABEL_OVERRIDE.update({n: {"scapula_r": "torso"} for n in ("LAT1", "LAT2", "LAT3")})
# Hình đầu ngắn nhị đầu của Z-Anatomy chỉ là bụng cơ, dừng cách chỗ bám xương quay ~7 cm (gân chung với đầu dài):
# không cho bụng cơ đi theo xương quay — nếu không, khi giơ tay qua đầu và gập khuỷu sâu, nó bị kéo rách (x7).
LABEL_OVERRIDE["BICshort"] = {"radius_r": "humerus_r"}
LINE_SIGMA = 0.12       # m — độ rộng vùng chuyển xương dọc đường cơ (đã dò: 0.02 → kéo dài x20; 0.12 → x5.8)
SIGMA_OVERRIDE = {"TMAJ": 0.20}   # cơ tròn lớn ngắn, nối bả vai–cánh tay: chuyển đều trên cả cơ (0.12 → x6.8)
LINE_SMOOTH = 100       # số vòng làm mượt trọng số trên bề mặt cơ
# Làm mượt trọng số QUA MẶT TIẾP GIÁP giữa các cơ kề nhau (bán kính XR, XIT vòng): mỗi cơ lấy trọng số theo
# đường lực riêng nên hai cơ chồng nhau (nhị đầu / cơ cánh tay, các phần cơ delta…) trượt lệch nhau và xuyên
# vào nhau tới 13 mm. Không nối cơ thân (ngực lớn, lưng xô) với cơ tay: ở nách chúng nằm sát nhau, nối vào là
# trọng số xương cánh tay lại rò sang cơ thân (kéo dài x50). Cơ tròn lớn đứng riêng (xem cross_smooth).
# Kết quả ở 4 động tác thử: xuyên ≤ 7 mm, lật ≤ 17, kéo dài ≤ x5.8.
XR, XIT, XLAM = 0.02, 60, 0.5
SHOULDER_MUSCLES = {"DELT1", "DELT2", "DELT3", "SUPSP", "INFSP", "SUBSC", "TMIN", "TMAJ", "PECM1", "PECM2", "PECM3", "LAT1"}
# mesh Z-Anatomy → bó cơ MoBL-ARMS (bên phải)
MAP = {
    "Clavicular part of deltoid muscle": ["DELT1"], "Acromial part of deltoid muscle": ["DELT2"],
    "Scapular spinal part of deltoid muscle": ["DELT3"],
    "Supraspinatus muscle": ["SUPSP"], "Infraspinatus muscle": ["INFSP"], "Subscapularis muscle": ["SUBSC"],
    "Teres minor muscle": ["TMIN"], "Teres major muscle": ["TMAJ"],
    "Clavicular head of pectoralis major muscle": ["PECM1"], "Sternocostal head of pectoralis major muscle": ["PECM2"],
    "(Abdominal part of pectoralis major muscle)": ["PECM3"],
    "Latissimus dorsi muscle": ["LAT1", "LAT2", "LAT3"], "Coracobrachialis muscle": ["CORB"],
    "Long head of triceps brachii": ["TRIlong"], "Lateral head of triceps brachii": ["TRIlat"],
    "Medial head of triceps brachii": ["TRImed"], "Anconeus muscle": ["ANC"],
    "Long head of biceps brachii": ["BIClong"], "Short head of biceps brachii": ["BICshort"],
    "Brachialis muscle": ["BRA"], "Brachioradialis muscle": ["BRD"], "Supinator": ["SUP"],
    "Superficial head of pronator teres": ["PT"], "Deep head of pronator teres": ["PT"], "Pronator quadratus": ["PQ"],
    "Extensor carpi radialis longus": ["ECRL"], "Extensor carpi radialis brevis": ["ECRB"],
    "Humeral head of extensor carpi ulnaris": ["ECU"], "Ulnar head of extensor carpi ulnaris": ["ECU"],
    "Flexor carpi radialis": ["FCR"], "Humeral head of flexor carpi ulnaris": ["FCU"], "Ulnar head of flexor carpi ulnaris": ["FCU"],
    "Palmaris longus muscle": ["PL"], "Humero-ulnar head of flexor digitorum superficialis": ["FDSM"],
    "Radial head of flexor digitorum superficialis": ["FDSM"], "Flexor digitorum profundus": ["FDPM"],
    "Extensor digitorum": ["EDCM"],
}


def zmesh(Z, names):
    return trimesh.util.concatenate([trimesh.Trimesh(to_osim(Z[f"b:{n}:v"]), Z[f"b:{n}:f"], process=False) for n in names])


def register(Z, BM):
    print("Căn khớp xương Z-Anatomy thân trên vào OpenSim:")
    reg, trees, Ts = {}, [], []
    for g, (body, znames, vtps, scale) in REG_GROUPS.items():
        src = zmesh(Z, znames)
        dst = trimesh.util.concatenate([trimesh.Trimesh(*read_vtp(os.path.join(GEOMETRY_DIR, v)), process=False) for v in vtps])
        dst.apply_transform(BM[body])
        pts = src.sample(5000, seed=1)
        s0 = np.ptp(dst.vertices, axis=0).max() / np.ptp(src.vertices, axis=0).max() if scale else 1.0
        M0 = np.eye(4)
        M0[:3, :3] *= s0
        M0[:3, 3] = dst.vertices.mean(0) - s0 * src.vertices.mean(0)
        M, _, _ = trimesh.registration.icp(pts, dst, initial=M0, threshold=1e-7, max_iterations=100,
                                           reflection=False, translation=True, scale=scale)
        resid = np.abs(trimesh.proximity.signed_distance(dst, trimesh.transform_points(pts[:1500], M))).mean()
        sc = np.cbrt(np.linalg.det(M[:3, :3]))
        ang = math.degrees(math.acos(np.clip((np.trace(M[:3, :3] / sc) - 1) / 2, -1, 1)))
        print(f"  {g:<8} co giãn {sc:.3f}  xoay {ang:4.1f}°  sai lệch TB {resid * 1000:.1f} mm")
        reg[g] = M
        trees.append(cKDTree(to_osim(np.concatenate([Z[f"b:{n}:v"] for n in znames]))))
        Ts.append(M)

    def warp(V):
        d = np.stack([t.query(V)[0] for t in trees], 1)
        w = 1.0 / (d ** 2 + 0.008 ** 2) ** 2
        w /= w.sum(1, keepdims=True)
        return sum(w[:, i:i + 1] * (V @ M[:3, :3].T + M[:3, 3]) for i, M in enumerate(Ts))

    return reg, warp


def field_points(Z, reg, BM, spacing=0.0015):
    out = {}
    for body, parts in FIELD.items():
        meshes = []
        for g, names in parts:
            if g is None:
                m = trimesh.util.concatenate([trimesh.Trimesh(*read_vtp(os.path.join(GEOMETRY_DIR, v)), process=False) for v in names])
                m.apply_transform(BM[body])
            else:
                m = zmesh(Z, names)
                m.apply_transform(reg[g])
            meshes.append(m)
        mesh = trimesh.util.concatenate(meshes)
        n = int(mesh.area / spacing ** 2) + 500
        pts, _ = trimesh.sample.sample_surface(mesh, n, seed=3)
        out[body] = np.vstack([pts, mesh.vertices])
    return out


def drop_spheres(pts, BM):
    out = {}
    for n, p in pts.items():
        keep = np.ones(len(p), bool)
        for body, r in JOINT_RADII.items():
            keep &= np.linalg.norm(p - BM[body][:3, 3], axis=1) > r
        out[n] = p[keep]
    return out


def add_disks(pts, BM, spacing=0.003):
    out = dict(pts)
    for bone, (a, b, frac, R) in SEGMENT_DISKS.items():
        pa, pb = BM[a][:3, 3], BM[b][:3, 3]
        axis = (pb - pa) / np.linalg.norm(pb - pa)
        c = pa + frac * (pb - pa)
        u = np.cross(axis, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        g = np.arange(-R, R + spacing, spacing)
        U, Vv = np.meshgrid(g, g)
        keep = U ** 2 + Vv ** 2 <= R ** 2
        out[bone] = np.vstack([out[bone], c + U[keep, None] * u + Vv[keep, None] * v])
    return out


def line_tables(U, T0, names):
    """Mỗi đường cơ MoBL ở tư thế nghỉ: điểm (toạ độ thế giới), tham số u ∈ [0,1], nhãn xương mỗi điểm."""
    # tư thế MoBL khớp với tư thế nghỉ Rajagopal (tay buông, cẳng tay ngửa) — đúng tư thế của hình cơ
    U.evaluate({k: 0.0 for k in ["arm_flex_r", "arm_add_r", "arm_rot_r", "elbow_flex_r", "pro_sup_r"]}, "r")
    out = {}
    from .upper import SHOWN
    for nm in SHOWN:
        pp = U.path_points(nm)
        P = np.array([q for q, _ in pp]) @ T0[:3, :3].T + T0[:3, 3]
        ov = LABEL_OVERRIDE.get(nm, {})
        lab = [names.index(ov.get(b, b)) for _, b in pp]
        keep = np.r_[True, np.linalg.norm(np.diff(P, axis=0), axis=1) > 1e-5]
        P, lab = P[keep], [l for l, k in zip(lab, keep) if k]
        sarc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        out[nm] = (P, sarc / sarc[-1], lab, sarc[-1])
    return out


def line_weights(V, F, line_ids, cl, cw, tables, K, sigma=None, smooth=None):
    """Trọng số xương theo vị trí dọc đường cơ (xem đầu file)."""
    import scipy.sparse as sp
    sigma, smooth = sigma or LINE_SIGMA, smooth or LINE_SMOOTH
    W = np.zeros((len(V), K))
    grid = np.linspace(0, 1, 400)
    for slot, wslot in ((0, cw), (1, 1 - cw)):
        for li in set(cl[:, slot].tolist()):
            P, u, lab, L = tables[line_ids[li]]
            sel = cl[:, slot] == li
            uu, _ = closest_on_polyline(P, u, V[sel])
            onehot = np.zeros((len(grid), K))
            idx = np.clip(np.searchsorted(u, grid, side="right") - 1, 0, len(u) - 2)
            t = (grid - u[idx]) / np.maximum(u[idx + 1] - u[idx], 1e-9)
            np.add.at(onehot, (np.arange(len(grid)), np.array(lab)[idx]), 1 - t)
            np.add.at(onehot, (np.arange(len(grid)), np.array(lab)[idx + 1]), t)
            ker = np.exp(-0.5 * ((grid[:, None] - grid[None, :]) / max(sigma / L, 1e-4)) ** 2)
            sm = ker @ onehot
            sm /= sm.sum(1, keepdims=True)
            W[sel] += wslot[sel, None] * np.stack([np.interp(uu, grid, sm[:, k]) for k in range(K)], 1)
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    A = sp.coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(V), len(V))).tocsr()
    A.data[:] = 1
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    for _ in range(smooth):
        W = 0.5 * W + 0.5 * (A @ W) / deg[:, None]
    return W / W.sum(1, keepdims=True)


SOLO = ("Teres major", "Teres minor")   # không làm mượt chéo với cơ nào (xem chú thích trong cross_smooth)


def cross_smooth(ms):
    import scipy.sparse as sp
    trunk_names = ("pectoralis", "Latissimus")
    allV = np.concatenate([m["_V"] for m in ms])
    off = np.cumsum([0] + [len(m["_V"]) for m in ms])
    own = np.concatenate([np.full(len(m["_V"]), i) for i, m in enumerate(ms)])
    # nhóm làm mượt chéo: 1 = cơ thân (ngực, lưng xô), 0 = cơ tay–vai, 2 = đứng riêng (không nối với cơ nào).
    # Cơ tròn lớn đứng riêng: nối với delta/tam đầu là nó nhận trọng số rò từ xương đòn/xương trụ (kéo dài
    # x6.8 khi giơ tay qua đầu); nối với lưng xô thì lưng xô bị lật 55 tam giác. Đứng riêng: x5.8 / 17.
    trunk = np.array([2 if any(t in m["name"] for t in SOLO) else int(any(t in m["name"] for t in trunk_names)) for m in ms])
    W = np.concatenate([m["_W"] for m in ms])
    rows, cols = [], []
    for i, m in enumerate(ms):
        F = m["_F"] + off[i]
        e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
        rows += [e[:, 0], e[:, 1]]
        cols += [e[:, 1], e[:, 0]]
    pr = cKDTree(allV).query_pairs(XR, output_type="ndarray")
    ga, gb = trunk[own[pr[:, 0]]], trunk[own[pr[:, 1]]]
    pr = pr[(own[pr[:, 0]] != own[pr[:, 1]]) & (ga == gb) & (ga != 2)]
    rows += [pr[:, 0], pr[:, 1]]
    cols += [pr[:, 1], pr[:, 0]]
    A = sp.coo_matrix((np.ones(sum(len(x) for x in rows)), (np.concatenate(rows), np.concatenate(cols))), shape=(len(allV),) * 2).tocsr()
    A.data[:] = 1
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    for _ in range(XIT):
        W = (1 - XLAM) * W + XLAM * (A @ W) / deg[:, None]
    W /= W.sum(1, keepdims=True)
    for i, m in enumerate(ms):
        m["_W"] = W[off[i]:off[i + 1]]
    print(f"  làm mượt qua {len(pr):,} cặp điểm tiếp giáp giữa các cơ")


def main(npz=os.path.join(ASSETS, "zanat_upper.npz"), out=os.path.join(ASSETS, "zanat_upper.json"),
         field_out=os.path.join(ASSETS, "zanat_upper_field.npz")):
    from .upper import SHOWN, UpperLimb
    Z = np.load(npz)
    model, state = load_model()
    Poser(model, state).set({}, reset=True)
    BM = body_matrices(model, state)
    for v in VIRTUAL:
        BM[v] = BM["torso"].copy()
    reg, warp = register(Z, BM)

    meshes = {}
    for zname in MAP:
        V, F = remesh(to_osim(Z[f"m:{zname}:v"]), Z[f"m:{zname}:f"])
        meshes[zname] = (warp(V), F)
    allV = np.concatenate([v for v, _ in meshes.values()])

    names = list(FIELD)
    # bó cơ MoBL ở tư thế nghỉ (toạ độ thế giới) — chỉ để tô màu
    U = UpperLimb()
    rest = U.evaluate({k: 0.0 for k in ["arm_flex_r", "arm_add_r", "arm_rot_r", "elbow_flex_r", "pro_sup_r"]}, "r", want_paths=True)
    T = BM["torso"]
    lines = []
    index = {}
    for k, nm in enumerate(SHOWN):
        P = rest["paths_torso"][k] @ T[:3, :3].T + T[:3, 3]
        index[nm] = len(lines)
        lines.append({"id": nm + "_r", "_P": P, "_u": line_geometry(P)})

    print("Gán trọng số cho từng cơ (theo đường lực):")
    tables = line_tables(U, T, names)
    line_ids = [ln["id"][:-2] for ln in lines]
    out_m = []
    for zname, lids in MAP.items():
        V, F = meshes[zname]
        nv0 = len(V)
        li = [index[l] for l in lids]
        if len(li) > 1:
            d = np.stack([closest_on_polyline(lines[l]["_P"], lines[l]["_u"], V)[1] for l in li], 1)
            order = np.argsort(d, 1)[:, :2]
            r = np.arange(len(V))
            i0, i1 = 1 / (d[r, order[:, 0]] ** 2 + 1e-5), 1 / (d[r, order[:, 1]] ** 2 + 1e-5)
            cw, cl = i0 / (i0 + i1), np.array(li)[order]
        else:
            cw, cl = np.ones(len(V)), np.tile([li[0], li[0]], (len(V), 1))
        bw = line_weights(V, F, line_ids, cl, cw, tables, len(names), SIGMA_OVERRIDE.get(lids[0], LINE_SIGMA))
        dom = bw.sum(0)
        print(f"  {zname:<46} {nv0:5d} đỉnh  xương chính: "
              + ", ".join(f"{names[k]} {dom[k] / len(V) * 100:.0f}%" for k in np.argsort(-dom)[:3] if dom[k] > 0.02 * len(V)))
        out_m.append({"name": zname, "lines": li, "nv": len(V), "nf": len(F), "bones": names, "_V": V, "_F": F, "_W": bw,
                      "idx": b64(F.astype("<u2")), "v": b64(np.round(V * 1e4).astype("<i2")),
                      "l": b64(cl.astype("u1")), "w": b64(cw.astype("<f4"))})
    cross_smooth(out_m)
    for mm in out_m:
        mm["bw"] = b64(np.round(mm.pop("_W") * 65535).astype("<u2"))
        mm.pop("_V"); mm.pop("_F")

    out_b = []
    for g, (body, rg, znames, nf, replace) in DISPLAY.items():
        mesh = decimate(zmesh(Z, znames), nf)
        Mx = np.linalg.inv(BM[body]) @ reg[rg]
        Vb = np.asarray(mesh.vertices) @ Mx[:3, :3].T + Mx[:3, 3]
        out_b.append({"group": g, "body": body, "replace": replace, "nv": len(Vb), "v": b64(Vb.astype("<f4")),
                      "idx": b64(np.asarray(mesh.faces, dtype="<u2" if len(Vb) < 65535 else "<u4"))})

    rest_xf = {}
    for n in names + [n[:-2] + "_l" for n in names if n.endswith("_r")]:
        rest_xf[n] = xf7(BM[n] if n in BM else BM[n.replace("_l", "_r")] if n[:-2] + "_r" in VIRTUAL else BM[n])
    res = {"version": 2, "region": "upper", "weights": "line",
           "source": "Z-Anatomy (CC BY-SA 4.0) + MoBL-ARMS (Saul et al. 2015), warped onto OpenSim RajagopalLaiUhlrich2023",
           "method": "harmonic weights + dual quaternion skinning",
           "skinBodies": names, "rest": rest_xf, "lines": [{"id": ln["id"]} for ln in lines],
           "muscles": out_m, "bones": out_b}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, separators=(",", ":"))
    print(f"OK -> {out} ({os.path.getsize(out) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
