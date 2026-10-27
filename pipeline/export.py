"""Bước 2 — Chạy chuyển động qua mô hình cơ-xương và xuất dữ liệu cho viewer.

Mỗi khung hình: vị trí + hướng từng xương, đường đi từng cơ (lấy mẫu lại thành số
điểm cố định) và chiều dài sợi cơ chuẩn hoá l/l_opt (1.0 = tối ưu, > 1 = bị kéo giãn).

Chiều dài sợi cơ tính ở trạng thái cân bằng của mô hình cơ Millard 2012 với GÂN ĐÀN HỒI và cơ
gần như thả lỏng (kích hoạt 1%): đúng tình huống "cơ bị kéo giãn thụ động". Gân dài (cơ dép,
bụng chân, đùi sau) tự nhận một phần độ dài khi lực căng thụ động tăng ở cuối biên độ.
Đã so với giả định gân cứng: thứ tự xếp hạng không đổi, giá trị cuối biên độ thấp hơn tới ~0.15.
"""
import base64

import numpy as np
import opensim as osim

from .common import Poser, load_model, body_names, MODEL_PATH
from .muscle_names import GROUPS, MUSCLES
from . import stretch

N_PTS = 14


def b64(arr):
    return base64.b64encode(np.ascontiguousarray(arr).tobytes()).decode("ascii")


def resample(points, n=N_PTS):
    pts = np.asarray(points)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    pts = pts[np.concatenate([[True], seg > 1e-6])]
    if len(pts) < 2:
        return np.repeat(pts[:1], n, axis=0)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    target = np.linspace(0, s[-1], n)
    return np.stack([np.interp(target, s, pts[:, k]) for k in range(3)], axis=1)


def muscle_polyline(muscle, state):
    pts = []
    cp = muscle.getGeometryPath().getCurrentPath(state)
    for i in range(cp.getSize()):
        pp = cp.get(i)
        pwp = osim.PathWrapPoint.safeDownCast(pp)
        if pwp is not None:
            wrap = pwp.getWrapPath(state)
            if wrap.getSize() > 0:
                frame = pwp.getParentFrame()
                for k in range(wrap.getSize()):
                    v = frame.findStationLocationInGround(state, wrap.get(k))
                    pts.append([v.get(0), v.get(1), v.get(2)])
                continue
        v = pp.getLocationInGround(state)
        pts.append([v.get(0), v.get(1), v.get(2)])
    return pts


def is_symmetric(rows):
    for n in rows[0]:
        if n.endswith("_r") and n[:-2] + "_l" in rows[0]:
            # bộ giải số cho hai bên lệch nhau cỡ phần trăm độ; cổ tay chống sàn được dò với bước 0.5°
            tol = 1.0 if n.startswith("wrist") else 0.05
            if any(abs(r[n] - r[n[:-2] + "_l"]) > tol for r in rows):
                return False
    return True


ACTIVATION = 0.01


def equilibrate(model, state, muscles):
    """Chiều dài sợi cơ cân bằng (gân đàn hồi, cơ thả lỏng) cho tư thế hiện tại."""
    for m in muscles:
        m.setActivation(state, ACTIVATION)
    model.equilibrateMuscles(state)
    model.realizeVelocity(state)


VIRTUAL = ["scapula_r", "clavicle_r", "scapula_l", "clavicle_l"]   # xương ảo thân trên (pipeline/zbind_upper.py)
GAP_FILL = 8          # lỗ số liệu (đường cơ quấn sai) ngắn hơn chừng này khung thì nội suy theo thời gian


def fill_gaps(x, max_gap=GAP_FILL):
    """Nội suy các đoạn NaN ngắn; trả về (mảng, số khung đã lấp, số khung còn thiếu)."""
    x = np.array(x, float)
    bad = ~np.isfinite(x)
    if not bad.any() or bad.all():
        return x, 0, int(bad.sum())
    filled = 0
    i, n = 0, len(x)
    while i < n:
        if bad[i]:
            j = i
            while j < n and bad[j]:
                j += 1
            if j - i <= max_gap and i > 0 and j < n:
                x[i:j] = np.interp(np.arange(i, j), [i - 1, j], [x[i - 1], x[j]])
                filled += j - i
            i = j
        else:
            i += 1
    return x, filled, int((~np.isfinite(x)).sum())


JUMP_M = 0.012      # chiều dài cơ-gân không thể nhảy 12 mm giữa hai khung liền nhau (≈ 3° khớp)
JUMP_SEG = 12       # đoạn "nhánh quấn sai" ngắn hơn chừng này khung thì loại


