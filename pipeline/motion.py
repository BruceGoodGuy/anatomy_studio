"""Bước 1 — Từ file bài tập (JSON) tạo chuyển động cho mô hình OpenSim.

Một bài tập gồm vài TƯ THẾ THEN CHỐT (phase 0 = bắt đầu, phase 1 = điểm cuối của
động tác, ví dụ đáy squat). Chuyển động chạy 0 → 1 → 0 theo thời gian bạn đặt.

Hai kiểu bài:

* "standing" — đứng hai chân bám sàn (squat, RDL, good morning, sumo...).
  Bạn nhập: độ gập gối, độ nghiêng chậu, độ gập lưng, tay. Chương trình tự giải góc
  hông, cổ chân, độ dạng/xoay hông sao cho: gót cố định trên sàn, bàn chân phẳng,
  đúng độ rộng chân và góc mũi chân, và khối tâm luôn nằm trên giữa bàn chân.

* "free" — tự đặt từng khớp cho từng chân và tay (lunge, split squat, chống đẩy, kéo xà, đẩy ngực…).
  IK mềm: dời chậu (và nghiêng thân khi cả tay lẫn chân cùng neo), chỉnh nhẹ các khớp của chi được
  "neo" để chỗ neo đứng yên: chân neo phẳng / neo mũi / không neo; tay chống sàn / nắm cố định /
  không neo. Treo xà không chân chạm đất → khối tâm nằm dưới chỗ nắm. Không neo gì → chậu ở
  pelvis_height_cm (bài nằm, ngồi). Chi tiết: docs/03-pipeline-so-lieu.md.
"""
import json
import math

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares, minimize_scalar

from .common import Poser, load_model, TRANSLATIONS

FPS = 30

# Mô tả cột cho giao diện: (nhãn, min, max, mặc định, gợi ý)
COLUMNS = {
    "standing": {
        "knee_flexion": ("Gập gối", 0, 140, 0, "0 = duỗi thẳng. Đáy squat sâu khoảng 110–130."),
        "pelvis_anterior_tilt": ("Chậu nghiêng trước", -20, 90, 0, "Độ nghiêng của chậu so với phương thẳng đứng. RDL ở đáy khoảng 60–80."),
        "lumbar_flexion": ("Gập lưng dưới", -30, 60, 0, "0 = lưng trung tính, âm = ưỡn."),
    },
    "free": {
        "pelvis_anterior_tilt": ("Chậu nghiêng trước", -90, 90, 0, "So với phương thẳng đứng."),
        "lumbar_flexion": ("Gập lưng dưới", -30, 60, 0, ""),
        "hip_flexion_r": ("Gập hông (phải)", -30, 120, 0, "So với chậu. Âm = duỗi ra sau."),
        "hip_adduction_r": ("Khép hông (phải)", -50, 30, 0, "Âm = dạng chân ra ngoài."),
        "hip_rotation_r": ("Xoay trong hông (phải)", -40, 40, 0, "Âm = xoay ngoài."),
        "knee_flexion_r": ("Gập gối (phải)", 0, 140, 0, ""),
        "ankle_dorsiflexion_r": ("Gập mu cổ chân (phải)", -50, 50, 0, "Bị bỏ qua nếu bàn chân phải được neo phẳng và bật 'tự giải cổ chân'."),
        "hip_flexion_l": ("Gập hông (trái)", -30, 120, 0, ""),
        "hip_adduction_l": ("Khép hông (trái)", -50, 30, 0, ""),
        "hip_rotation_l": ("Xoay trong hông (trái)", -40, 40, 0, ""),
        "knee_flexion_l": ("Gập gối (trái)", 0, 140, 0, ""),
        "ankle_dorsiflexion_l": ("Gập mu cổ chân (trái)", -50, 50, 0, ""),
    },
}
# Tay: giống nhau hai bên, dùng cho cả hai kiểu bài. Không ảnh hưởng tới cơ chân, nhưng làm dáng
# tự nhiên hơn và (ở kiểu đứng) làm dời khối tâm một chút.
ARM_COLUMNS = {
    "arm_flexion": ("Tay đưa ra trước", -60, 180, 0, "Ở vai. 0 = buông xuôi, 90 = ngang vai, 180 = giơ thẳng qua đầu."),
    "arm_abduction": ("Dang tay ra ngang", -30, 170, 6, "Ở vai. 0 = sát thân, 90 = ngang vai, 170 = giơ qua đầu theo phía bên."),
    "arm_rotation": ("Xoay trong cánh tay", -90, 90, 0, "Dương = xoay vào trong (cẳng tay hướng vào ngực), âm = xoay ra ngoài."),
    "elbow_flexion": ("Gập khuỷu tay", 0, 150, 8, "0 = duỗi thẳng."),
    "forearm_rotation": ("Xoay cẳng tay", 0, 170, 85, "0 = ngửa lòng bàn tay (tư thế giải phẫu), 90 = trung tính (ngón cái ra trước), 170 = úp hẳn."),
}
for _cols in COLUMNS.values():
    _cols.update(ARM_COLUMNS)

