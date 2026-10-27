"""Gắn mesh cơ + xương Z-Anatomy vào mô hình OpenSim — CHẠY MỘT LẦN, dùng cho mọi bài.

1. Căn xương chậu, đùi, bánh chè, cẳng chân của Z-Anatomy vào xương OpenSim ở tư thế
   trung tính (ICP có co giãn), rồi uốn mesh cơ theo các xương gần nó.
2. Dựng TRƯỜNG TRỌNG SỐ ĐIỀU HOÀ chung trên lưới 3D phủ vùng hông – đùi – cẳng chân: giải
   phương trình Laplace với bề mặt xương làm biên (trừ mặt khớp), cộng "đĩa giữa đoạn chi"
   để trọng số không rò từ khớp này sang khớp kia (xem pipeline/skin.py).
3. Dựng lại lưới tam giác mỗi cơ cho đều cạnh, mịn hơn ở quanh khớp.
4. Lấy trọng số xương tại từng đỉnh cơ → viewer biến dạng bằng dual-quaternion skinning.
5. Gán mỗi đỉnh vào bó cơ OpenSim gần nhất — CHỈ để tô màu theo độ giãn của bó đó;
   hình dạng không phụ thuộc đường cơ.

Đầu vào: assets/zanat_lowerlimb.npz (tools/extract_zanatomy.py tạo từ FBX của Z-Anatomy)
Đầu ra:  assets/zanat_binding.json  (cho viewer)
         assets/zanat_field.npz     (trường trọng số, cho bộ kiểm tra chất lượng)
Chạy:    python -m pipeline.zbind        (cần thêm: pip install pyamg pymeshlab)
"""
import base64
import json
import math
import os
import time

import numpy as np
import scipy.sparse as sp
import trimesh
from scipy.spatial import cKDTree

from .common import ASSETS, GEOMETRY_DIR, Poser, load_model, body_names
from .export import muscle_polyline, resample
from .geometry import read_vtp
from .skin import FieldSet, WeightField

# Z-Anatomy (x: trái +, y: sau +, z: lên)  ->  OpenSim (X: trước, Y: lên, Z: phải)
AXES = np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], dtype=float)

BONE_GROUPS = {
    "pelvis": ("pelvis", ["Hip bone.r", "Hip bone.l", "Sacrum"], ["r_pelvis.vtp", "l_pelvis.vtp", "sacrum.vtp"], 9000),
    "femur": ("femur_r", ["Femur.r"], ["r_femur.vtp"], 3500),
    "patella": ("patella_r", ["Patella.r"], ["r_patella.vtp"], 600),
    "shank": ("tibia_r", ["Tibia.r", "Fibula.r"], ["r_tibia.vtp", "r_fibula.vtp"], 4000),
}
# Xương làm biên cho trường trọng số. Xương Z-Anatomy (đã căn) cho vùng có cơ bám; xương
# OpenSim cho bàn chân và cột sống (không có trong bộ trích Z-Anatomy).
FIELD_BONES = [
    ("torso", None, ["hat_spine.vtp"]),
    ("pelvis", "pelvis", None),
    ("femur_r", "femur", None),
    ("patella_r", "patella", None),
    ("tibia_r", "shank", None),
    ("talus_r", None, ["r_talus.vtp"]),
    ("calcn_r", None, ["r_foot.vtp"]),
    ("toes_r", None, ["r_bofoot.vtp"]),
]
GRID_H = 0.006          # bước lưới 6 mm
MARGIN = 0.05           # lề quanh vùng có cơ
# Mặt khớp: phần bề mặt xương nằm gần một xương khác hơn JOINT_GAP thì KHÔNG làm biên.
# Nếu giữ chúng làm biên, trọng số phải đổi từ xương này sang xương kia trong khe khớp chỉ
# vài mm → cơ đi sát khớp bị xé/gập khi gập sâu. Bỏ đi thì vùng chuyển tiếp trải rộng quanh
# khớp, đổi dần theo góc như mô mềm thật.
JOINT_GAP = 0.025
# Thêm một quả cầu quanh tâm mỗi khớp: bề mặt xương trong đó cũng không làm biên, để vùng
# chuyển tiếp quanh khớp đủ rộng cho gập sâu (đã dò bằng pipeline.qa ở đáy squat, sumo, RDL,
# split squat: nhỏ hơn thì nếp gấp sau gối/trước hông bị gập ngược nhiều hơn; lớn hơn thì
# cơ ở gần điểm bám bắt đầu trôi khỏi xương).
JOINT_RADII = {"femur_r": 0.035, "tibia_r": 0.06, "talus_r": 0.05}   # tâm khớp = gốc của body này
# Lưới tam giác của cơ: dựng lại cho đều cạnh (không có tam giác "kim"), và mịn hơn ở vùng
# trọng số đổi nhanh quanh khớp — tam giác quá to so với độ cong của phép biến dạng sẽ bị
# "xoắn" (pháp tuyến lật) dù trường biến dạng không gập.
REMESH_EDGE = 0.0065    # cạnh tam giác mục tiêu khi dựng lại lưới cơ
REMESH_FINE = 0.0035    # cạnh tam giác ở vùng chuyển tiếp quanh khớp
REFINE_GRAD = 14.0      # độ dốc trọng số (1/m) coi là "vùng chuyển tiếp"


