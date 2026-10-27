"""Cơ thân trên: ghép mô hình cơ tay–vai MoBL-ARMS vào bộ xương toàn thân Rajagopal.

Vì sao hai mô hình: mô hình toàn thân (Rajagopal–Lai–Uhlrich) chỉ có cơ thân dưới; tay của nó
được điều khiển bằng mô-men, không có cơ. MoBL-ARMS (Saul et al. 2015, dựa trên Holzbaur et al.
2005) là mô hình cơ tay–vai chuẩn của OpenSim: 50 cơ (delta, ngực lớn, lưng xô, chóp xoay, nhị đầu,
tam đầu, cơ cẳng tay…) và xương bả vai/xương đòn chuyển động theo cánh tay (nhịp vai–cánh tay).

Cách ghép, cho từng tay ở từng khung hình:
  1. Từ tư thế toàn thân, lấy hướng xương cánh tay trong hệ trục của THÂN: trục dọc cánh tay
     (vai → khuỷu) và trục gập khuỷu. Hai hướng này xác định đầy đủ tư thế cánh tay so với thân,
     không phụ thuộc quy ước góc riêng của từng mô hình.
  2. Giải 3 góc vai của MoBL (mặt phẳng nâng, độ nâng, xoay trục) sao cho hai hướng đó trùng nhau.
     Gập khuỷu lấy nguyên (MoBL tối đa 130°); xoay cẳng tay đổi thang: MoBL pro_sup = Rajagopal − 90
     (Rajagopal 0 = ngửa hẳn, 90 = trung tính; MoBL −90 = ngửa hẳn). Gập/nghiêng cổ tay lấy nguyên
     (wrist_flex → flexion, wrist_dev → deviation; dương = gập về phía lòng bàn tay).
  3. Đặt MoBL vào tư thế đó, tính chiều dài sợi cơ ở trạng thái cân bằng (gân đàn hồi, cơ thả lỏng)
     giống hệt cách làm với cơ chân.
Tay trái: lấy đối xứng qua mặt phẳng giữa thân rồi dùng chính mô hình tay phải.

Căn hệ trục (chỉ ảnh hưởng HÌNH VẼ đường cơ, không ảnh hưởng số liệu), lưu trong assets/upper_align.json:
  * mobl_to_torso: ICP có co giãn đều (chặn 0.8–1.25) lồng ngực + bả vai + xương đòn MoBL (ở tư thế khớp
    tư thế nghỉ Rajagopal) lên đúng các xương Z-Anatomy đang hiển thị (assets/zanat_upper.json).
  * segments: mỗi đoạn tay MoBL (cánh tay, trụ, quay, cổ tay, bàn tay) → xương Rajagopal tương ứng; điểm của
    đường cơ đi theo xương nó bám (to_torso). Xoá file này để tính lại (cần zanat_upper.json đã có).
"""
import json
import math
import os

import numpy as np
import opensim as osim
from scipy.optimize import least_squares

from .common import ASSETS, GEOMETRY_DIR, Poser, load_model

MOBL_PATH = os.path.join(ASSETS, "model", "MoBL_ARMS_millard.osim")   # tools/mobl_to_millard.py
MOBL_GEOMETRY = os.path.join(ASSETS, "model", "GeometryMoBL")
ALIGN_PATH = os.path.join(ASSETS, "upper_align.json")
ACTIVATION = 0.01
MIR = np.diag([1.0, 1.0, -1.0])

# Cơ MoBL được hiển thị / tính (bỏ các cơ ngón tay, cổ tay nhỏ: không cần cho bài tập thân trên)
SHOWN = ["DELT1", "DELT2", "DELT3", "SUPSP", "INFSP", "SUBSC", "TMIN", "TMAJ", "PECM1", "PECM2", "PECM3",
         "LAT1", "LAT2", "LAT3", "CORB", "TRIlong", "TRIlat", "TRImed", "ANC", "SUP", "BIClong", "BICshort",
         "BRA", "BRD", "ECRL", "ECRB", "ECU", "FCR", "FCU", "PL", "PT", "PQ", "FDSM", "FDPM", "EDCM"]