# Nhóm cột trên giao diện (theo vùng cơ thể)
SECTIONS = [
    ("legs", "Chân", ["knee_flexion"]),
    ("trunk", "Thân & chậu", ["pelvis_anterior_tilt", "lumbar_flexion"]),
    ("leg_r", "Chân phải", ["hip_flexion_r", "hip_adduction_r", "hip_rotation_r", "knee_flexion_r", "ankle_dorsiflexion_r"]),
    ("leg_l", "Chân trái", ["hip_flexion_l", "hip_adduction_l", "hip_rotation_l", "knee_flexion_l", "ankle_dorsiflexion_l"]),
    ("arms", "Tay (hai bên giống nhau)", list(ARM_COLUMNS)),
]

# Tư thế tay mẫu (giải sẵn bằng cách đặt bàn tay vào vị trí đích trên mô hình)
ARM_PRESETS = {
    "hang":     ("Buông xuôi",              {"arm_flexion": 0,   "arm_abduction": 6,   "arm_rotation": 0,   "elbow_flexion": 8,   "forearm_rotation": 85}),
    "forward":  ("Duỗi ra trước",           {"arm_flexion": 85,  "arm_abduction": 0,   "arm_rotation": 0,   "elbow_flexion": 6,   "forearm_rotation": 160}),
    "goblet":   ("Ôm tạ trước ngực",        {"arm_flexion": 21,  "arm_abduction": -3,  "arm_rotation": 9,   "elbow_flexion": 111, "forearm_rotation": 70}),
    "cross":    ("Khoanh tay trước ngực",   {"arm_flexion": 49,  "arm_abduction": 2,   "arm_rotation": 67,  "elbow_flexion": 100, "forearm_rotation": 150}),
    "hips":     ("Chống hông",              {"arm_flexion": -20, "arm_abduction": 32,  "arm_rotation": 25,  "elbow_flexion": 95,  "forearm_rotation": 150}),
    "prisoner": ("Hai tay sau đầu",         {"arm_flexion": 2,   "arm_abduction": 120, "arm_rotation": -90, "elbow_flexion": 144, "forearm_rotation": 110}),
    "overhead": ("Giơ thẳng qua đầu",       {"arm_flexion": 175, "arm_abduction": 8,   "arm_rotation": 0,   "elbow_flexion": 0,   "forearm_rotation": 90}),
}


ARM_COLUMNS_L = {k + "_l": (lab + " (trái)", lo, hi, d, h) for k, (lab, lo, hi, d, h) in ARM_COLUMNS.items()}


def columns(ex):
    """Các cột của bài: theo kiểu bài, thêm cột tay trái khi chọn 'hai tay khác nhau'."""
    cols = dict(COLUMNS[ex["mode"]])
    if ex.get("options", {}).get("arms") == "separate":
        cols.update(ARM_COLUMNS_L)
    return cols