def drop_joint_spheres(bone_pts, BM, radii=JOINT_RADII):
    out = {}
    for n, p in bone_pts.items():
        keep = np.ones(len(p), bool)
        for body, r in radii.items():
            keep &= np.linalg.norm(p - BM[body][:3, 3], axis=1) > r
        out[n] = p[keep]
    return out


def drop_joint_surfaces(bone_pts, gap=JOINT_GAP):
    trees = {n: cKDTree(p) for n, p in bone_pts.items()}
    out = {}
    for n, p in bone_pts.items():
        keep = np.ones(len(p), bool)
        for m, t in trees.items():
            if m != n:
                keep &= t.query(p, distance_upper_bound=gap)[0] > gap
        out[n] = p[keep]
    return out

# mesh Z-Anatomy -> bó cơ OpenSim (bên phải) dùng để tô màu
MAP = {
    "Gluteus maximus muscle": ["glmax1_r", "glmax2_r", "glmax3_r"],
    "Gluteus medius muscle": ["glmed1_r", "glmed2_r", "glmed3_r"],
    "Gluteus minimus muscle": ["glmin1_r", "glmin2_r", "glmin3_r"],
    "Tensor fasciae latae": ["tfl_r"],
    "Piriformis muscle": ["piri_r"],
    "Iliacus muscle": ["iliacus_r"],
    "Psoas major": ["psoas_r"],
    "Sartorius muscle": ["sart_r"],
    "Rectus femoris muscle": ["recfem_r"],
    "Vastus lateralis muscle": ["vaslat_r"],
    "Vastus medialis muscle": ["vasmed_r"],
    "Vastus intermedius muscle": ["vasint_r"],
    "Long head of biceps femoris": ["bflh_r"],
    "Short head of biceps femoris": ["bfsh_r"],
    "Semimembranosus muscle": ["semimem_r"],
    "Semitendinosus muscle": ["semiten_r"],
    "Adductor magnus": ["addmagProx_r", "addmagMid_r", "addmagDist_r", "addmagIsch_r"],
    "(Adductor minimus)": ["addmagProx_r"],
    "Adductor longus": ["addlong_r"],
    "Adductor brevis": ["addbrev_r"],
    "Gracilis muscle": ["grac_r"],
    "Lateral head of gastrocnemius": ["gaslat_r"],
    "Medial head of gastrocnemius": ["gasmed_r"],
    "Soleus muscle": ["soleus_r"],
}
# Mỗi cơ chỉ chịu ảnh hưởng của những xương nó bám vào (và các xương nằm giữa hai đầu bám,
# tức các khớp nó bắc qua). Ví dụ cơ rộng (vasti) bám xương đùi và — qua gân bánh chè —
# xương chày, KHÔNG bám xương chậu: không để phần trên của chúng bị kéo theo chậu ở nếp
# trước hông khi gập người (đúng là lỗi "cơ tứ đầu bị bẻ vào trong").
PELVIS_FEMUR = ("pelvis", "femur_r")
ALLOWED = {
    "Gluteus maximus muscle": PELVIS_FEMUR, "Gluteus medius muscle": PELVIS_FEMUR,
    "Gluteus minimus muscle": PELVIS_FEMUR, "Tensor fasciae latae": PELVIS_FEMUR,
    "Piriformis muscle": PELVIS_FEMUR, "Iliacus muscle": PELVIS_FEMUR,
    "Psoas major": ("torso", "pelvis", "femur_r"),
    "Sartorius muscle": ("pelvis", "femur_r", "tibia_r"), "Rectus femoris muscle": ("pelvis", "femur_r", "tibia_r"),
    "Vastus lateralis muscle": ("femur_r", "tibia_r"), "Vastus medialis muscle": ("femur_r", "tibia_r"),
    "Vastus intermedius muscle": ("femur_r", "tibia_r"),
    "Long head of biceps femoris": ("pelvis", "femur_r", "tibia_r"), "Short head of biceps femoris": ("femur_r", "tibia_r"),
    "Semimembranosus muscle": ("pelvis", "femur_r", "tibia_r"), "Semitendinosus muscle": ("pelvis", "femur_r", "tibia_r"),
    "Adductor magnus": PELVIS_FEMUR, "(Adductor minimus)": PELVIS_FEMUR,
    "Adductor longus": PELVIS_FEMUR, "Adductor brevis": PELVIS_FEMUR,
    "Gracilis muscle": ("pelvis", "femur_r", "tibia_r"),
    "Lateral head of gastrocnemius": ("femur_r", "tibia_r"), "Medial head of gastrocnemius": ("femur_r", "tibia_r"),
    "Soleus muscle": ("tibia_r",),
}