# Vùng tư thế MoBL-ARMS đã kiểm chứng (Holzbaur 2005; Saul 2015). Ngoài vùng này vẫn tính, nhưng báo.
ROM = {"elv_angle": (-90, 130), "shoulder_elv": (0, 180), "shoulder_rot": (-90, 20)}
# Đường cơ quấn sai quanh mặt trụ/elip (lỗi đã biết của mô hình ở vài tư thế cực đoan): quấn đúng chỉ làm
# đường cơ dài hơn đường thẳng qua các điểm bám/điểm uốn tối đa ~1.4 lần; quấn sai dài gấp 2.8–14 lần.
WRAP_RATIO_MAX = 1.6


def _mat(X):
    R = X.R()
    M = np.eye(4)
    M[:3, :3] = [[R.get(i, j) for j in range(3)] for i in range(3)]
    M[:3, 3] = [X.p().get(i) for i in range(3)]
    return M


def _icp_similarity(src, dst, M0, iters=80, scale_bounds=(0.8, 1.25)):
    """ICP hai chiều (điểm gần nhất cả hai phía, bỏ 10% cặp xa nhất), nghiệm Umeyama có co giãn đều bị chặn."""
    from scipy.spatial import cKDTree
    td, M = cKDTree(dst), M0.copy()
    for _ in range(iters):
        S = src @ M[:3, :3].T + M[:3, 3]
        d1, i1 = td.query(S)
        d2, i2 = cKDTree(S).query(dst)
        A = np.r_[src, src[i2]]
        B = np.r_[dst[i1], dst]
        d = np.r_[d1, d2]
        keep = d <= np.quantile(d, 0.9)
        A, B = A[keep], B[keep]
        ma, mb = A.mean(0), B.mean(0)
        H = (A - ma).T @ (B - mb) / len(A)
        U_, sig, Vt = np.linalg.svd(H)
        D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U_.T))])
        R = Vt.T @ D @ U_.T
        sc = np.clip(np.trace(np.diag(sig) @ D) / ((A - ma) ** 2).sum(1).mean(), *scale_bounds)
        Mn = np.eye(4)
        Mn[:3, :3], Mn[:3, 3] = sc * R, mb - sc * R @ ma
        if np.abs(Mn - M).max() < 1e-7:
            M = Mn
            break
        M = Mn
    S = src @ M[:3, :3].T + M[:3, 3]
    return M, float(np.mean(td.query(S)[0]) * 1000)


class _Arm:
    """Một mô hình + các hằng số hình học của cánh tay phải trong hệ trục xương cánh tay."""

    def __init__(self, model, state, thorax, humerus, forearm, elbow_coord, hand):
        self.m, self.s, self.p = model, state, Poser(model, state)
        self.thorax, self.humerus, self.forearm, self.elbow, self.hand = thorax, humerus, forearm, elbow_coord, hand
        B = model.getBodySet()
        self.B = B

    def frame(self, body):
        return _mat(self.B.get(body).getTransformInGround(self.s))

    def thorax_frame(self):
        return np.eye(4) if self.thorax is None else self.frame(self.thorax)

    def local_axes(self, base):
        """Trục dọc cánh tay và trục gập khuỷu, trong hệ trục xương cánh tay (hằng số)."""
        self.p.set({**base, self.elbow: 0.0}, reset=True)
        H = self.frame(self.humerus)
        Hi = np.linalg.inv(H)
        elbow = (Hi @ np.r_[self.frame(self.forearm)[:3, 3], 1])[:3]
        shoulder = np.zeros(3)
        u = (elbow - shoulder) / np.linalg.norm(elbow - shoulder)
        self.p.set({**base, self.elbow: 90.0}, reset=True)
        H2 = self.frame(self.humerus)
        F = self.frame(self.forearm)
        # hướng cẳng tay ở khuỷu 90°: dùng trục dài cẳng tay = từ khuỷu tới cổ tay (gốc bàn tay)
        wrist = self.frame(self.hand)[:3, 3]
        f = np.linalg.inv(H2)[:3, :3] @ (wrist - F[:3, 3])
        f -= u * (f @ u)
        f /= np.linalg.norm(f)
        e = np.cross(u, f)
        self.u_local, self.e_local, self.f_local = u, e / np.linalg.norm(e), f

    def dirs(self):
        """(u, f) của cánh tay hiện tại trong hệ trục thân."""
        T = self.thorax_frame()
        R = T[:3, :3].T @ self.frame(self.humerus)[:3, :3]
        return R @ self.u_local, R @ self.f_local