def arm_values(c, phase):
    """Toạ độ OpenSim của hai tay. Các cột tay chung = tay phải; tay trái dùng cột *_l nếu có."""
    v = {}
    for s in "rl":
        g = (lambda k: c.get(k + "_l", c[k])) if s == "l" else (lambda k: c[k])
        v[f"arm_flex_{s}"] = float(g("arm_flexion")(phase))
        v[f"arm_add_{s}"] = -float(g("arm_abduction")(phase))
        v[f"arm_rot_{s}"] = float(g("arm_rotation")(phase))
        v[f"elbow_flex_{s}"] = float(g("elbow_flexion")(phase))
        v[f"pro_sup_{s}"] = float(g("forearm_rotation")(phase))
    return v
OPTIONS = {
    "standing": {
        "stance_width_cm": ("Độ rộng hai gót (cm)", 10, 90, 30),
        "toe_out_deg": ("Mũi chân xoay ra (°)", -10, 45, 10),
        "arms": ("Hai tay", ["same", "separate"], "same"),
    },
    "free": {
        "anchor_r": ("Neo chân phải", ["flat", "toes", "none"], "flat"),
        "anchor_l": ("Neo chân trái", ["flat", "toes", "none"], "flat"),
        "auto_ankle": ("Tự giải cổ chân cho chân neo phẳng", [True, False], True),
        "anchor_hand_r": ("Neo tay phải", ["none", "floor", "bar"], "none"),
        "anchor_hand_l": ("Neo tay trái", ["none", "floor", "bar"], "none"),
        "arms": ("Hai tay", ["same", "separate"], "same"),
        "pelvis_height_cm": ("Độ cao hông khi không neo gì (cm)", 20, 130, 94),
    },
}
HAND_FLOOR_Y = 0.045     # tâm cổ tay cách sàn khi bàn tay úp phẳng xuống sàn (m)
DEFAULT_TIMING = {"hold": 0.3, "down": 2.0, "pause": 0.4, "up": 1.4}


def foot_angles(R):
    X = R[:, 0]
    pitch = math.degrees(math.atan2(X[1], math.hypot(X[0], X[2])))
    yaw = math.degrees(math.atan2(X[2], X[0]))
    return pitch, yaw


def validate(ex):
    errs = []
    mode = ex.get("mode")
    if mode not in COLUMNS:
        errs.append("Kiểu bài phải là 'standing' hoặc 'free'.")
        return errs
    kf = ex.get("keyframes", [])
    if len(kf) < 2:
        errs.append("Cần ít nhất 2 tư thế then chốt (phase 0 và phase 1).")
    phases = [float(k.get("phase", -1)) for k in kf]
    if sorted(phases) != phases or len(set(phases)) != len(phases):
        errs.append("Các phase phải tăng dần và không trùng nhau.")
    if phases and (phases[0] != 0 or phases[-1] != 1):
        errs.append("Tư thế đầu phải có phase = 0 và tư thế cuối phase = 1.")
    for k in kf:
        for col, (label, lo, hi, _, _) in columns(ex).items():
            v = k.get(col, None)
            if v is not None and not (lo <= float(v) <= hi):
                errs.append(f"Phase {k.get('phase')}: '{label}' = {v} nằm ngoài khoảng {lo}…{hi}.")
    return errs


def curves(ex):
    mode = ex["mode"]
    kf = ex["keyframes"]
    ph = np.array([float(k["phase"]) for k in kf])
    out = {}
    for col, (_, _, _, default, _) in columns(ex).items():
        if col.endswith("_l") and col in ARM_COLUMNS_L:   # tay trái chưa đặt riêng → lấy theo tay phải
            default_col = col[:-2]
            vals = np.array([float(k.get(col, k.get(default_col, ARM_COLUMNS[default_col][3]))) for k in kf])
            out[col] = PchipInterpolator(ph, vals)
            continue
        vals = np.array([float(k.get(col, default)) for k in kf])
        out[col] = PchipInterpolator(ph, vals)
    return out