# Đã thử cho mỗi cơ một trường riêng theo ALLOWED: cơ không còn bị kéo bởi xương nó không bám,
# NHƯNG hai cơ kề nhau dùng hai trường khác nhau thì đi lệch nhau và xuyên vào nhau (đo ở đáy
# squat: sâu tới 13 mm). Dùng MỘT trường chung (có đĩa giữa đoạn chi chặn rò trọng số) thì
# xuyên lẫn nhau còn < 3 mm và ít nếp gấp hơn → mặc định dùng trường chung.
# Đặt ZBIND_PER_MUSCLE=1 để thử lại cách theo từng cơ.
ALL = ("torso", "pelvis", "femur_r", "tibia_r")
if not os.environ.get("ZBIND_PER_MUSCLE"):
    ALLOWED = {k: ALL for k in ALLOWED}


def restrict(W, names, allowed):
    mask = np.array([n in allowed for n in names], float)
    W = W * mask
    return W / np.maximum(W.sum(1, keepdims=True), 1e-9), mask


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")


def to_osim(v):
    return v @ AXES.T


def decimate(m, n):
    m = trimesh.Trimesh(m.vertices, m.faces, process=True)
    if len(m.faces) > n:
        m = m.simplify_quadric_decimation(face_count=n)
    m.remove_unreferenced_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    return m


def remesh(V, F, target=None):
    """Lưới tam giác đều (isotropic) bằng MeshLab: tam giác gần đều, không có tam giác "kim"
    — tam giác kim lật pháp tuyến chỉ với một biến dạng rất nhỏ và gây đốm tối khi tô bóng."""
    import pymeshlab
    target = target or REMESH_EDGE
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(np.asarray(V, float), np.asarray(F, np.int32)))
    ms.meshing_remove_duplicate_vertices()
    ms.meshing_isotropic_explicit_remeshing(iterations=10, targetlen=pymeshlab.PureValue(target), adaptive=False, featuredeg=75,
                                            checksurfdist=True, maxsurfdist=pymeshlab.PureValue(target * 0.15))
    m = ms.current_mesh()
    return m.vertex_matrix().astype(float), m.face_matrix().astype(np.int64)


def weight_gradient(V, F, field):
    """Độ dốc trọng số lớn nhất quanh mỗi đỉnh (đổi bao nhiêu trên mỗi mét)."""
    _, W = field.weights(V)
    e = np.unique(np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)
    g = np.abs(W[e[:, 0]] - W[e[:, 1]]).max(1) / np.maximum(np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1), 1e-6)
    q = np.zeros(len(V))
    np.maximum.at(q, e[:, 0], g)
    np.maximum.at(q, e[:, 1], g)
    return q


