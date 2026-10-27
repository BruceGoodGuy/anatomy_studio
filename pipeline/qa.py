"""Kiểm tra chất lượng hình học của mesh cơ cho một bài tập — chạy tự động mỗi lần Tạo dữ liệu.

Dùng ĐÚNG phép biến dạng mà viewer dùng (pipeline/skin.py ⇄ web/anatomy-core.js, có test so
sánh) và đo trên mọi cơ, cả hai bên chân:

* flips      — tam giác bị lật so với chuyển động cục bộ của bề mặt → gai, "bẻ vào trong",
               lỗ thủng (mặt sau bị ẩn). Không tính tam giác "kim" < 1 mm² (không nhìn thấy).
* edge_max   — cạnh bị kéo dài nhất so với tư thế nghỉ → "rách".
* jac_neg    — tỉ lệ đỉnh mà trường biến dạng bị gập ngược (định thức Jacobian < 0): mô tự
               xuyên qua chính nó. Ở nếp khớp gập sâu, một ít là không tránh được (mô ép vào
               nhau như ngoài đời) → chỉ cảnh báo; lan rộng → lỗi.
* penetration— độ xuyên MỚI giữa hai cơ kề nhau ở đáy động tác → "các nhóm cơ chồng lên nhau".

Vượt ngưỡng LỖI (LIMITS): build vẫn tạo file nhưng đánh dấu "fail", Studio báo đỏ và khoá
nút tải gói; dòng lệnh trả mã lỗi 1.

Dòng lệnh:
    python -m pipeline.qa squat-khong-ta          # kiểm tra một bài đã tạo
    python -m pipeline.qa --all                   # tất cả bài trong output/
    python -m pipeline.qa --selftest              # so viewer (JS) với bản tham chiếu Python
"""
import base64
import json
import os
import sys

import numpy as np

from .common import ASSETS, OUTPUT_DIR, WEB_DIR
from .qa_metrics import MeshQA
from .skin import FieldSet, apply_dqs, jacobian_det, skin_dq

# Ngưỡng. Để so sánh, cách neo theo đường cơ cũ (bản bị lỗi) ở đáy squat: 50–120 tam giác lật
# mỗi cơ, cạnh bị kéo dài tới x33. Bản hiện tại ở 6 bài mẫu: ≤ 14 tam giác nhỏ, ≤ x5,
# gập ngược ≤ 5% (chỉ ở nếp háng/khoeo khi gập sâu), xuyên giữa cơ ≤ 3 mm.
LIMITS = {
    "flip_warn": 0, "flip_fail": 25,           # tam giác lật / cơ
    "edge_warn": 4.5, "edge_fail": 6.0,        # cạnh dài gấp bao nhiêu lần
    "jac_neg_warn": 0.0, "jac_neg_fail": 6.0,  # % đỉnh của một cơ có Jacobian < 0
    "pen_warn": 0.004, "pen_fail": 0.008,      # xuyên giữa hai cơ (m)
}

dec = lambda s, t: np.frombuffer(base64.b64decode(s), t)
MIRROR = np.array([1.0, 1.0, -1.0])


class Binding:
    def __init__(self, path=os.path.join(ASSETS, "zanat_binding.json"), field=os.path.join(ASSETS, "zanat_field.npz")):
        self.z = json.load(open(path, encoding="utf-8"))
        # vùng thân trên dùng trọng số theo đường lực (không có trường thể tích) → không đo Jacobian
        self.fields = FieldSet.load(field) if field and os.path.exists(field) and self.z.get("weights") != "line" else None
        self.names = self.z["skinBodies"]
        self.muscles = []
        for zm in self.z["muscles"]:
            V = dec(zm["v"], "<i2").reshape(-1, 3) / 1e4
            F = dec(zm["idx"], "<u2").reshape(-1, 3).astype(np.int64)
            K = len(self.z["skinBodies"])
            bw = dec(zm["bw"], "<u2").reshape(-1, K) / 65535.0
            bi = np.tile(np.arange(K), (len(bw), 1))
            bw = bw / bw.sum(1, keepdims=True)
            FL = F[:, [0, 2, 1]]
            allowed = zm.get("bones", self.names)
            mask = np.array([n in allowed for n in self.names], float)
            self.muscles.append({"name": zm["name"], "V": V, "F": F, "bi": bi, "bw": bw, "mask": mask, "bones": allowed,
                                 "qa": {"R": MeshQA(V, F), "L": MeshQA(V * MIRROR, FL)},
                                 })

    def side_names(self, side):
        return self.names if side == "R" else [n[:-2] + "_l" if n.endswith("_r") else n for n in self.names]

    def dq(self, motion_bodies, xforms_frame, side):
        names = self.side_names(side)
        rest = np.array([self.z["rest"][n] for n in names])
        cur = np.array([xforms_frame[motion_bodies.index(n)] for n in names])
        return skin_dq(rest, cur)