class UpperLimb:
    def __init__(self):
        osim.Logger.setLevelString("error")
        osim.ModelVisualizer.addDirToGeometrySearchPaths(MOBL_GEOMETRY)
        m = osim.Model(MOBL_PATH)
        s = m.initSystem()
        self.mobl = _Arm(m, s, None, "humerus", "ulna", "elbow_flexion", "hand")
        self.mobl.local_axes({})
        rm, rs = load_model()
        self.raj = _Arm(rm, rs, "torso", "humerus_r", "ulna_r", "elbow_flex_r", "hand_r")
        self.raj.local_axes({})
        M = m.getMuscles()
        self.muscles = [M.get(n) for n in SHOWN]
        self.align = self._alignment()
        self.seg = self._segments()
        self._x = {"r": np.array([0.0, 5.0, 0.0]), "l": np.array([0.0, 5.0, 0.0])}

    # ------------------------------------------------------------ căn hệ trục
    def _alignment(self):
        """MoBL ground → hệ trục thân Rajagopal: ICP (có co giãn đều) lồng ngực + bả vai + xương đòn của MoBL (ở tư thế
        khớp với tư thế nghỉ Rajagopal) lên đúng các xương Z-Anatomy đang hiển thị."""
        data = json.load(open(ALIGN_PATH)) if os.path.exists(ALIGN_PATH) else {}
        if data.get("version") == 2:
            return np.array(data["mobl_to_torso"])
        import base64
        import trimesh
        zb = json.load(open(os.path.join(ASSETS, "zanat_upper.json"), encoding="utf-8"))
        dec = lambda b: np.frombuffer(base64.b64decode(b["v"]), "<f4").reshape(-1, 3).astype(float)  # noqa: E731
        Z = {b["body"]: dec(b) for b in zb["bones"]}
        rng = np.random.default_rng(1)
        pick = lambda P, n: P[rng.choice(len(P), min(n, len(P)), replace=False)]  # noqa: E731
        dst = np.concatenate([pick(Z["torso"], 3000), pick(Z["scapula_r"], 1500), pick(Z["clavicle_r"], 600)])
        # MoBL ở tư thế khớp tư thế nghỉ Rajagopal
        u_t, f_t = self.raj_dirs({k: 0.0 for k in ["arm_flex_r", "arm_add_r", "arm_rot_r", "elbow_flex_r", "pro_sup_r"]}, "r")
        A0 = np.eye(4)
        self.align = A0
        x, _ = self.fit(u_t, f_t, np.array([0.0, 5.0, 0.0]))
        self.mobl.p.set({"elv_angle": x[0], "shoulder_elv": x[1], "shoulder_rot": x[2]}, reset=True)
        self.mobl.m.assemble(self.mobl.s)
        def ground(b):
            P = self._body_mesh_points(self.mobl.m, self.mobl.s, b)
            X = self.mobl.frame(b)
            return P @ X[:3, :3].T + X[:3, 3]
        from .geometry import read_vtp
        thor = read_vtp(os.path.join(MOBL_GEOMETRY, "thorax.vtp"))[0]
        src = np.concatenate([pick(thor, 3000), pick(ground("scapula"), 1500), pick(ground("clavicle"), 600)])
        # điểm xuất phát: căn cũ (chỉ lồng ngực) nếu có
        M0 = np.eye(4)
        M0[:3, :3] *= 0.86
        M0[:3, 3] = dst.mean(0) - 0.86 * src.mean(0)
        M, cost = _icp_similarity(src, dst, M0)
        data.update({"version": 2, "mobl_to_torso": M.tolist(), "icp_cost_mm": round(cost, 2)})
        data.pop("segments", None)
        json.dump(data, open(ALIGN_PATH, "w"), indent=1)
        return M

    # Mỗi đoạn tay của MoBL-ARMS (cánh tay, xương trụ, xương quay, cổ–bàn tay) có kích thước và gốc toạ độ hơi khác
    # xương Rajagopal mà hình cơ Z-Anatomy được dựng theo. Để đường cơ MoBL nằm đúng trên xương đang hiển thị, mỗi
    # điểm của đường cơ được chuyển theo xương nó bám: toạ độ trong xương MoBL → (ICP xương MoBL lên xương Rajagopal,
    # có co giãn đều) → xương Rajagopal ở tư thế hiện tại. Chỉ ảnh hưởng hình vẽ, không ảnh hưởng số liệu cơ.
    SEG = {"humerus": ("humerus_r", None), "ulna": ("ulna_r", None), "radius": ("radius_r", None),
           "proximal_row": ("hand_r", ("lunate", "scaphoid", "triquetrum", "pisiform")), "hand": ("hand_r", None)}
    SEG_ALIAS = {"humphant": "humerus", "humphant1": "humerus"}

    @staticmethod
    def _body_mesh_points(model, state, body, only=None):
        from .geometry import read_vtp
        Xb = np.linalg.inv(_mat(model.getBodySet().get(body).getTransformInGround(state)))
        pts = []
        for c in model.getComponentsList():
            if c.getConcreteClassName() != "Mesh":
                continue
            g = osim.Mesh.safeDownCast(c)
            f = g.getFrame()
            if f.findBaseFrame().getName() != body:
                continue
            fn = g.get_mesh_file()
            if only and not any(o in fn.lower() for o in only):
                continue
            for d in (MOBL_GEOMETRY, GEOMETRY_DIR):
                if os.path.exists(os.path.join(d, fn)):
                    V = read_vtp(os.path.join(d, fn))[0]
                    break
            else:
                continue
            sf = g.get_scale_factors()
            V = V * np.array([sf.get(0), sf.get(1), sf.get(2)])
            Xf = _mat(f.getTransformInGround(state))
            pts.append((Xb @ Xf @ np.c_[V, np.ones(len(V))].T).T[:, :3])
        return np.concatenate(pts)

    def _segments(self):
        data = json.load(open(ALIGN_PATH)) if os.path.exists(ALIGN_PATH) else {}
        if "segments" in data:
            return {k: np.array(v) for k, v in data["segments"].items()}
        import trimesh
        self.mobl.p.set({}, reset=True)
        self.raj.p.set({}, reset=True)
        out, cost = {}, {}
        for mb, (rb, only) in self.SEG.items():
            src = self._body_mesh_points(self.mobl.m, self.mobl.s, mb)
            dst = self._body_mesh_points(self.raj.m, self.raj.s, rb, only)
            rng = np.random.default_rng(0)
            src = src[rng.choice(len(src), min(len(src), 4000), replace=False)]
            M0 = np.eye(4)
            M0[:3, 3] = dst.mean(0) - src.mean(0)
            # xương dài: co giãn đều; khối cổ–bàn tay (nhiều xương nhỏ, hình khác nhau): giữ nguyên kích thước
            M, _, c = trimesh.registration.icp(src, dst, initial=M0, threshold=1e-9, max_iterations=200,
                                               reflection=False, translation=True, scale=mb not in ("proximal_row", "hand"))
            out[mb], cost[mb] = M, float(c) * 1000
        data["segments"] = {k: v.tolist() for k, v in out.items()}
        data["segments_icp_cost_mm"] = cost
        json.dump(data, open(ALIGN_PATH, "w"), indent=1)
        return out

    def to_torso(self, pg, body):
        """Một điểm (toạ độ ground của MoBL) → hệ trục thân Rajagopal, bám theo xương của nó (xem SEG)."""
        b = self.SEG_ALIAS.get(body, body)
        if b in self.seg:
            loc = np.linalg.inv(self.mobl.frame(b)) @ np.r_[pg, 1.0]
            T = np.linalg.inv(self.raj.thorax_frame()) @ self.raj.frame(self.SEG[b][0]) @ self.seg[b]
            return (T @ loc)[:3]
        return pg @ self.align[:3, :3].T + self.align[:3, 3]

    def current_path(self, mu):
        """[(điểm ground MoBL, thân MoBL)] của đường cơ ở tư thế hiện tại, gồm cả các điểm trên mặt quấn."""
        s = self.mobl.s
        cp = mu.getGeometryPath().getCurrentPath(s)
        out = []
        for i in range(cp.getSize()):
            q = cp.get(i)
            body = q.getParentFrame().findBaseFrame().getName()
            pw = osim.PathWrapPoint.safeDownCast(q)
            if pw is not None:
                wp = pw.getWrapPath(s)
                fr = pw.getParentFrame()
                for k in range(wp.getSize()):
                    v = fr.findStationLocationInGround(s, wp.get(k))
                    out.append((np.array([v.get(0), v.get(1), v.get(2)]), body))
            else:
                v = q.getLocationInGround(s)
                out.append((np.array([v.get(0), v.get(1), v.get(2)]), body))
        return out

    # ------------------------------------------------------------ ghép tư thế
    def raj_dirs(self, vals, side):
        """Hướng cánh tay (u, f) trong hệ trục thân từ tư thế toàn thân; tay trái → đối xứng sang phải."""
        v = {k: vals[k] for k in vals if k.startswith(("arm_", "elbow_", "pro_sup", "wrist_"))}
        if side == "l":
            v = {k[:-2] + "_r": v[k] for k in v if k.endswith("_l")}
        else:
            v = {k: v[k] for k in v if k.endswith("_r")}
        self.raj.p.set(v, reset=True)
        u, f = self.raj.dirs()
        return u, f

    def fit(self, u_t, f_t, x0):
        """Ba góc vai MoBL (elv_angle, shoulder_elv, shoulder_rot) cho trục cánh tay & khuỷu cho trước."""
        A = self.align[:3, :3] / np.cbrt(np.linalg.det(self.align[:3, :3]))
        p = self.mobl.p

        def res(x):
            p.set({"elv_angle": x[0], "shoulder_elv": x[1], "shoulder_rot": x[2]})
            u, f = self.mobl.dirs()
            return np.r_[A @ u - u_t, (A @ f - f_t) * 0.7, 0.002 * (x[1] < 1) * x[0]]

        lo, hi = [-90, 0, -90], [130, 180, 75]
        x0 = np.clip(x0, np.array(lo) + 1e-6, np.array(hi) - 1e-6)
        sol = least_squares(res, x0, bounds=(lo, hi), xtol=1e-10, ftol=1e-10, max_nfev=200)
        best = sol
        if sol.cost > 1e-4:   # thử vài điểm xuất phát khác (tránh cực tiểu địa phương)
            for e0 in (-60, 0, 60, 110):
                s2 = least_squares(res, [e0, max(x0[1], 20), 0], bounds=(lo, hi), max_nfev=200)
                if s2.cost < best.cost:
                    best = s2
        return best.x, math.degrees(math.asin(min(1.0, math.sqrt(2 * best.cost) / 2)))

    def mobl_coords(self, vals, side):
        u_t, f_t = self.raj_dirs(vals, side)
        x, err = self.fit(u_t, f_t, self._x[side])
        self._x[side] = x
        sfx = "_" + side
        return {"elv_angle": x[0], "shoulder_elv": x[1], "shoulder_rot": x[2],
                "elbow_flexion": float(np.clip(vals["elbow_flex" + sfx], 0, 130)),
                "pro_sup": float(np.clip(vals["pro_sup" + sfx] - 90.0, -90, 90)),   # Rajagopal 0 = ngửa ↔ MoBL −90
                "flexion": float(np.clip(vals.get("wrist_flex" + sfx, 0.0), -70, 70)),
                "deviation": float(np.clip(vals.get("wrist_dev" + sfx, 0.0), -10, 25))}, err

    # ------------------------------------------------------------ số liệu cơ
    def evaluate(self, vals, side, want_paths=False):
        """→ dict: nfl, mtu (theo SHOWN; NaN nếu đường cơ quấn sai), sai số ghép (độ), cờ ngoài vùng,
        [đường cơ trong hệ trục thân (đối xứng nếu tay trái), tư thế bả vai & xương đòn]."""
        c, err = self.mobl_coords(vals, side)
        nfl, mtu, bad = self._measure(c)
        if bad:
            # Mặt quấn có những điểm kỳ dị số học đơn lẻ: lệch 0.01° là hết. Đo lại ở vài tư thế lệch cực nhỏ;
            # chỉ khi cả vùng lân cận đều lỗi mới loại số liệu cơ đó.
            for d in ((0.05, 0.05, 0), (-0.05, 0.03, 0.04), (0.03, -0.05, -0.04), (-0.04, -0.04, 0.05)):
                c2 = {**c, "elv_angle": c["elv_angle"] + d[0], "shoulder_elv": c["shoulder_elv"] + d[1],
                      "shoulder_rot": c["shoulder_rot"] + d[2]}
                n2, l2, b2 = self._measure(c2)
                for j, mu in enumerate(self.muscles):
                    if np.isnan(nfl[j]) and not np.isnan(n2[j]):
                        nfl[j], mtu[j] = n2[j], l2[j]
                bad = [mu.getName() for j, mu in enumerate(self.muscles) if np.isnan(nfl[j])]
                if not bad:
                    break
            self._measure(c)   # trả mô hình về đúng tư thế (cho đường cơ / bả vai)
        out_rom = [k for k, (a, b) in ROM.items() if not (a - 2 <= c[k] <= b + 2)]
        out = {"coords": c, "fit_err_deg": err, "nfl": nfl, "mtu": mtu, "wrap_bad": bad, "out_of_rom": out_rom}
        if want_paths:
            from .export import resample
            paths = []
            for mu in self.muscles:
                P = resample(np.array([self.to_torso(q, b) for q, b in self.current_path(mu)]))
                if side == "l":
                    P = P @ MIR
                paths.append(P)
            out["paths_torso"] = np.array(paths)
            out["scapula"] = self._body_in_torso("scapula", side)
            out["clavicle"] = self._body_in_torso("clavicle", side)
            out["humerus"] = self._body_in_torso("humerus", side)
        return out

    def _measure(self, c):
        import opensim as _o
        p, m, s = self.mobl.p, self.mobl.m, self.mobl.s
        p.set(c)
        m.assemble(s)            # làm mới bộ nhớ mặt quấn (OpenSim nhớ phía quấn của tư thế trước)
        for mu in self.muscles:
            mu.setActivation(s, ACTIVATION)
        m.equilibrateMuscles(s)
        m.realizeVelocity(s)
        nfl, mtu, bad = [], [], []
        for mu in self.muscles:
            L = mu.getLength(s)
            cp = mu.getGeometryPath().getCurrentPath(s)
            pts = []
            for i in range(cp.getSize()):
                q = cp.get(i)
                if _o.PathWrapPoint.safeDownCast(q) is None:
                    v = q.getLocationInGround(s)
                    pts.append([v.get(0), v.get(1), v.get(2)])
            straight = float(np.linalg.norm(np.diff(np.array(pts), axis=0), axis=1).sum())
            n = mu.getNormalizedFiberLength(s)
            ok = bool(np.isfinite(L) and np.isfinite(n) and L / straight <= WRAP_RATIO_MAX)
            nfl.append(n if ok else np.nan)
            mtu.append(L if ok else np.nan)
            if not ok:
                bad.append(mu.getName())
        return nfl, mtu, bad

    MOBL_TO_SKIN = {"ground": "torso", "clavicle": "clavicle_r", "clavphant": "clavicle_r", "scapula": "scapula_r",
                    "scapphant": "scapula_r", "humerus": "humerus_r", "humphant": "humerus_r", "humphant1": "humerus_r",
                    "ulna": "ulna_r", "radius": "radius_r", "proximal_row": "hand_r", "hand": "hand_r"}

    def path_points(self, name):
        """Các điểm của đường cơ ở tư thế hiện tại (hệ trục thân, tay phải) kèm xương mà mỗi điểm bám theo."""
        mu = self.mobl.m.getMuscles().get(name)
        return [(self.to_torso(q, b), self.MOBL_TO_SKIN.get(b, "torso")) for q, b in self.current_path(mu)]

    def _body_in_torso(self, body, side):
        M = self.align @ self.mobl.frame(body)
        if side == "l":
            F = np.diag([1.0, 1.0, -1.0, 1.0])
            M = F @ M @ F
        return M