def remesh_adaptive(V, F, field, coarse=REMESH_EDGE, fine=REMESH_FINE, grad=REFINE_GRAD):
    """Lưới đều cạnh ~coarse; ở vùng trọng số đổi nhanh (quanh khớp) dựng lại lưới đều mịn hơn
    (~fine). Tam giác ở mọi nơi đều gần đều cạnh — không tạo tam giác kim như cách chia đôi cạnh."""
    import pymeshlab
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(np.asarray(V, float), np.asarray(F, np.int32)))
    for _ in range(2):
        m = ms.current_mesh()
        Vm, Fm = m.vertex_matrix().astype(float), m.face_matrix().astype(np.int64)
        q = weight_gradient(Vm, Fm, field)
        if (q > grad).sum() == 0:
            break
        ms.add_mesh(pymeshlab.Mesh(Vm, Fm.astype(np.int32), v_scalar_array=q))
        ms.compute_selection_by_condition_per_face(condselect=f"(q0 > {grad}) || (q1 > {grad}) || (q2 > {grad})")
        ms.apply_selection_dilatation()
        ms.apply_selection_dilatation()
        ms.meshing_isotropic_explicit_remeshing(iterations=8, targetlen=pymeshlab.PureValue(fine), selectedonly=True, featuredeg=75,
                                                adaptive=False, checksurfdist=True, maxsurfdist=pymeshlab.PureValue(fine * 0.2))
    m = ms.current_mesh()
    return m.vertex_matrix().astype(float), m.face_matrix().astype(np.int64)


def line_geometry(P):
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    return s / s[-1]


def closest_on_polyline(P, u_arr, V):
    best_d, best_u = np.full(len(V), np.inf), np.zeros(len(V))
    for k in range(len(P) - 1):
        a, ab = P[k], P[k + 1] - P[k]
        t = np.clip(((V - a) @ ab) / (ab @ ab), 0, 1)
        d = np.linalg.norm(V - (a + t[:, None] * ab), axis=1)
        m = d < best_d
        best_d[m], best_u[m] = d[m], u_arr[k] + t[m] * (u_arr[k + 1] - u_arr[k])
    return best_u, best_d


def body_matrices(model, state):
    BM = {}
    for b in body_names(model):
        X = model.getBodySet().get(b).getTransformInGround(state)
        M = np.eye(4)
        M[:3, :3] = [[X.R().get(i, j) for j in range(3)] for i in range(3)]
        M[:3, 3] = [X.p().get(i) for i in range(3)]
        BM[b] = M
    return BM


def register_bones(Z, BM):
    print("Căn khớp xương Z-Anatomy vào OpenSim:")
    reg, trees, Ts = {}, [], []
    for g, (body, znames, vtps, _) in BONE_GROUPS.items():
        src = trimesh.util.concatenate([trimesh.Trimesh(to_osim(Z[f"b:{n}:v"]), Z[f"b:{n}:f"], process=False) for n in znames])
        dst = trimesh.util.concatenate([trimesh.Trimesh(*read_vtp(os.path.join(GEOMETRY_DIR, v)), process=False) for v in vtps])
        dst.apply_transform(BM[body])
        pts = src.sample(4000, seed=1)
        s0 = np.ptp(dst.vertices[:, 1]) / np.ptp(src.vertices[:, 1])
        M0 = np.eye(4)
        M0[:3, :3] *= s0
        M0[:3, 3] = dst.vertices.mean(0) - s0 * src.vertices.mean(0)
        M, _, _ = trimesh.registration.icp(pts, dst, initial=M0, threshold=1e-7, max_iterations=80,
                                           reflection=False, translation=True, scale=True)
        resid = np.abs(trimesh.proximity.signed_distance(dst, trimesh.transform_points(pts[:1500], M))).mean()
        sc = np.cbrt(np.linalg.det(M[:3, :3]))
        ang = math.degrees(math.acos(np.clip((np.trace(M[:3, :3] / sc) - 1) / 2, -1, 1)))
        print(f"  {g:<8} co giãn {sc:.3f}  xoay {ang:4.1f}°  sai lệch TB {resid * 1000:.1f} mm")
        reg[g] = M
        trees.append(cKDTree(np.concatenate([to_osim(Z[f"b:{n}:v"]) for n in znames])))
        Ts.append(M)

    def warp(V):
        d = np.stack([t.query(V)[0] for t in trees], 1)
        w = 1.0 / (d ** 2 + 0.008 ** 2) ** 2
        w /= w.sum(1, keepdims=True)
        return sum(w[:, i:i + 1] * (V @ M[:3, :3].T + M[:3, 3]) for i, M in enumerate(Ts))

    return reg, warp