def _inside_depth(mesh, P):
    """(điểm nằm trong mesh kín?, khoảng cách tới mặt) — kiểm tra bằng tia, chỉ tính khoảng
    cách cho điểm nằm trong."""
    import trimesh
    ins = mesh.contains(P)
    d = np.zeros(len(P))
    if ins.any():
        _, d[ins], _ = trimesh.proximity.closest_point(mesh, P[ins])
    return ins, d


def penetration(b, motion, frames, sides):
    """Độ xuyên MỚI giữa các cơ kề nhau (không tính chỗ mesh gốc vốn đã chạm nhau)."""
    import trimesh
    from scipy.spatial import cKDTree
    B = len(motion["bodies"])
    xf = dec(motion["xforms_f32"], "<f4").reshape(-1, B, 7).astype(float)
    if not hasattr(b, "_pairs"):
        trees = [cKDTree(m["V"]) for m in b.muscles]
        b._pairs, b._rest_in = [], {}
        rest_mesh = [trimesh.Trimesh(m["V"], m["F"], process=False) for m in b.muscles]
        for i, mi in enumerate(b.muscles):
            for j in range(len(b.muscles)):
                if i == j or not rest_mesh[j].is_watertight:
                    continue
                near = trees[j].query(mi["V"], distance_upper_bound=0.015)[0] < 0.015
                if near.any():
                    idx = np.where(near)[0]
                    ins, _ = _inside_depth(rest_mesh[j], mi["V"][idx])
                    b._pairs.append((i, j, idx))
                    b._rest_in[(i, j)] = set(idx[ins].tolist())
    worst = {}
    for f in frames:
        for side in sides:
            q0, qe = b.dq(motion["bodies"], xf[f], side)
            V = [apply_dqs(m["V"] if side == "R" else m["V"] * MIRROR, m["bi"], m["bw"], q0, qe) for m in b.muscles]
            meshes = {}
            for i, j, idx in b._pairs:
                if j not in meshes:
                    F = b.muscles[j]["F"] if side == "R" else b.muscles[j]["F"][:, [0, 2, 1]]
                    meshes[j] = trimesh.Trimesh(V[j], F, process=False)
                ins, d = _inside_depth(meshes[j], V[i][idx])
                new = ins & ~np.isin(idx, list(b._rest_in[(i, j)]))
                if new.any():
                    key = (b.muscles[i]["name"], b.muscles[j]["name"])
                    dm = float(d[new].max())
                    if dm > worst.get(key, (0,))[0]:
                        worst[key] = (dm, int(new.sum()), f, side)
    return worst