def timeline(timing):
    t = {**DEFAULT_TIMING, **(timing or {})}
    ease = lambda u: 0.5 - 0.5 * math.cos(math.pi * u)
    segs = [(t["hold"], lambda u: 0.0), (t["down"], ease), (t["pause"], lambda u: 1.0),
            (t["up"], lambda u: 1.0 - ease(u)), (t["hold"], lambda u: 0.0)]
    total = sum(d for d, _ in segs)
    out = []
    for i in range(int(round(total * FPS)) + 1):
        tt, acc = i / FPS, 0.0
        for k, (d, fn) in enumerate(segs):
            if tt <= acc + d + 1e-9 or k == len(segs) - 1:
                out.append((tt, fn(0.0 if d == 0 else min(max((tt - acc) / d, 0.0), 1.0))))
                break
            acc += d
    return out


class MotionSolver:
    def __init__(self):
        self.model, self.state = load_model()
        for s_ in "rl":     # cổ tay khoá sẵn trong mô hình; mở để bàn tay úp phẳng khi chống xuống sàn
            self.model.getCoordinateSet().get(f"wrist_flex_{s_}").setLocked(self.state, False)
        self.poser = Poser(self.model, self.state)
        p = self.poser
        p.set({}, reset=True)
        self.heel0 = p.body_pos("calcn_r")
        self.toes0 = p.body_pos("toes_r")
        self.pitch0, self.yaw0 = foot_angles(p.body_R("calcn_r"))
        self.ty0 = p.values()["pelvis_ty"]

    # ---------------- standing ----------------
    def _standing_pose(self, c, phase, x, opts):
        hip, ankle, add, rot, tx, ty = x
        tilt = -float(c["pelvis_anterior_tilt"](phase))   # mô hình: + là nghiêng sau
        lumbar = -float(c["lumbar_flexion"](phase))       # mô hình: + là ưỡn
        knee = float(c["knee_flexion"](phase))
        v = {"pelvis_tilt": tilt, "pelvis_tx": tx, "pelvis_ty": ty, "lumbar_extension": lumbar}
        for s in "rl":
            v.update({f"hip_flexion_{s}": hip, f"hip_adduction_{s}": add, f"hip_rotation_{s}": rot,
                      f"knee_angle_{s}": knee, f"ankle_angle_{s}": ankle})
        v.update(arm_values(c, phase))
        return v

    def _solve_standing(self, c, phase, opts, x0):
        p = self.poser
        half_w = float(opts.get("stance_width_cm", 30)) / 200.0
        toe_out = float(opts.get("toe_out_deg", 10))

        def res(x):
            p.set(self._standing_pose(c, phase, x, opts))
            heel, toes = p.body_pos("calcn_r"), p.body_pos("toes_r")
            pitch, yaw = foot_angles(p.body_R("calcn_r"))
            return [(heel[0] - self.heel0[0]) * 100, (heel[1] - self.heel0[1]) * 100, (heel[2] - half_w) * 100,
                    (pitch - self.pitch0) / 2, (yaw - (self.yaw0 + toe_out)) / 2,
                    (p.com()[0] - 0.5 * (heel[0] + toes[0])) * 100]

        lo = [-30, -50, -50, -40, -1.0, 0.2]
        hi = [130, 50, 30, 40, 1.0, 1.3]
        x0 = np.clip(x0, np.array(lo) + 1e-6, np.array(hi) - 1e-6)
        sol = least_squares(res, x0, bounds=(lo, hi), xtol=1e-9, ftol=1e-9, max_nfev=400)
        vals = self._standing_pose(c, phase, sol.x, opts)
        p.set(vals)
        err_cm = float(np.max(np.abs(sol.fun[[0, 1, 2, 5]])))
        err_deg = float(np.max(np.abs(sol.fun[[3, 4]]))) * 2
        return vals, sol.x, {"err_cm": err_cm, "err_deg": err_deg}

    # ---------------- free ----------------
    # IK mềm: ẩn số = vị trí chậu (+ độ nghiêng chậu khi cả tay lẫn chân cùng neo, vd. chống đẩy)
    # + các khớp của chi được neo (chân: hông–gối–cổ chân; tay: gập & dang vai, cổ tay nếu chống sàn).
    # Ràng buộc neo có trọng số lớn; mỗi khớp bị "kéo" nhẹ về góc bạn đặt. Kết quả: chỗ neo đứng yên,
    # tư thế gần nhất có thể với tư thế bạn mô tả.
    LEG = ("hip_flexion", "knee_angle", "ankle_angle")
    ARM = ("arm_flex", "arm_add")
    W_ANCHOR, W_PRIOR = 10.0, 0.05
    W_FINGER = 1 / 40
    LIM = {"hip_flexion": (-30, 120), "knee_angle": (0, 140), "ankle_angle": (-70, 50),
           "arm_flex": (-60, 185), "arm_add": (-175, 40), "wrist_flex": (-90, 100)}

    def _free_base(self, c, phase):
        v = {"pelvis_tilt": -float(c["pelvis_anterior_tilt"](phase)),
             "lumbar_extension": -float(c["lumbar_flexion"](phase))}
        for s in "rl":
            v[f"hip_flexion_{s}"] = float(c[f"hip_flexion_{s}"](phase))
            v[f"hip_adduction_{s}"] = float(c[f"hip_adduction_{s}"](phase))
            v[f"hip_rotation_{s}"] = float(c[f"hip_rotation_{s}"](phase))
            v[f"knee_angle_{s}"] = float(c[f"knee_flexion_{s}"](phase))
            v[f"ankle_angle_{s}"] = float(c[f"ankle_dorsiflexion_{s}"](phase))
            v[f"wrist_flex_{s}"] = 0.0
        v.update(arm_values(c, phase))
        return v

    def _free_vars(self, opts):
        feet = [s for s in "rl" if opts.get(f"anchor_{s}", "flat") != "none"]
        hands = [s for s in "rl" if opts.get(f"anchor_hand_{s}", "none") != "none"]
        names = [f"{j}_{s}" for s in feet for j in self.LEG] + [f"{j}_{s}" for s in hands for j in self.ARM]
        tilt = bool(hands) and bool(feet)
        return feet, hands, names, tilt

    def _unpack(self, x, opts):
        feet, hands, names, tilt = self._free_vars(opts)
        k = 3 if tilt else 2
        return x[0], x[1], (x[2] if tilt else None), dict(zip(names, x[k:]))

    def _free_eval(self, c, phase, x, opts, ref, floor_only=False):
        p = self.poser
        feet, hands, names, tilt = self._free_vars(opts)
        base = self._free_base(c, phase)
        tx, ty, tl, joints = self._unpack(x, opts)
        v = dict(base)
        v["pelvis_tx"], v["pelvis_ty"] = (0.0 if floor_only else tx), ty
        if tl is not None:
            v["pelvis_tilt"] = tl
        v.update(joints)
        p.set(v)
        if self._wrist_on:
            self._place_wrists(v, hands, opts)
        r = []
        W = 100 * self.W_ANCHOR
        for s in feet:
            a = opts.get(f"anchor_{s}", "flat")
            pt = p.body_pos(f"calcn_{s}" if a == "flat" else f"toes_{s}")
            if not floor_only:
                r.append((pt[0] - ref[s][0]) * W)
            r.append((pt[1] - ref[s][1]) * W)
            if a == "flat" and opts.get("auto_ankle", True):
                r.append((foot_angles(p.body_R(f"calcn_{s}"))[0] - self.pitch0) * self.W_ANCHOR / 2)
        for s in hands:
            a = opts.get(f"anchor_hand_{s}")
            pt = p.body_pos(f"hand_{s}")
            if floor_only:
                if a == "floor":
                    r.append((pt[1] - HAND_FLOOR_Y) * W)
            else:
                key = "h" + s
                r += [(pt[0] - ref[key][0]) * W, (pt[1] - ref[key][1]) * W, (pt[2] - ref[key][2]) * W]
        if hands and not feet and not floor_only:
            # treo trên xà, không chân chạm đất: trọng tâm nằm ngay dưới chỗ nắm (cân bằng tĩnh)
            hx = np.mean([ref["h" + s][0] for s in hands])
            r.append((p.com()[0] - hx) * W * 0.5)
        for n, val in joints.items():
            flat_auto = n.startswith("ankle") and opts.get("auto_ankle", True) and opts.get(f"anchor_{n[-1]}", "flat") == "flat"
            # góc vai của tay được neo: để bộ giải tự quyết (chỉ kéo rất nhẹ về góc bạn đặt)
            w = self.W_PRIOR * (0.02 if flat_auto or n.startswith("wrist") else 0.2 if n.startswith("arm_") else 1.0)
            r.append((val - base[n]) * w)
        if tl is not None:
            # độ nghiêng thân do các điểm neo quyết định (vd. chống đẩy: thân xoay quanh mũi chân) → kéo rất nhẹ
            r.append((tl - base["pelvis_tilt"]) * self.W_PRIOR * 0.05)
        return v, r

    _wrist_on = False

    def _place_wrists(self, v, hands, opts):
        """Bàn tay chống sàn úp phẳng: chọn góc cổ tay để ngón tay nằm ngang (cổ tay không làm dời gốc bàn tay
        nên không ảnh hưởng chỗ neo — giải riêng, không kéo cả thân theo)."""
        p = self.poser
        for s in hands:
            if opts.get(f"anchor_hand_{s}") != "floor":
                continue
            def f(w):
                v[f"wrist_flex_{s}"] = w
                p.set(v)
                return abs((p.body_R(f"hand_{s}") @ np.array([0.0, -1.0, 0.0]))[1])
            # duỗi cổ tay (góc âm) để ngón tay hướng ra trước, bàn tay úp phẳng
            res = minimize_scalar(f, bounds=(-100, 30), method="bounded", options={"xatol": 0.5})
            f(float(res.x))

    def _final(self, c, phase, x, opts, ref, floor_only=False):
        self._wrist_on = True
        try:
            return self._free_eval(c, phase, x, opts, ref, floor_only)
        finally:
            self._wrist_on = False

    def _free_bounds(self, opts):
        feet, hands, names, tilt = self._free_vars(opts)
        lo = [-1.5, 0.05] + ([-100] if tilt else []) + [self.LIM[n[:-2]][0] for n in names]
        hi = [1.5, 2.4] + ([100] if tilt else []) + [self.LIM[n[:-2]][1] for n in names]
        return lo, hi

    def _free_x0(self, c, phase, opts, ty):
        feet, hands, names, tilt = self._free_vars(opts)
        base = self._free_base(c, phase)
        return np.array([0.0, ty] + ([base["pelvis_tilt"]] if tilt else []) + [base[n] for n in names])

    def free_reference(self, c, opts):
        """Chỗ neo ở tư thế phase 0: hạ chậu cho bàn chân neo (và bàn tay chống sàn) chạm sàn.
        Tay bám xà: chỗ neo là vị trí bàn tay ở tư thế phase 0."""
        feet, hands, names, tilt = self._free_vars(opts)
        if not feet and not hands:
            return None
        floor = {s: (self.heel0 if opts.get(f"anchor_{s}", "flat") == "flat" else self.toes0) for s in feet}
        lo, hi = self._free_bounds(opts)
        ty0 = self.ty0 if feet else float(opts.get("pelvis_height_cm", 94)) / 100
        x0 = np.clip(self._free_x0(c, 0.0, opts, ty0), np.array(lo) + 1e-6, np.array(hi) - 1e-6)
        if feet or any(opts.get(f"anchor_hand_{s}") == "floor" for s in hands):
            sol = least_squares(lambda x: self._free_eval(c, 0.0, x, opts, floor, floor_only=True)[1], x0,
                                bounds=(lo, hi), xtol=1e-8, ftol=1e-9, gtol=1e-9, max_nfev=150)
            x = sol.x
        else:
            x = x0
        self._final(c, 0.0, x, opts, floor, floor_only=True)
        ref = {s: self.poser.body_pos(f"calcn_{s}" if opts.get(f"anchor_{s}", "flat") == "flat" else f"toes_{s}")
               for s in feet}
        for s in hands:
            ref["h" + s] = self.poser.body_pos(f"hand_{s}")
        return {"ref": ref, "ty": float(x[1]), "x0": x}

    def _solve_free(self, c, phase, opts, x0, refinfo):
        feet, hands, names, tilt = self._free_vars(opts)
        if refinfo is None:
            v = self._free_base(c, phase)
            v["pelvis_tx"], v["pelvis_ty"] = 0.0, float(opts.get("pelvis_height_cm", 94)) / 100
            self.poser.set(v)
            return v, None, {"err_cm": 0.0, "err_deg": 0.0, "adjust_deg": 0.0}
        lo, hi = self._free_bounds(opts)
        if x0 is None or len(x0) != len(lo):
            x0 = self._free_x0(c, phase, opts, refinfo["ty"])
        x0 = np.clip(x0, np.array(lo) + 1e-6, np.array(hi) - 1e-6)
        sol = least_squares(lambda x: self._free_eval(c, phase, x, opts, refinfo["ref"])[1], x0,
                            bounds=(lo, hi), xtol=1e-8, ftol=1e-9, gtol=1e-9, max_nfev=150)
        v, r = self._final(c, phase, sol.x, opts, refinfo["ref"])
        base = self._free_base(c, phase)
        n_anchor = len(r) - len(names) - (1 if tilt else 0)
        err = float(np.max(np.abs(r[:n_anchor]))) / (100 * self.W_ANCHOR) * 100 if n_anchor else 0.0
        adj = {n: round(float(v[n] - base[n]), 1) for n in names
               if not ((n.startswith("ankle") and opts.get("auto_ankle", True) and opts.get(f"anchor_{n[-1]}", "flat") == "flat")
                       or n.startswith("arm_"))}
        return v, sol.x, {"err_cm": err, "err_deg": 0.0,
                          "adjust_deg": max([abs(a) for a in adj.values()] or [0.0]), "adjust": adj}

    # ---------------- public ----------------
    def pose(self, ex, phase, x0=None, refinfo=None):
        c = curves(ex)
        opts = ex.get("options", {})
        if ex["mode"] == "standing":
            if x0 is None:
                # đi dần từ phase 0 để lời giải bám đúng nhánh (tránh nghiệm vô lý)
                x0 = np.array([0, 0, 0, 0, 0, self.ty0], float)
                for ph in np.arange(0.0, phase, 0.1):
                    _, x0, _ = self._solve_standing(c, float(ph), opts, x0)
            vals, x, info = self._solve_standing(c, phase, opts, x0)
        else:
            if refinfo is None:
                refinfo = self.free_reference(c, opts)
            if x0 is None and refinfo is not None:
                x0 = refinfo["x0"]
                for ph in np.arange(0.0, phase, 0.1):
                    _, x0, _ = self._solve_free(c, float(ph), opts, x0, refinfo)
            vals, x, info = self._solve_free(c, phase, opts, x0, refinfo)
        return vals, x, info

    def build(self, ex, progress=None):
        """Trả về (times, [dict toạ độ đầy đủ], summary_rows, warnings)."""
        errs = validate(ex)
        if errs:
            raise ValueError("\n".join(errs))
        c = curves(ex)
        opts = ex.get("options", {})
        refinfo = self.free_reference(c, opts) if ex["mode"] == "free" else None
        tl = timeline(ex.get("timing"))
        cache, x, rows, summary, worst = {}, (refinfo or {}).get("x0"), [], [], (0.0, 0.0, 0.0)
        max_adj = (0.0, None, 0.0)
        # giải theo thứ tự phase tăng dần để lời giải trước làm điểm xuất phát
        for key in sorted({round(ph, 6) for _, ph in tl}):
            vals, x, info = self.pose(ex, key, x, refinfo)
            cache[key] = (self.poser.values(), info)
            for n, a in info.get("adjust", {}).items():
                if abs(a) > abs(max_adj[2]):
                    max_adj = (key, n, a)
            if info["err_cm"] > worst[0] or info["err_deg"] > worst[1]:
                worst = (max(worst[0], info["err_cm"]), max(worst[1], info["err_deg"]), key)
        for t, ph in tl:
            vals, info = cache[round(ph, 6)]
            rows.append((t, vals))
            summary.append({
                "time": round(t, 3), "phase": round(ph, 4),
                "knee_flexion_r": round(vals["knee_angle_r"], 1), "hip_flexion_r": round(vals["hip_flexion_r"], 1),
                "ankle_dorsiflexion_r": round(vals["ankle_angle_r"], 1),
                "knee_flexion_l": round(vals["knee_angle_l"], 1), "hip_flexion_l": round(vals["hip_flexion_l"], 1),
                "ankle_dorsiflexion_l": round(vals["ankle_angle_l"], 1),
                "trunk_lean": round(-vals["pelvis_tilt"] - vals["lumbar_extension"], 1),
                "pelvis_height_cm": round(vals["pelvis_ty"] * 100, 1),
                "foot_error_cm": round(info["err_cm"], 2),
            })
        warnings = []
        if worst[0] > 1.0:
            warnings.append(f"Ở phase {worst[2]:.2f}, bàn chân lệch {worst[0]:.1f} cm khỏi chỗ neo — các góc bạn đặt "
                            f"không khớp với nhau (ví dụ gập gối quá ít so với gập hông). Thử chỉnh lại tư thế đó.")
        if worst[1] > 3.0:
            warnings.append(f"Ở phase {worst[2]:.2f}, bàn chân không giữ được phẳng/đúng hướng (lệch {worst[1]:.0f}°).")
        if abs(max_adj[2]) > 8:
            warnings.append(f"Để giữ bàn chân neo đứng yên, '{max_adj[1]}' ở phase {max_adj[0]:.2f} phải chỉnh "
                            f"{max_adj[2]:+.0f}° so với góc bạn đặt. Nếu muốn đúng góc đó, chỉnh các khớp khác cho khớp với nhau.")
        ankles = [r["ankle_dorsiflexion_r"] for r in summary] + [r["ankle_dorsiflexion_l"] for r in summary]
        if max(ankles) > 45:
            warnings.append(f"Cổ chân phải gập mu tới {max(ankles):.0f}° — vượt mức đa số người làm được (~40–45°). "
                            "Tăng độ nghiêng chậu hoặc giảm độ gập gối.")
        return [t for t, _ in rows], [v for _, v in rows], summary, warnings


def write_mot(path, times, rows):
    names = list(rows[0].keys())
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"motion\nversion=1\nnRows={len(rows)}\nnColumns={len(names) + 1}\ninDegrees=yes\nendheader\n")
        f.write("time\t" + "\t".join(names) + "\n")
        for t, v in zip(times, rows):
            f.write(f"{t:.4f}\t" + "\t".join(f"{v[n]:.6f}" for n in names) + "\n")


def load_exercise(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