def bone_surface_points(Z, reg, BM, spacing=0.0015):
    """Điểm lấy mẫu dày trên bề mặt từng xương biên (toạ độ ground, tư thế nghỉ)."""
    out = {}
    for name, group, vtps in FIELD_BONES:
        if group:
            _, znames, _, _ = BONE_GROUPS[group]
            mesh = trimesh.util.concatenate([trimesh.Trimesh(to_osim(Z[f"b:{n}:v"]), Z[f"b:{n}:f"], process=False) for n in znames])
            mesh.apply_transform(reg[group])
        else:
            mesh = trimesh.util.concatenate([trimesh.Trimesh(*read_vtp(os.path.join(GEOMETRY_DIR, v)), process=False) for v in vtps])
            mesh.apply_transform(BM[name])
        n = int(mesh.area / spacing ** 2) + 500
        pts, _ = trimesh.sample.sample_surface(mesh, n, seed=3)
        out[name] = np.vstack([pts, mesh.vertices])
    return out


# "Đĩa giữa đoạn chi": một đĩa ảo vuông góc với trục xương ở giữa đùi / giữa cẳng chân, gắn
# cứng vào xương đó. Không có nó, trọng số của xương xa (vd. xương chày) vẫn rò lên tận giữa
# đùi với giá trị nhỏ — nhưng nhân với cánh tay đòn rất dài khi gập gối 120° thì đủ để ép bẹp
# mô ở đó. Đĩa chặn rò, giữ vùng chuyển tiếp quanh khớp, và đúng với thực tế: mô giữa đùi đi
# theo xương đùi.
SEGMENT_DISKS = {"femur_r": ("femur_r", "tibia_r", 0.5), "tibia_r": ("tibia_r", "talus_r", 0.5)}
DISK_RADIUS = 0.13


def add_segment_disks(bone_pts, BM, spacing=0.003):
    out = dict(bone_pts)
    for bone, (a, b, frac) in SEGMENT_DISKS.items():
        pa, pb = BM[a][:3, 3], BM[b][:3, 3]
        axis = (pb - pa) / np.linalg.norm(pb - pa)
        c = pa + frac * (pb - pa)
        u = np.cross(axis, [0, 0, 1.0])
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        g = np.arange(-DISK_RADIUS, DISK_RADIUS + spacing, spacing)
        U, Vv = np.meshgrid(g, g)
        keep = U ** 2 + Vv ** 2 <= DISK_RADIUS ** 2
        disk = c + U[keep, None] * u + Vv[keep, None] * v
        out[bone] = np.vstack([out[bone], disk])
    return out