def run(motion, binding=None, stride=1, log=None, pen=True):
    """motion: dict motion.json. Trả về báo cáo dict."""
    b = binding or Binding()
    B = len(motion["bodies"])
    xf = dec(motion["xforms_f32"], "<f4").reshape(-1, B, 7).astype(float)
    sides = ["R"] if motion.get("mirror") else ["R", "L"]
    ph = np.array(motion.get("phase") or np.linspace(0, 1, len(xf)))
    # Gần tư thế bắt đầu thì gần như không biến dạng: kiểm thưa; phần còn lại kiểm dày.
    frames = sorted({f for f in range(len(xf)) if (ph[f] >= 0.25 and f % stride == 0) or f % (stride * 4) == 0}
                    | {int(np.argmax(ph)), len(xf) - 1})
    per = {}
    for n_, f in enumerate(frames):
        for side in sides:
            q0, qe = b.dq(motion["bodies"], xf[f], side)
            for m in b.muscles:
                V0 = m["V"] if side == "R" else m["V"] * MIRROR
                V = apply_dqs(V0, m["bi"], m["bw"], q0, qe)
                r = m["qa"][side].measure(V, V0)
                # Jacobian chỉ cần ở nửa sâu của động tác (nơi có nếp gấp); bên trái tra trường
                # trọng số của bên phải tại điểm đối xứng
                if ph[f] >= 0.5 and b.fields is not None:
                    jd = jacobian_det(b.fields.for_bones(m["bones"], mirror=side == "L"), V0, q0, qe)
                else:
                    jd = np.ones(1)
                neg = float((jd < 0).mean() * 100)
                c = per.setdefault(m["name"], {"flips": 0, "flip_t": 0.0, "edge_max": 0.0, "edge_t": 0.0,
                                               "jac_min": 9.0, "jac_neg_pct": 0.0, "jac_t": 0.0})
                if r["flip_faces"] > c["flips"]:
                    c.update(flips=r["flip_faces"], flip_t=motion["times"][f])
                if r["edge_max"] > c["edge_max"]:
                    c.update(edge_max=round(r["edge_max"], 2), edge_t=motion["times"][f])
                if neg > c["jac_neg_pct"] or (neg == c["jac_neg_pct"] and jd.min() < c["jac_min"]):
                    c.update(jac_neg_pct=round(neg, 2), jac_min=round(float(jd.min()), 2), jac_t=motion["times"][f])
        if log and n_ % 10 == 0:
            log(f"  kiểm tra hình học: {n_ + 1}/{len(frames)} khung")
    pens = {}
    if pen:
        if log:
            log("  kiểm tra xuyên giữa các cơ ở đáy động tác…")
        fb = int(np.argmax(ph))
        fm = int(np.argmin(np.abs(ph[:fb + 1] - 0.6)))
        pens = penetration(b, motion, sorted({fm, fb}), sides)
    issues = []

    def add(level, muscle, text):
        issues.append({"level": level, "muscle": muscle, "text": text})

    L = LIMITS
    for name, c in per.items():
        if c["flips"] > L["flip_fail"]:
            add("fail", name, f"{c['flips']} tam giác bị lật (gai/thủng) lúc {c['flip_t']:.2f} s")
        elif c["flips"] > L["flip_warn"]:
            add("warn", name, f"{c['flips']} tam giác nhỏ bị lật lúc {c['flip_t']:.2f} s")
        if c["edge_max"] > L["edge_fail"]:
            add("fail", name, f"bề mặt bị kéo dài x{c['edge_max']:.1f} (rách) lúc {c['edge_t']:.2f} s")
        elif c["edge_max"] > L["edge_warn"]:
            add("warn", name, f"bề mặt bị kéo dài x{c['edge_max']:.1f} lúc {c['edge_t']:.2f} s")
        if c["jac_neg_pct"] > L["jac_neg_fail"]:
            add("fail", name, f"{c['jac_neg_pct']:.1f}% thể tích cơ bị gập ngược lúc {c['jac_t']:.2f} s")
        elif c["jac_neg_pct"] > L["jac_neg_warn"]:
            add("warn", name, f"mô bị ép vào nhau ở nếp khớp ({c['jac_neg_pct']:.1f}% thể tích) lúc {c['jac_t']:.2f} s")
    for (a_, b_), (d, n, f, side) in sorted(pens.items(), key=lambda kv: -kv[1][0]):
        if d > L["pen_fail"]:
            add("fail", a_, f"xuyên vào {b_} sâu {d * 1000:.0f} mm lúc {motion['times'][f]:.2f} s")
        elif d > L["pen_warn"]:
            add("warn", a_, f"chạm/xuyên nhẹ vào {b_} ({d * 1000:.0f} mm) lúc {motion['times'][f]:.2f} s")
    status = "fail" if any(i["level"] == "fail" for i in issues) else "warn" if issues else "pass"
    worst_pen = max([v[0] for v in pens.values()], default=0.0)
    return {"status": status, "limits": LIMITS, "frames_checked": len(frames), "sides": sides,
            "summary": {"flips_max": max(c["flips"] for c in per.values()),
                        "edge_max": max(c["edge_max"] for c in per.values()),
                        "jac_neg_pct_max": max(c["jac_neg_pct"] for c in per.values()),
                        "penetration_max_mm": round(worst_pen * 1000, 1)},
            "issues": issues, "muscles": per}


def bindings():
    """Mọi vùng có hình cơ: thân dưới (+ thân trên nếu đã dựng)."""
    out = [Binding()]
    up = os.path.join(ASSETS, "zanat_upper.json")
    if os.path.exists(up):
        out.append(Binding(up, None))
    return out