def branch_glitches(L):
    """Mặt quấn của MoBL-ARMS đôi khi đổi nhánh đột ngột (đường cơ bỏ quấn → đi tắt, ngắn hụt vài cm).
    Tìm các đoạn ngắn bị hụt so với hai bên và trả về mặt nạ khung cần loại + số chỗ nhảy còn lại."""
    L = np.asarray(L, float)
    bad = np.zeros(len(L), bool)
    for _ in range(6):
        x = np.where(bad, np.nan, L)
        idx = np.flatnonzero(np.isfinite(x))
        if len(idx) < 3:
            break
        d = np.diff(x[idx])
        cut = np.flatnonzero(np.abs(d) > JUMP_M)
        if not len(cut):
            return bad, 0
        bounds = [0] + list(cut + 1) + [len(idx)]
        segs = [(idx[bounds[k]], idx[bounds[k + 1] - 1], float(np.nanmean(x[idx[bounds[k]:bounds[k + 1]]])))
                for k in range(len(bounds) - 1)]
        changed = False
        for k, (i0, i1, lev) in enumerate(segs):
            if k == 0 or k == len(segs) - 1:      # đoạn ở hai đầu: không biết bên nào đúng → giữ, chỉ cảnh báo
                continue
            nb = [segs[k - 1][2], segs[k + 1][2]]
            if i1 - i0 + 1 <= JUMP_SEG and all(lev < v - JUMP_M for v in nb):
                bad[i0:i1 + 1] = True
                changed = True
        if not changed:
            return bad, len(cut)
    return bad, 0


class UpperExport:
    """Số liệu cơ thân trên + tư thế bả vai/xương đòn cho từng khung (pipeline/upper.py)."""

    def __init__(self, raj_model, raj_state):
        from .upper import UpperLimb, SHOWN
        self.U, self.names = UpperLimb(), SHOWN
        p = Poser(raj_model, raj_state)
        p.set({}, reset=True)
        T0 = np.array(p.body_xforms(["torso"]))[0]
        R0 = _quat_R(T0[3:])
        self.gh = {}
        for s in "rl":
            h = p.body_pos(f"humerus_{s}")
            self.gh[s] = R0.T @ (h - T0[:3])                  # tâm khớp vai trong hệ trục thân
        # tư thế nghỉ của bả vai / xương đòn trong MoBL (tay buông, mọi góc = 0)
        u = self.U
        u.evaluate({k: 0.0 for k in ["arm_flex_r", "arm_add_r", "arm_rot_r", "elbow_flex_r", "pro_sup_r"]}, "r")
        self.rest = {b: u._body_in_torso(b, "r") for b in ("scapula", "clavicle")}

    @staticmethod
    def _rot(M):
        R = M[:3, :3]
        return R / np.cbrt(np.linalg.det(R))

    def frame(self, vals, torso7, sides):
        """→ ({id: nfl}, {id: mtu}, {id: path_world}, {body: xf7}, ghi chú)."""
        T = np.eye(4)
        T[:3, :3], T[:3, 3] = _quat_R(torso7[3:]), torso7[:3]
        nfl, mtu, paths, xf, notes = {}, {}, {}, {}, {"wrap_bad": set(), "rom": set(), "fit": 0.0}
        F = np.diag([1.0, 1.0, -1.0])
        for s in ("r", "l"):
            if s not in sides and "r" in sides and s == "l":
                o = self._last_r      # bài đối xứng: bên trái = đối xứng của bên phải
                mirror = True
            else:
                o = self.U.evaluate(vals, s, want_paths=True)
                mirror = False
                if s == "r":
                    self._last_r = o
                for k, n in enumerate(self.names):
                    nfl[f"{n}_{s}"], mtu[f"{n}_{s}"] = o["nfl"][k], o["mtu"][k]
                    paths[f"{n}_{s}"] = o["paths_torso"][k] @ T[:3, :3].T + T[:3, 3]
                notes["wrap_bad"].update(o["wrap_bad"])
                notes["rom"].update(o["out_of_rom"])
                notes["fit"] = max(notes["fit"], o["fit_err_deg"])
            # bả vai xoay quanh tâm khớp vai, xương đòn quanh khớp ức–đòn (giữ khớp không bị hở)
            for body, pivot in (("scapula", self.gh["r"]), ("clavicle", self.rest["clavicle"][:3, 3])):
                Rd = self._rot(o[body]) @ self._rot(self.rest[body]).T
                c = np.array(pivot, float)
                if s == "l":
                    Rd = F @ Rd @ F
                    c = self.gh["l"] if body == "scapula" else F @ c
                X = np.eye(4)
                X[:3, :3], X[:3, 3] = Rd, c - Rd @ c
                W = T @ X
                xf[f"{body}_{s}"] = list(W[:3, 3]) + list(_R_quat(W[:3, :3]))
        return nfl, mtu, paths, xf, notes