def solve_harmonic(bone_pts, lo, hi, h):
    """Trọng số điều hoà trên lưới [lo, hi] bước h. Trả về W [K, nx, ny, nz]."""
    shape = np.ceil((hi - lo) / h).astype(int) + 1
    nx, ny, nz = shape
    gx, gy, gz = [lo[i] + h * np.arange(shape[i]) for i in range(3)]
    G = np.stack(np.meshgrid(gx, gy, gz, indexing="ij"), -1).reshape(-1, 3)
    K = len(bone_pts)
    print(f"  lưới {nx}×{ny}×{nz} = {len(G):,} nút, {K} xương")
    dist = np.full((len(G), K), np.inf)
    for k, (name, pts) in enumerate(bone_pts.items()):
        dist[:, k] = cKDTree(pts).query(G, distance_upper_bound=h * 1.05)[0]
    near = np.isfinite(dist).any(1)
    label = np.full(len(G), -1)
    label[near] = np.argmin(dist[near], 1)
    free = label < 0
    print(f"  {near.sum():,} nút nằm trên bề mặt xương (biên), {free.sum():,} nút cần giải")

    # đồ thị lưới 6 hàng xóm, Neumann (không thông lượng) ở biên hộp
    idx = np.arange(len(G)).reshape(nx, ny, nz)
    pairs = [np.stack([idx[:-1].ravel(), idx[1:].ravel()], 1),
             np.stack([idx[:, :-1].ravel(), idx[:, 1:].ravel()], 1),
             np.stack([idx[:, :, :-1].ravel(), idx[:, :, 1:].ravel()], 1)]
    E = np.concatenate(pairs)
    deg = np.bincount(E.ravel(), minlength=len(G)).astype(float)
    fid = -np.ones(len(G), int)
    fid[free] = np.arange(free.sum())
    a, b = E[:, 0], E[:, 1]
    ff = free[a] & free[b]
    rows = np.concatenate([fid[a[ff]], fid[b[ff]]])
    cols = np.concatenate([fid[b[ff]], fid[a[ff]]])
    nF = free.sum()
    A = sp.csr_matrix((np.full(len(rows), -1.0), (rows, cols)), shape=(nF, nF)) + sp.diags(deg[free])
    # vế phải: hàng xóm là nút biên
    fd = free[a] & ~free[b]
    df = ~free[a] & free[b]
    rhs_rows = np.concatenate([fid[a[fd]], fid[b[df]]])
    rhs_lab = np.concatenate([label[b[fd]], label[a[df]]])
    RHS = np.zeros((nF, K))
    np.add.at(RHS, (rhs_rows, rhs_lab), 1.0)
    W = np.zeros((len(G), K))
    W[near, label[near]] = 1.0
    t0 = time.time()
    try:
        import pyamg
        ml = pyamg.smoothed_aggregation_solver(A.tocsr(), symmetry="hermitian")
        for k in range(K):
            W[free, k] = ml.solve(RHS[:, k], tol=1e-9, accel="cg", maxiter=400)
    except ImportError:
        from scipy.sparse.linalg import cg
        M = sp.diags(1.0 / A.diagonal())
        for k in range(K):
            W[free, k], _ = cg(A, RHS[:, k], rtol=1e-9, maxiter=20000, M=M)
    W = np.clip(W, 0, 1)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    res = np.abs(W.sum(1) - 1).max()
    print(f"  giải xong sau {time.time() - t0:.1f} s (tổng trọng số lệch 1 tối đa {res:.1e})")
    return W.T.reshape(K, nx, ny, nz)


def xf7(M):
    from .skin import mat_to_quat
    q = mat_to_quat(M[:3, :3])
    return [float(x) for x in M[:3, 3]] + [float(x) for x in q]