def run_all(motion, binds=None, stride=1, log=None, pen=True):
    """Chạy run() cho từng vùng rồi gộp."""
    reps = [run(motion, b, stride=stride, log=log, pen=pen) for b in (binds or bindings())]
    issues = [i for r in reps for i in r["issues"]]
    status = "fail" if any(r["status"] == "fail" for r in reps) else "warn" if issues else "pass"
    summ = {k: max(r["summary"][k] for r in reps) for k in reps[0]["summary"]}
    muscles = {k: v for r in reps for k, v in r["muscles"].items()}
    return {"status": status, "limits": LIMITS, "frames_checked": reps[0]["frames_checked"], "sides": reps[0]["sides"],
            "summary": summ, "issues": issues, "muscles": muscles}


def print_report(slug, rep):
    sm = rep["summary"]
    print(f"[{rep['status'].upper()}] {slug}: {rep['frames_checked']} khung × {len(rep['sides'])} bên — "
          f"lật tối đa {sm['flips_max']}, kéo dài tối đa x{sm['edge_max']:.1f}, "
          f"gập ngược tối đa {sm['jac_neg_pct_max']:.1f}%, xuyên giữa cơ tối đa {sm['penetration_max_mm']:.1f} mm")
    for i in rep["issues"]:
        print(f"   {'LỖI ' if i['level'] == 'fail' else 'chú ý'}  {i['muscle']}: {i['text']}")


def selftest():
    """Chạy hàm biến dạng của viewer (JS, bằng Node) và so với bản Python."""
    import subprocess
    import tempfile
    b = Binding()
    rng = np.random.default_rng(1)
    K = len(b.names)
    rest = np.array([b.z["rest"][n] for n in b.names])
    ang = rng.normal(size=(K, 3)) * 0.8
    cur = rest.copy()
    from scipy.spatial.transform import Rotation as Rot
    for k in range(K):
        cur[k, 3:] = (Rot.from_rotvec(ang[k]) * Rot.from_quat(rest[k, 3:])).as_quat()
        cur[k, :3] += rng.normal(size=3) * 0.05
    m = b.muscles[0]
    q0, qe = skin_dq(rest, cur)
    ref = apply_dqs(m["V"], m["bi"], m["bw"], q0, qe)
    src = open(os.path.join(WEB_DIR, "anatomy-core.js"), encoding="utf-8").read()   # viewer & Studio dùng file này
    a, z = src.index("// <dqs>"), src.index("// </dqs>")
    js = src[a:z].replace("export function", "function") + f"""
const rest = {json.dumps(rest.tolist())}, cur = {json.dumps(cur.tolist())};
const V = new Float32Array({json.dumps(m['V'].ravel().tolist())});
const W = new Float32Array({json.dumps(m['bw'].ravel().tolist())});
const dq = new Float64Array(rest.length * 8);
for (let k = 0; k < rest.length; k++) skinDQ(rest[k], cur[k], dq, k * 8);
const out = new Float32Array(V.length);
dqsDeform(V, rest.length, W, dq, out, false);
process.stdout.write(JSON.stringify(Array.from(out)));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fp:
        fp.write(js)
    res = subprocess.run(["node", fp.name], capture_output=True, text=True, check=True)
    os.unlink(fp.name)
    got = np.array(json.loads(res.stdout)).reshape(-1, 3)
    err = np.abs(got - ref).max()
    print(f"selftest: sai khác lớn nhất giữa viewer (JS) và Python = {err * 1000:.4f} mm")
    assert err < 1e-4, "viewer và bản tham chiếu Python không khớp!"
    return err


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
        sys.exit(0)
    stride = int(args[args.index("--stride") + 1]) if "--stride" in args else 2
    if "--stride" in args:
        del args[args.index("--stride"):args.index("--stride") + 2]
    slugs = sorted(os.listdir(OUTPUT_DIR)) if "--all" in args else [a for a in args if not a.startswith("-")]
    bind = bindings()
    bad = 0
    for s in slugs:
        p = os.path.join(OUTPUT_DIR, s, "data", "motion.json")
        if not os.path.exists(p):
            continue
        rep = run_all(json.load(open(p, encoding="utf-8")), bind, stride=stride)
        print_report(s, rep)
        with open(os.path.join(OUTPUT_DIR, s, "qa.json"), "w", encoding="utf-8") as fp:
            json.dump(rep, fp, ensure_ascii=False, indent=1)
        bad += rep["status"] == "fail"
    sys.exit(1 if bad else 0)