def _quat_R(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _R_quat(R):
    from .skin import mat_to_quat
    return [float(v) for v in mat_to_quat(R)]


class Exporter:
    def __init__(self):
        self.model, self.state = load_model(rigid_tendons=False)
        self.poser = Poser(self.model, self.state)
        self.bodies = body_names(self.model)
        self.all_muscles = [self.model.getMuscles().get(i) for i in range(self.model.getMuscles().getSize())]
        self.upper = UpperExport(*load_model())

    def run(self, times, rows, meta):
        mirror = is_symmetric(rows)
        sides = ["r"] if mirror else ["r", "l"]
        muscles = [m for m in self.all_muscles if m.getName().endswith("_r")] if mirror else self.all_muscles
        up_ids = [f"{n}_{s}" for s in sides for n in self.upper.names]
        bodies = self.bodies + VIRTUAL
        n_f, n_m, n_u, n_b = len(rows), len(muscles), len(up_ids), len(bodies)
        paths = np.zeros((n_f, n_m + n_u, N_PTS, 3), np.float32)
        nfl = np.full((n_f, n_m + n_u), np.nan, np.float64)
        mtu = np.full((n_f, n_m + n_u), np.nan, np.float64)
        xforms = np.zeros((n_f, n_b, 7), np.float32)
        angles, notes = [], {"wrap_bad": set(), "rom": set(), "fit": 0.0}
        ti = self.bodies.index("torso")
        for f, vals in enumerate(rows):
            self.poser.set(vals)
            equilibrate(self.model, self.state, self.all_muscles)
            for j, m in enumerate(muscles):
                paths[f, j] = resample(muscle_polyline(m, self.state))
                nfl[f, j] = m.getNormalizedFiberLength(self.state)
                mtu[f, j] = m.getLength(self.state)
            body_xf = np.array(self.poser.body_xforms(self.bodies))
            xforms[f, :len(self.bodies)] = body_xf
            un, ul, up, uxf, nt = self.upper.frame(vals, body_xf[ti], sides)
            for k, uid in enumerate(up_ids):
                nfl[f, n_m + k], mtu[f, n_m + k] = un[uid], ul[uid]
                paths[f, n_m + k] = up[uid]
            for k, b in enumerate(VIRTUAL):
                xforms[f, len(self.bodies) + k] = uxf[b]
            notes["wrap_bad"] |= nt["wrap_bad"]
            notes["rom"] |= nt["rom"]
            notes["fit"] = max(notes["fit"], nt["fit"])
            angles.append([round(float(times[f]), 3),
                           round(vals["knee_angle_r"], 1), round(vals["hip_flexion_r"], 1), round(vals["ankle_angle_r"], 1),
                           round(-vals["pelvis_tilt"] - vals["lumbar_extension"], 1),
                           round(vals["knee_angle_l"], 1), round(vals["hip_flexion_l"], 1), round(vals["ankle_angle_l"], 1)])

        # lấp lỗ số liệu ngắn (đường cơ thân trên quấn sai ở vài khung)
        gaps, jumpy = {}, set()
        for j in range(n_m, n_m + n_u):
            badj, left = branch_glitches(mtu[:, j])
            nfl[badj, j] = np.nan
            mtu[badj, j] = np.nan
            if left:
                jumpy.add(up_ids[j - n_m])
            nfl[:, j], filled, missing = fill_gaps(nfl[:, j])
            mtu[:, j], _, _ = fill_gaps(mtu[:, j])
            if filled or missing:
                gaps[up_ids[j - n_m]] = (filled, missing)

        t = np.asarray(times)
        meta_mus, summary = [], []
        all_list = [(m.getName(), m) for m in muscles] + [(uid, None) for uid in up_ids]
        up_params = {mu.getName(): mu for mu in self.upper.U.muscles}
        for j, (name, m) in enumerate(all_list):
            base, side = name[:-2], name[-1]
            vi, latin, group = MUSCLES.get(base, (base, base, "other"))
            if not mirror:
                vi += " (phải)" if side == "r" else " (trái)"
            src = m if m is not None else up_params[base]
            st = stretch.summarize(nfl[:, j])
            k = st["argmax"]
            series = nfl[:, j]
            ok = np.isfinite(series)
            mt = mtu[:, j]
            meta_mus.append({"id": name, "base": base, "side": side, "vi": vi, "latin": latin, "group": group,
                             "region": "lower" if m is not None else "upper",
                             "fmax": round(src.getMaxIsometricForce(), 1), "lopt": round(src.getOptimalFiberLength(), 4),
                             "lts": round(src.getTendonSlackLength(), 4)})
            if st["start"] is None:
                summary.append({"id": name, "nfl_start": None, "nfl_max": None, "nfl_min": None, "t_max": 0.0,
                                "fiber_change_pct": 0.0, "mtu_change_pct": 0.0, "beyond_opt": 0.0, "stretched": False,
                                "valid_pct": 0.0})
                continue
            m0 = mt[np.argmax(np.isfinite(mt))]
            summary.append({"id": name, "nfl_start": round(st["start"], 3), "nfl_max": round(st["max"], 3),
                            "nfl_min": round(float(np.nanmin(series)), 3), "t_max": round(float(t[k]), 3),
                            "fiber_change_pct": round(float(st["change"] * 100), 1),
                            "mtu_change_pct": round(float((np.nanmax(mt) / m0 - 1) * 100), 1),
                            "beyond_opt": round(st["beyond"], 3), "stretched": st["stretched"],
                            "valid_pct": round(st["valid_pct"], 1)})
        warn = []
        missing = {k: v[1] for k, v in gaps.items() if v[1]}
        if missing:
            names = sorted({MUSCLES.get(k[:-2], (k,))[0] for k in missing})
            warn.append("Ở một số tư thế, đường cơ của " + ", ".join(names) + " trong mô hình MoBL-ARMS quấn sai quanh "
                        "xương (lỗi đã biết ở tư thế cực đoan): số liệu các khung đó bị loại, cơ hiện màu xám.")
        if jumpy:
            names = sorted({MUSCLES.get(k[:-2], (k,))[0] for k in jumpy})
            warn.append("Đường cơ của " + ", ".join(names) + " trong MoBL-ARMS đổi cách quấn quanh xương đột ngột ở một "
                        "đoạn của động tác (chiều dài nhảy > 1 cm giữa hai khung): số liệu quanh chỗ đó kém tin cậy.")
        if notes["rom"]:
            warn.append("Tay đi ra ngoài vùng tư thế mô hình MoBL-ARMS đã kiểm chứng (" +
                        ", ".join({"shoulder_rot": "xoay trong vai > 20°", "elv_angle": "mặt phẳng nâng tay",
                                   "shoulder_elv": "độ nâng tay"}[r] for r in sorted(notes["rom"])) +
                        "): số liệu cơ vai ở đoạn đó kém tin cậy hơn.")
        enc = np.where(np.isfinite(nfl), np.round(nfl * 10000), 0).clip(0, 65535)
        return {
            "title": meta.get("name", "Bài tập"),
            "category": meta.get("category", ""),
            "notes": meta.get("notes", ""),
            "model": {"name": MODEL_PATH.split("/")[-1].split("\\")[-1],
                      "upper": "MoBL-ARMS (Saul et al. 2015; Holzbaur et al. 2005), Millard 2012 muscles",
                      "citation": "Rajagopal et al. 2016 (IEEE TBME); Lai et al. 2017 (Ann Biomed Eng); Uhlrich et al. 2022 (Sci Rep); "
                                  "Saul et al. 2015 (Comput Methods Biomech Biomed Engin)",
                      "assumption": "compliant tendon, passive equilibrium (activation 0.01); kinematics only"},
            "fps": round(1.0 / float(t[1] - t[0]), 3),
            "times": [round(float(x), 4) for x in t],
            "mirror": mirror,
            "nPts": N_PTS,
            "groups": GROUPS,
            "bodies": bodies,
            "muscles": meta_mus,
            "summary": summary,
            "upper_notes": {"gaps": {k: list(v) for k, v in gaps.items()}, "rom": sorted(notes["rom"]),
                            "fit_err_deg_max": round(notes["fit"], 1)},
            "upper_warnings": warn,
            "angles": {"columns": ["time", "knee_r", "hip_r", "ankle_r", "trunk", "knee_l", "hip_l", "ankle_l"], "rows": angles},
            "paths_mm_i16": b64(np.round(np.nan_to_num(paths) * 1000).astype("<i2")),
            "nfl_u16": b64(enc.astype("<u2")),
            "xforms_f32": b64(xforms.astype("<f4")),
        }