def main(npz=os.path.join(ASSETS, "zanat_lowerlimb.npz"), out=os.path.join(ASSETS, "zanat_binding.json"),
         field_out=os.path.join(ASSETS, "zanat_field.npz")):
    Z = np.load(npz)
    model, state = load_model()
    Poser(model, state).set({}, reset=True)          # tư thế trung tính = tư thế nghỉ
    BM = body_matrices(model, state)
    reg, warp = register_bones(Z, BM)

    # mesh cơ ở tư thế nghỉ
    meshes = {}
    for zname in MAP:
        V, F = remesh(to_osim(Z[f"m:{zname}:v"]), Z[f"m:{zname}:f"])
        meshes[zname] = (warp(V), F)
    allV = np.concatenate([v for v, _ in meshes.values()])

    print("Dựng trường trọng số điều hoà:")
    lo, hi = allV.min(0) - MARGIN, allV.max(0) + MARGIN
    lo[2] = max(lo[2], -0.03)                        # chỉ nửa phải + một chút qua đường giữa
    bpts = add_segment_disks(drop_joint_spheres(drop_joint_surfaces(bone_surface_points(Z, reg, BM)), BM), BM)
    for n, p in bpts.items():
        print(f"  biên {n:<10} {len(p):7,} điểm")
    names = [n for n, _, _ in FIELD_BONES if len(bpts[n])]            # bỏ xương không còn mặt biên
    names = [n for n in names if any(n in ALLOWED[z] for z in MAP)]   # chỉ giữ xương có cơ theo
    print("  xương tham gia biến dạng:", ", ".join(names))
    # Mỗi nhóm xương (theo ALLOWED) có một trường riêng: xương ngoài nhóm coi như không tồn tại
    # (không làm biên), nên cơ không "thấy" xương mà nó không bám vào.
    fields = {}
    for key in sorted({tuple(n for n in names if n in ALLOWED[z]) for z in MAP}, key=len):
        print(f"  nhóm {' + '.join(key)}")
        if len(key) == 1:
            W = np.ones((1, 2, 2, 2))
            fields[key] = WeightField(W, lo, (hi - lo).max(), list(key))
        else:
            W = solve_harmonic({n: bpts[n] for n in key}, lo, hi, GRID_H)
            fields[key] = WeightField(W, lo, GRID_H, list(key))
    fset = FieldSet(fields, names)
    fset.save(field_out)

    # bó cơ OpenSim ở tư thế nghỉ (chỉ để tô màu)
    muscles = model.getMuscles()
    lines, index = [], {}
    for lids in MAP.values():
        for lid in lids:
            if lid not in index:
                P = resample(muscle_polyline(muscles.get(lid), state))
                index[lid] = len(lines)
                lines.append({"id": lid, "_P": P, "_u": line_geometry(P)})

    print("Gán trọng số cho từng cơ:")
    out_m = []
    for zname, lids in MAP.items():
        V, F = meshes[zname]
        nv0 = len(V)
        field = fset.for_bones(ALLOWED[zname])
        V, F = remesh_adaptive(V, F, field)
        bi, bw = field.weights(V)
        li = [index[l] for l in lids]
        d = np.stack([closest_on_polyline(lines[l]["_P"], lines[l]["_u"], V)[1] for l in li], 1)
        if len(li) > 1:
            order = np.argsort(d, 1)[:, :2]
            r = np.arange(len(V))
            i0, i1 = 1 / (d[r, order[:, 0]] ** 2 + 1e-5), 1 / (d[r, order[:, 1]] ** 2 + 1e-5)
            cw = i0 / (i0 + i1)
            cl = np.array(li)[order]
        else:
            cw = np.ones(len(V))
            cl = np.tile([li[0], li[0]], (len(V), 1))
        dom = bw.sum(0)
        print(f"  {zname:<32} {nv0:5d} → {len(V):5d} đỉnh  xương chính: "
              + ", ".join(f"{names[k]} {dom[k] / len(V) * 100:.0f}%" for k in np.argsort(-dom)[:3] if dom[k] > 0.02 * len(V)))
        out_m.append({"name": zname, "lines": li, "nv": len(V), "nf": len(F), "bones": [n for n in names if n in ALLOWED[zname]],
                      "idx": b64(F.astype("<u2")),
                      "v": b64(np.round(V * 1e4).astype("<i2")),            # 0.1 mm
                      "bw": b64(np.round(bw * 65535).astype("<u2")),   # [nv, K] theo skinBodies
                      "l": b64(cl.astype("u1")), "w": b64(cw.astype("<f4"))})

    out_b = []
    for g, (body, znames, _, nf) in BONE_GROUPS.items():
        mesh = decimate(trimesh.util.concatenate([trimesh.Trimesh(to_osim(Z[f"b:{n}:v"]), Z[f"b:{n}:f"], process=False) for n in znames]), nf)
        M = np.linalg.inv(BM[body]) @ reg[g]
        V = np.asarray(mesh.vertices) @ M[:3, :3].T + M[:3, 3]
        out_b.append({"group": g, "body": body, "nv": len(V), "v": b64(V.astype("<f4")),
                      "idx": b64(np.asarray(mesh.faces, dtype="<u2" if len(V) < 65535 else "<u4"))})

    rest = {}
    for n in names + [n[:-2] + "_l" for n in names if n.endswith("_r")]:
        rest[n] = xf7(BM[n])
    res = {"version": 2,
           "source": "Z-Anatomy (CC BY-SA 4.0), warped onto OpenSim RajagopalLaiUhlrich2023",
           "method": "harmonic weights + dual quaternion skinning",
           "skinBodies": names, "rest": rest,
           "lines": [{"id": ln["id"]} for ln in lines],
           "muscles": out_m, "bones": out_b}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, separators=(",", ":"))
    print(f"OK -> {out} ({os.path.getsize(out) / 1024:.0f} KB), {field_out} ({os.path.getsize(field_out) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
