"""Kiểm chứng: vùng cơ hiển thị có ĐÚNG không?

Ba tầng kiểm tra độc lập, kết quả ghi ra docs/kiem-chung.md (dùng được để trích trong blog):

  A. Chức năng giải phẫu — cho từng khớp gập/duỗi riêng lẻ từ tư thế đứng, cơ nào dài ra / ngắn lại
     phải đúng như sách giải phẫu (ví dụ gập hông làm đùi sau dài ra, gập gối làm đùi sau ngắn lại).
  B. Hình cơ 3D ↔ đường cơ OpenSim — mỗi hình cơ Z-Anatomy được tô màu theo đường cơ OpenSim
     của chính nó; kiểm tra đường đó thật sự nằm trong / sát hình cơ đó (không lệch sang cơ bên cạnh).
  C. Đối chiếu bài tập với nghiên cứu đã công bố — squat, RDL, split squat.
  E. Thân trên (MoBL-ARMS): chức năng, vị trí điểm bám, đối chiếu các bài đẩy/kéo/tay.

Chạy:  python tools/validate_muscles.py
"""
import base64
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pipeline.common import ASSETS, OUTPUT_DIR, Poser, load_model  # noqa: E402
from pipeline.export import equilibrate, resample, muscle_polyline  # noqa: E402
from pipeline.muscle_names import MUSCLES  # noqa: E402

# ---------------------------------------------------------------- A
# Chiều thay đổi độ dài cơ-gân (MTU) khi gập riêng một khớp, theo giải phẫu chức năng.
# +1 = dài ra, -1 = ngắn lại, 0 = không bắc qua khớp (thay đổi phải ~0).
# Nguồn: chức năng cơ theo sách giải phẫu chuẩn (Gray's Anatomy; Neumann, Kinesiology of the
# Musculoskeletal System). Chỉ ghi những trường hợp không gây tranh cãi.
JOINT_TESTS = {
    "Gập hông 60°": ({"hip_flexion_r": 60}, {
        "glmax1": 1, "glmax2": 1, "glmax3": 1, "bflh": 1, "semimem": 1, "semiten": 1, "addmagIsch": 1,
        "iliacus": -1, "psoas": -1, "recfem": -1, "sart": -1, "tfl": -1,
        "vaslat": 0, "vasmed": 0, "vasint": 0, "bfsh": 0, "soleus": 0, "gasmed": 0, "gaslat": 0}),
    "Gập gối 60°": ({"knee_angle_r": 60}, {
        "vaslat": 1, "vasmed": 1, "vasint": 1, "recfem": 1,
        "bflh": -1, "bfsh": -1, "semimem": -1, "semiten": -1, "grac": -1, "sart": -1, "gasmed": -1, "gaslat": -1,
        "glmax1": 0, "glmax2": 0, "iliacus": 0, "psoas": 0, "soleus": 0, "addlong": 0}),
    "Gập mu cổ chân 20°": ({"ankle_angle_r": 20}, {
        "soleus": 1, "gasmed": 1, "gaslat": 1, "tibpost": 1, "fdl": 1, "fhl": 1,
        "tibant": -1, "edl": -1, "ehl": -1,
        "vaslat": 0, "bflh": 0, "glmax2": 0}),
    "Dang hông 25°": ({"hip_adduction_r": -25}, {
        "addlong": 1, "addbrev": 1, "addmagMid": 1, "addmagDist": 1, "grac": 1,
        "glmed1": -1, "glmed2": -1, "glmed3": -1, "glmin2": -1, "tfl": -1,
        "vaslat": 0, "soleus": 0}),
    "Duỗi hông 20° (ra sau)": ({"hip_flexion_r": -20}, {
        "iliacus": 1, "psoas": 1, "recfem": 1, "addlong": 1,
        "glmax2": -1, "bflh": -1, "semimem": -1}),
}
ZERO_TOL = 0.004   # 4 mm: cơ không bắc qua khớp thì gần như không đổi
SIGN_TOL = 0.002   # 2 mm: đủ lớn để coi là dài ra / ngắn lại


def mtu_lengths(model, state, poser, values):
    poser.set(values, reset=True)
    model.realizeVelocity(state)
    M = model.getMuscles()
    return {M.get(i).getName(): M.get(i).getLength(state) for i in range(M.getSize())}


def check_function(model, state, poser):
    base = mtu_lengths(model, state, poser, {})
    rows, bad = [], 0
    for test, (pose, expect) in JOINT_TESTS.items():
        L = mtu_lengths(model, state, poser, pose)
        for mus, sign in expect.items():
            d = L[mus + "_r"] - base[mus + "_r"]
            if sign == 0:
                ok = abs(d) < ZERO_TOL
            else:
                ok = d * sign > SIGN_TOL
            bad += not ok
            rows.append((test, MUSCLES[mus][0], sign, d * 1000, ok))
    return rows, bad


# ---------------------------------------------------------------- B
def b64(s, dt):
    return np.frombuffer(base64.b64decode(s), dt)


def seg_dist(P, V):
    """Khoảng cách từ các điểm V tới polyline P."""
    best = np.full(len(V), np.inf)
    for a, b in zip(P[:-1], P[1:]):
        ab = b - a
        t = np.clip(((V - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        best = np.minimum(best, np.linalg.norm(V - (a + t[:, None] * ab), axis=1))
    return best


# Cơ mà hình Z-Anatomy chỉ có phần bụng cơ, còn đường OpenSim đi tiếp qua một gân dài tới điểm bám xa:
LONG_TENDON = {"tfl_r": "bám xuống xương chày qua dải chậu–chày", "gaslat_r": "bám vào gót qua gân Achilles",
               "gasmed_r": "bám vào gót qua gân Achilles", "soleus_r": "bám vào gót qua gân Achilles"}
# Thứ tự các bó trong một hình cơ: (trục, chiều) — trục 0 = trước(+)/sau, 1 = trên(+)/dưới
BUNDLE_ORDER = {
    "Gluteus maximus muscle": (1, ["glmax1_r", "glmax2_r", "glmax3_r"], "trên → dưới"),
    "Gluteus medius muscle": (0, ["glmed1_r", "glmed2_r", "glmed3_r"], "trước → sau"),
    "Gluteus minimus muscle": (0, ["glmin1_r", "glmin2_r", "glmin3_r"], "trước → sau"),
    "Adductor magnus": (1, ["addmagProx_r", "addmagMid_r", "addmagDist_r"], "trên → dưới"),
}
ATTACH_TOL = 0.025


def check_meshes(model, state, poser):
    import trimesh
    zb = json.load(open(os.path.join(ASSETS, "zanat_binding.json"), encoding="utf-8"))
    poser.set({}, reset=True)
    model.realizeVelocity(state)
    M = model.getMuscles()
    rows, orders, best = [], [], {}
    for zm in zb["muscles"]:
        V = b64(zm["v"], "<i2").reshape(-1, 3).astype(float) / 1e4
        F = b64(zm["idx"], "<u2").reshape(-1, 3)
        mesh = trimesh.Trimesh(V, F, process=False)
        own = [zb["lines"][i]["id"] for i in zm["lines"]]
        for lid in own:
            P = np.array(muscle_polyline(M.get(lid), state))
            _, d, _ = trimesh.proximity.closest_point(mesh, P[[0, -1]])
            best.setdefault(lid, []).append((zm["name"], d))
        if zm["name"] in BUNDLE_ORDER:
            ax, ids, label = BUNDLE_ORDER[zm["name"]]
            l = b64(zm["l"], "u1").reshape(-1, 2)
            w = b64(zm["w"], "<f4")
            dom = np.where(w >= 0.5, l[:, 0], l[:, 1])
            idx = {zb["lines"][i]["id"]: i for i in zm["lines"]}
            pos = [float(V[dom == idx[i], ax].mean()) for i in ids]
            orders.append((zm["name"], label, [MUSCLES[i[:-2]][0] for i in ids], pos, all(np.diff(pos) < 0)))
    # một đường cơ có thể được gán cho nhiều hình (khép lớn phần gần ↔ "Adductor minimus"): lấy hình khớp nhất
    for lid, cands in best.items():
        zname, d = min(cands, key=lambda c: c[1].max())
        note = LONG_TENDON.get(lid, "")
        ok = d[0] < ATTACH_TOL and (d[1] < ATTACH_TOL or bool(note))
        rows.append((" / ".join(c[0] for c in cands), MUSCLES[lid[:-2]][0], d[0] * 1000, d[1] * 1000, ok, note))
    return rows, orders


# ---------------------------------------------------------------- C
def fiber_series(slug):
    from pipeline import stretch
    p = os.path.join(OUTPUT_DIR, slug, "data", "motion.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    nm = len(d["muscles"])
    nfl = b64(d["nfl_u16"], "<u2").reshape(-1, nm) / 1e4
    nfl[nfl <= 0] = np.nan                                 # 0 = khung không có số liệu tin cậy
    bottom = int(np.argmax(d["phase"]))
    out = {}
    for j, m in enumerate(d["muscles"]):
        st = stretch.summarize(nfl[:, j])
        st["drop"] = float(np.nanmin(nfl[:, j]) / nfl[0, j] - 1) if np.isfinite(nfl[:, j]).any() else 0.0
        st["bottom"] = float(nfl[bottom, j] / nfl[0, j] - 1)     # ở điểm cuối động tác (phase 1)
        out[m["id"]] = st
    return d, out


# Kỳ vọng rút từ nghiên cứu / giải phẫu (xem phần Nguồn). Mỗi dòng: (mô tả, hàm kiểm tra, nguồn)
def lit_checks():
    pct = lambda r, m: r[m]["change"] * 100              # noqa: E731  dài thêm so với lúc bắt đầu
    gmean = lambda r, ms, k="change": np.mean([r[m][k] for m in ms])  # noqa: E731
    stretched = lambda r, ms: all(r[m]["stretched"] for m in ms)  # noqa: E731
    HAM = ["bflh_r", "semimem_r", "semiten_r"]
    VAS = ["vaslat_r", "vasmed_r", "vasint_r"]
    GLM = ["glmax1_r", "glmax2_r", "glmax3_r"]
    L = lambda ms: [m[:-2] + "_l" for m in ms]  # noqa: E731
    return {
        "squat-khong-ta": [
            ("Mông lớn, khép lớn và các cơ rộng (tứ đầu một khớp) bị kéo giãn ở đáy squat sâu",
             lambda r: stretched(r, GLM + VAS + ["addmagIsch_r", "addmagDist_r"]), "kubo"),
            ("Thẳng đùi (tứ đầu hai khớp) KHÔNG bị kéo giãn — gập hông bù cho gập gối",
             lambda r: not r["recfem_r"]["stretched"], "kubo"),
            ("Đùi sau dài thêm ít hơn hẳn so với RDL (squat gần như không kéo đùi sau)",
             lambda r: gmean(r, HAM) < 0.6 * gmean(R["rdl"], HAM), "kubo"),
            ("Nhị đầu đùi đầu dài vẫn dài ra trong pha xuống; đầu ngắn (một khớp, chỉ bắc qua gối) thì ngắn lại",
             lambda r: r["bflh_r"]["change"] > 0.05 and r["bfsh_r"]["drop"] < -0.1, "geiser"),
            ("Bụng chân (hai khớp) chỉ giãn nhẹ thoáng qua lúc cổ chân gập trước, rồi ngắn lại ở đáy vì gối gập sâu",
             lambda r: all(r[m]["beyond"] < 0.1 and r[m]["bottom"] < 0 for m in ["gasmed_r", "gaslat_r"]), "anat"),
            ("Cơ dép (một khớp, chỉ bắc qua cổ chân) bị kéo giãn ở đáy — cổ chân gập mu sâu",
             lambda r: r["soleus_r"]["stretched"], "anat"),
        ],
        "rdl": [
            ("Đùi sau là nhóm bị kéo giãn mạnh nhất", lambda r: gmean(r, HAM, "beyond") > max(gmean(r, GLM, "beyond"), gmean(r, VAS, "beyond")), "rdl"),
            ("Các cơ rộng không bị kéo giãn vì gối gần như giữ nguyên", lambda r: not any(r[m]["stretched"] for m in VAS), "anat"),
            ("Thẳng đùi ngắn lại (gập hông, gối gần thẳng)", lambda r: r["recfem_r"]["drop"] < -0.2, "anat"),
        ],
        "split-squat": [
            ("Chân sau: thẳng đùi bị kéo giãn (hông duỗi + gối gập)", lambda r: r["recfem_l"]["stretched"], "split"),
            ("Chân trước: mông lớn bị kéo giãn; chân sau thì không (vẫn ngắn hơn chiều dài tối ưu)",
             lambda r: stretched(r, GLM) and not any(r[m]["stretched"] for m in L(GLM)), "split"),
        ],
    }


# ---------------------------------------------------------------- thân trên (MoBL-ARMS)
# A2. Cùng cách làm như A, nhưng đi qua ĐÚNG chuỗi tính của chương trình: góc tay kiểu Rajagopal → khớp vai
# MoBL-ARMS (pipeline/upper.py) → chiều dài cơ-gân. Tư thế gốc: tay buông, khuỷu 10°, cẳng tay trung tính.
UP_BASE = {"arm_flex_r": 0.0, "arm_add_r": -6.0, "arm_rot_r": 0.0, "elbow_flex_r": 10.0, "pro_sup_r": 90.0}
SHOULDER_ONLY = ["DELT1", "DELT2", "DELT3", "SUPSP", "INFSP", "SUBSC", "TMIN", "TMAJ", "PECM1", "PECM2", "PECM3",
                 "LAT1", "LAT2", "LAT3", "CORB"]
UPPER_TESTS = {
    "Gập khuỷu 10° → 90°": ({"elbow_flex_r": 90}, {
        "TRIlong": 1, "TRIlat": 1, "TRImed": 1, "ANC": 1, "BIClong": -1, "BICshort": -1, "BRA": -1, "BRD": -1,
        **{m: 0 for m in SHOULDER_ONLY}}),
    # 60°: trong khoảng này các cơ gập vai (delta trước, ngực lớn bó đòn, quạ cánh tay) chắc chắn ngắn lại; cao hơn,
    # cánh tay đòn của quạ cánh tay/ngực lớn bó đòn đổi dấu (cả trên người thật lẫn trong mô hình).
    "Đưa tay ra trước (gập vai) 60°": ({"arm_flex_r": 60}, {
        "DELT3": 1, "LAT1": 1, "LAT2": 1, "LAT3": 1, "TMAJ": 1, "TRIlong": 1,
        "DELT1": -1, "CORB": -1, "PECM1": -1, "BIClong": -1,
        "BRA": 0, "BRD": 0, "TRImed": 0, "TRIlat": 0, "ANC": 0}),
    "Dang tay ngang vai 90°": ({"arm_add_r": -90}, {
        "LAT1": 1, "LAT2": 1, "LAT3": 1, "TMAJ": 1, "PECM2": 1, "PECM3": 1,
        "DELT2": -1, "SUPSP": -1, "BRA": 0, "TRImed": 0}),
    "Đưa tay ra sau (duỗi vai) 30°": ({"arm_flex_r": -30}, {
        "DELT1": 1, "CORB": 1, "PECM1": 1, "BIClong": 1, "DELT3": -1, "TRIlong": -1, "BRA": 0}),
    "Xoay ngoài vai 45° (khuỷu 90°, cánh tay sát thân)": ({"elbow_flex_r": 90, "arm_rot_r": -45, "_base": {"elbow_flex_r": 90}}, {
        "SUBSC": 1, "PECM1": 1, "PECM2": 1, "TMAJ": 1, "INFSP": -1, "TMIN": -1}),
    # tới trung tính: khi úp hẳn, đường cơ ngửa của MoBL-ARMS quấn sai (đã báo trong viewer, cơ hiện xám)
    "Xoay cẳng tay từ ngửa hẳn về trung tính": ({"pro_sup_r": 80, "_base": {"pro_sup_r": 0}}, {
        "SUP": 1, "BIClong": 1, "BICshort": 1, "PT": -1, "PQ": -1, **{m: 0 for m in SHOULDER_ONLY}}),
}


def check_upper_function(U):
    from pipeline.upper import SHOWN
    rows, bad = [], 0
    for test, (pose, expect) in UPPER_TESTS.items():
        base = {**UP_BASE, **pose.get("_base", {})}
        L0 = U.evaluate(base, "r")["mtu"]
        L1 = U.evaluate({**base, **{k: v for k, v in pose.items() if k != "_base"}}, "r")["mtu"]
        for mus, sign in expect.items():
            d = L1[SHOWN.index(mus)] - L0[SHOWN.index(mus)]
            ok = bool(np.isfinite(d)) and (abs(d) < ZERO_TOL if sign == 0 else d * sign > SIGN_TOL)
            bad += not ok
            rows.append((test, MUSCLES[mus][0], sign, d * 1000, ok))
    return rows, bad


# B2. Điểm bám đầu/cuối của đường cơ MoBL-ARMS so với hình cơ Z-Anatomy (cùng phép căn khi dựng hình).
UP_TENDON = {
    "BIClong": "đầu dài đi qua rãnh gian củ bằng một gân dài tới củ trên ổ chảo",
    "BRD": "bám mỏm trâm quay qua gân dẹt",
    "ECRL": "bám xương bàn tay qua gân dài", "ECRB": "bám xương bàn tay qua gân dài", "ECU": "bám xương bàn tay qua gân dài",
    "FCR": "bám xương bàn tay qua gân dài", "FCU": "bám xương đậu qua gân", "PL": "nối vào cân gan tay qua gân dài",
    "FDSM": "bám đốt ngón qua gân dài", "FDPM": "bám đốt ngón qua gân dài", "EDCM": "bám đốt ngón qua gân dài",
    "LAT1": "bám rãnh gian củ xương cánh tay qua gân dẹt dài", "LAT2": "bám rãnh gian củ xương cánh tay qua gân dẹt dài",
    "LAT3": "bám rãnh gian củ xương cánh tay qua gân dẹt dài", "TMAJ": "bám mép trong rãnh gian củ qua gân dẹt (~5 cm)",
    "PECM3": "phần bụng xoắn vào gân chung của ngực lớn trước khi bám xương cánh tay",
    "BICshort": "nhập vào gân chung với đầu dài, bám lồi củ xương quay",
}


def check_upper_meshes(U):
    import trimesh
    from pipeline.common import Poser as _P
    zb = json.load(open(os.path.join(ASSETS, "zanat_upper.json"), encoding="utf-8"))
    m, s = load_model()
    p = _P(m, s)
    p.set({}, reset=True)
    T0 = np.array(p.body_xforms(["torso"])[0])
    from pipeline.export import _quat_R
    R0, t0 = _quat_R(T0[3:]), T0[:3]
    U.evaluate({k: 0.0 for k in ["arm_flex_r", "arm_add_r", "arm_rot_r", "elbow_flex_r", "pro_sup_r"]}, "r")  # tư thế nghỉ của hình cơ
    best = {}
    for zm in zb["muscles"]:
        V = b64(zm["v"], "<i2").reshape(-1, 3).astype(float) / 1e4
        F = b64(zm["idx"], "<u2").reshape(-1, 3)
        mesh = trimesh.Trimesh(V, F, process=False)
        for i in zm["lines"]:
            lid = zb["lines"][i]["id"]
            P = np.array([q for q, _ in U.path_points(lid[:-2])]) @ R0.T + t0
            _, d, _ = trimesh.proximity.closest_point(mesh, P[[0, -1]])
            best.setdefault(lid, []).append((zm["name"], d))
    rows = []
    for lid, cands in best.items():
        zname, d = min(cands, key=lambda c: c[1].max())
        note = UP_TENDON.get(lid[:-2], "")
        ok = (d[0] < ATTACH_TOL or (bool(note) and lid[:-2] == "BIClong")) and (d[1] < ATTACH_TOL or bool(note))
        rows.append((zname, MUSCLES[lid[:-2]][0], d[0] * 1000, d[1] * 1000, ok, note))
    return rows


def lit_checks_upper():
    pct = lambda r, m: r[m]["change"]                     # noqa: E731
    bot = lambda r, m: r[m]["bottom"]                     # noqa: E731
    return {
        "_tpl-overhead-triceps": [
            ("Tam đầu đầu dài dài hơn hẳn khi duỗi tam đầu qua đầu so với đẩy cáp (pushdown) — cánh tay giơ qua đầu kéo "
             "đầu dài (bắc qua vai) dài thêm",
             lambda r: "_tpl-triceps-pushdown" in R and r["TRIlong_r"]["max"] > R["_tpl-triceps-pushdown"]["TRIlong_r"]["max"] + 0.15, "maeo"),
            ("Đầu ngoài và đầu trong (một khớp) dài như nhau ở hai bài — chỉ phụ thuộc góc khuỷu",
             lambda r: "_tpl-triceps-pushdown" in R and all(abs(r[m]["max"] - R["_tpl-triceps-pushdown"][m]["max"]) < 0.08 for m in ["TRIlat_r", "TRImed_r"]), "anat"),
        ],
        "_tpl-pull-up": [
            ("Lưng xô và cơ tròn lớn dài nhất khi treo thẳng tay (phase 0), ngắn lại khi kéo người lên",
             lambda r: all(bot(r, m) < -0.03 for m in ["LAT2_r", "LAT3_r", "TMAJ_r"]), "anat"),
            ("Nhị đầu và cơ cánh tay ngắn lại khi kéo lên (gập khuỷu)", lambda r: all(bot(r, m) < -0.2 for m in ["BIClong_r", "BRA_r"]), "anat"),
        ],
        "_tpl-push-up": [
            ("Ngực lớn và delta trước dài ra ở đáy (cánh tay ra sau mặt phẳng thân)",
             lambda r: all(pct(r, m) > 0.08 for m in ["PECM1_r", "PECM2_r", "DELT1_r"]), "anat"),
            ("Tam đầu đầu ngoài/đầu trong dài ra (khuỷu gập)", lambda r: all(pct(r, m) > 0.2 for m in ["TRIlat_r", "TRImed_r"]), "anat"),
        ],
        "_tpl-bench-press": [
            ("Ngực lớn và delta trước dài ra khi hạ thanh đòn xuống ngực",
             lambda r: all(pct(r, m) > 0.08 for m in ["PECM1_r", "PECM2_r", "DELT1_r"]), "anat"),
        ],
        "_tpl-biceps-curl": [
            ("Nhị đầu, cơ cánh tay, cánh tay quay ngắn lại; tam đầu dài ra",
             lambda r: all(bot(r, m) < -0.2 for m in ["BIClong_r", "BICshort_r", "BRA_r", "BRD_r"]) and pct(r, "TRIlat_r") > 0.2, "anat"),
        ],
        "_tpl-lateral-raise": [
            ("Delta giữa và cơ trên gai ngắn lại; lưng xô, tròn lớn, ngực lớn bó ức sườn dài ra",
             lambda r: bot(r, "DELT2_r") < -0.2 and bot(r, "SUPSP_r") < -0.1 and all(pct(r, m) > 0.05 for m in ["LAT2_r", "TMAJ_r", "PECM3_r"]), "anat"),
        ],
        "_tpl-bent-over-row": [
            ("Delta sau ngắn lại, delta trước dài ra khi kéo tạ về bụng", lambda r: bot(r, "DELT3_r") < -0.15 and pct(r, "DELT1_r") > 0.2, "anat"),
        ],
        "_tpl-chest-stretch": [
            ("Ngực lớn (bó đòn và ức sườn) bị kéo giãn", lambda r: r["PECM1_r"]["stretched"] and r["PECM2_r"]["stretched"], "anat"),
        ],
        "_tpl-triceps-stretch": [
            ("Tam đầu đầu dài, lưng xô bó dưới và cơ tròn lớn bị kéo giãn", lambda r: all(r[m]["stretched"] for m in ["TRIlong_r", "LAT3_r", "TMAJ_r"]), "anat"),
        ],
        "_tpl-cross-body-stretch": [
            ("Delta sau và cơ dưới gai bị kéo giãn", lambda r: r["DELT3_r"]["stretched"] and r["INFSP_r"]["stretched"], "anat"),
        ],
    }


UPPER_NOTES = {
    "_tpl-chest-stretch": "phần ức sườn bị kéo giãn rõ (vượt chiều dài tối ưu ~7%); phần đòn dài thêm 15% nhưng chỉ vừa chạm "
                          "chiều dài tối ưu (1.02) nên chưa tính là \"bị kéo giãn\". Kết luận này được giữ nguyên là ✗ thay vì chỉnh tư thế cho khớp.",
}
R = {}


def main():
    model, state = load_model(rigid_tendons=False)
    poser = Poser(model, state)
    out = ["# Kiểm chứng vùng cơ hiển thị", "",
           "Tạo tự động bởi `tools/validate_muscles.py`. Mô hình: Rajagopal 2016 + Lai 2017 + Uhlrich 2022 "
           "(OpenSim). Chiều dài sợi cơ: gân đàn hồi, cơ thả lỏng (kích hoạt 1%).", ""]

    rows, bad = check_function(model, state, poser)
    out += ["## A. Chức năng giải phẫu (gập riêng từng khớp từ tư thế đứng)", "",
            f"**{len(rows) - bad}/{len(rows)} khớp đúng.** Thay đổi là chiều dài cơ + gân (mm).", "",
            "| Thao tác | Cơ | Kỳ vọng | Mô hình | Đúng |", "|---|---|---|---:|:---:|"]
    for t, m, s, d, ok in rows:
        out.append(f"| {t} | {m} | {'dài ra' if s > 0 else 'ngắn lại' if s < 0 else 'không đổi'} | {d:+.1f} | {'✓' if ok else '✗'} |")
    print(f"A. chức năng: {len(rows) - bad}/{len(rows)} đúng")

    mrows, orders = check_meshes(model, state, poser)
    mbad = sum(not r[4] for r in mrows) + sum(not o[4] for o in orders)
    out += ["", "## B. Hình cơ 3D có đúng là cơ được tô số liệu không", "",
            "Màu của mỗi hình cơ lấy theo **tên**: hình *Vastus lateralis* của Z-Anatomy chỉ nhận số liệu của cơ "
            "`vaslat` trong OpenSim, nên không thể tô nhầm sang cơ khác. Bảng dưới kiểm tra thêm hai nguồn dữ liệu "
            "khớp nhau về **vị trí**: điểm bám đầu và cuối của đường cơ OpenSim (được đặt theo số liệu tử thi) phải nằm "
            f"trên hoặc sát hình cơ Z-Anatomy đã căn vào bộ xương (ngưỡng {ATTACH_TOL * 1000:.0f} mm — cỡ chênh lệch giải "
            "phẫu giữa hai người khác nhau).", "",
            "Phần giữa của đường cơ OpenSim có thể lệch khỏi bụng cơ 1–3 cm: đó là chủ ý của mô hình (các điểm uốn "
            "được chọn để cánh tay đòn mô men đúng như đo trên tử thi), không phải lỗi căn chỉnh.", "",
            f"**{sum(r[4] for r in mrows)}/{len(mrows)} đường cơ khớp vị trí.**", "",
            "| Hình cơ (Z-Anatomy) | Cơ OpenSim | Điểm bám đầu (mm) | Điểm bám cuối (mm) | Đúng | Ghi chú |",
            "|---|---|---:|---:|:---:|---|"]
    for zname, mus, d0, d1, ok, note in mrows:
        out.append(f"| {zname} | {mus} | {d0:.0f} | {d1:.0f} | {'✓' if ok else '✗'} | {note} |")
    out += ["", "Cơ có nhiều bó (mông lớn 3 bó, khép lớn 4 phần…): mỗi vùng của hình cơ lấy màu của bó gần nhất. "
            "Kiểm tra thứ tự các bó trên hình:", ""]
    for zname, label, names, pos, ok in orders:
        out.append(f"- {'✓' if ok else '✗'} {zname}: {label} = " + " → ".join(names))
    print(f"B. vị trí: {sum(r[4] for r in mrows)}/{len(mrows)} đường cơ, {sum(o[4] for o in orders)}/{len(orders)} thứ tự bó")

    out += ["", "## C. Đối chiếu bài tập với nghiên cứu", ""]
    for slug in ["squat-khong-ta", "rdl", "split-squat", "good-morning", "squat-sumo", "squat-nong"]:
        fs = fiber_series(slug)
        if fs:
            R[slug] = fs[1]
    cbad = ctot = 0
    for slug, checks in lit_checks().items():
        if slug not in R:
            continue
        out += [f"### {slug}", ""]
        for desc, fn, src in checks:
            ok = bool(fn(R[slug]))
            cbad += not ok
            ctot += 1
            out.append(f"- {'✓' if ok else '✗'} {desc} *(nguồn: {SOURCES[src][0]})*")
        from pipeline.stretch import rank_key
        top = sorted(((rank_key(v), k) for k, v in R[slug].items()
                      if v["stretched"] and MUSCLES.get(k[:-2], ("", "", "other"))[2] != "other"), reverse=True)[:6]
        side = lambda k: (" (" + ("P" if k.endswith("_r") else "T") + ")") if slug == "split-squat" else ""  # noqa: E731
        out.append("")
        out.append("  Bị kéo giãn nhiều nhất: " + ", ".join(
            f"{MUSCLES[k[:-2]][0]}{side(k)} {R[slug][k]['start']:.2f}→{R[slug][k]['max']:.2f}" for _, k in top))
        out.append("")
    print(f"C. nghiên cứu: {ctot - cbad}/{ctot} khớp")

    # D. màu tuyệt đối dễ gây hiểu lầm
    if "squat-khong-ta" in R:
        r = R["squat-khong-ta"]
        mis = [(MUSCLES[k[:-2]][0], v["start"], v["change"]) for k, v in r.items()
               if v["start"] > 1.1 and v["change"] < 0.05 and MUSCLES.get(k[:-2], ("", "", "other"))[2] != "other"]
        out += ["## D. Vì sao màu mặc định là *mức kéo giãn do động tác*", "",
                "Tô theo độ dài tuyệt đối (l/l_opt) làm các cơ sau có màu \"giãn\" ngay khi đứng yên, dù squat không kéo "
                "chúng:", ""]
        out += [f"- {n}: l/l_opt lúc đứng {s0:.2f}, động tác chỉ đổi {c * 100:+.0f}%" for n, s0, c in mis]
        if "split-squat" in R:
            q = R["split-squat"]
            out += ["", "Ngược lại, tô theo mức thay đổi làm cơ mông lớn chân sau của split squat trông như \"giãn\" "
                    f"(dài thêm {q['glmax2_l']['change'] * 100:.0f}%) trong khi nó vẫn ngắn hơn chiều dài tối ưu "
                    f"({q['glmax2_l']['max']:.2f}); mông lớn chân trước mới thật sự bị kéo giãn ({q['glmax2_r']['max']:.2f})."]
        out += ["", "Vì vậy viewer dùng thang hai bậc (định nghĩa trong `pipeline/stretch.py`): một cơ chỉ được tô cam–đỏ "
                "khi nó dài hơn **cả** độ dài lúc bắt đầu **lẫn** chiều dài tối ưu. Dài ra mà chưa tới tối ưu thì tô vàng. "
                "Chế độ l/l_opt tuyệt đối vẫn có để bàn về vị trí trên đường cong lực–chiều dài.", ""]

    # ---------------- thân trên
    from pipeline.upper import UpperLimb
    U = UpperLimb()
    urows, ubad = check_upper_function(U)
    out += ["## E. Thân trên (mô hình MoBL-ARMS)", "",
            "Cơ vai, ngực, lưng xô, cánh tay và cẳng tay lấy từ mô hình chi trên MoBL-ARMS (Holzbaur 2005; Saul 2015). "
            "Góc tay bạn đặt (kiểu Rajagopal) được chuyển sang khớp vai của MoBL-ARMS bằng cách khớp hướng cánh tay và "
            "cẳng tay; bảng dưới kiểm tra **cả chuỗi** đó.", "",
            "### E1. Chức năng giải phẫu", "",
            f"**{len(urows) - ubad}/{len(urows)} đúng.** Thay đổi là chiều dài cơ + gân (mm).", "",
            "| Thao tác | Cơ | Kỳ vọng | Mô hình | Đúng |", "|---|---|---|---:|:---:|"]
    for t, m, sg, d, ok in urows:
        out.append(f"| {t} | {m} | {'dài ra' if sg > 0 else 'ngắn lại' if sg < 0 else 'không đổi'} | {d:+.1f} | {'✓' if ok else '✗'} |")
    print(f"E1. chức năng thân trên: {len(urows) - ubad}/{len(urows)} đúng")
    umrows = check_upper_meshes(U)
    out += ["", "### E2. Hình cơ 3D ↔ đường cơ MoBL-ARMS", "",
            f"**{sum(r[4] for r in umrows)}/{len(umrows)} đường cơ khớp vị trí** (ngưỡng {ATTACH_TOL * 1000:.0f} mm; "
            "cơ cẳng tay bám vào bàn tay qua gân dài nên chỉ xét điểm bám đầu).", "",
            "| Hình cơ (Z-Anatomy) | Cơ MoBL-ARMS | Điểm bám đầu (mm) | Điểm bám cuối (mm) | Đúng | Ghi chú |",
            "|---|---|---:|---:|:---:|---|"]
    for zname, mus, d0, d1, ok, note in sorted(umrows, key=lambda r: r[1]):
        out.append(f"| {zname} | {mus} | {d0:.0f} | {d1:.0f} | {'✓' if ok else '✗'} | {note} |")
    print(f"E2. vị trí thân trên: {sum(r[4] for r in umrows)}/{len(umrows)}")
    out += ["", "### E3. Đối chiếu bài tập thân trên", ""]
    for slug in lit_checks_upper():
        fs = fiber_series(slug)
        if fs:
            R[slug] = fs[1]
    if "_tpl-triceps-pushdown" not in R:
        fs = fiber_series("_tpl-triceps-pushdown")
        if fs:
            R["_tpl-triceps-pushdown"] = fs[1]
    ucbad = uctot = 0
    for slug, checks in lit_checks_upper().items():
        if slug not in R:
            continue
        out += [f"#### {slug[5:]}", ""]
        for desc, fn, src in checks:
            ok = bool(fn(R[slug]))
            ucbad += not ok
            uctot += 1
            out.append(f"- {'✓' if ok else '✗'} {desc} *(nguồn: {SOURCES[src][0][:60]}…)*")
        if slug in UPPER_NOTES:
            out.append(f"  - Ghi chú: {UPPER_NOTES[slug]}")
        out.append("")
    print(f"E3. nghiên cứu thân trên: {uctot - ucbad}/{uctot}")
    out += ["Giới hạn: mô hình không có cơ thang, cơ trám, răng cưa trước, cơ bụng và cơ dựng sống — các cơ này không được tô.", ""]

    out += ["## Nguồn", ""] + [f"- {t}" for t, _ in SOURCES.values()]
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    path = os.path.join(ROOT, "docs", "kiem-chung.md")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("→", path)
    nA, nB, bad, cbad, ctot = len(rows), len(mrows), int(bad), int(cbad), int(ctot)
    sentence = (f"Mô hình được kiểm tra tự động: {nA - bad}/{nA} phép thử chức năng giải phẫu cho đúng chiều dài ra/ngắn lại; "
                f"điểm bám của {sum(r[4] for r in mrows)}/{nB} đường cơ khớp hình cơ 3D (sai lệch dưới {ATTACH_TOL * 1000:.0f} mm); "
                f"{ctot - cbad}/{ctot} kết luận cho squat, RDL và split squat khớp với nghiên cứu đã công bố "
                "(Kubo et al. 2019; Geiser et al. 2006) và giải phẫu chức năng. "
                f"Thân trên (MoBL-ARMS): {len(urows) - ubad}/{len(urows)} phép thử chức năng, "
                f"{sum(r[4] for r in umrows)}/{len(umrows)} đường cơ khớp hình 3D, "
                f"{uctot - ucbad}/{uctot} kết luận cho các bài đẩy, kéo, tay (gồm Maeo et al. 2023).")
    json.dump({"sentence": sentence, "function": [nA - bad, nA], "attachments": [int(sum(r[4] for r in mrows)), nB],
               "literature": [ctot - cbad, ctot], "upper_function": [len(urows) - ubad, len(urows)],
               "upper_attachments": [int(sum(r[4] for r in umrows)), len(umrows)], "upper_literature": [uctot - ucbad, uctot]},
              open(os.path.join(ROOT, "docs", "kiem-chung.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return bad + mbad + cbad + ubad + ucbad + sum(not r[4] for r in umrows)


SOURCES = {
    "kubo": ("Kubo K, Ikebukuro T, Yata H (2019). Effects of squat training with different depths on lower limb muscle "
             "volumes. Eur J Appl Physiol 119:1933–1942 — squat sâu tăng thể tích mông lớn & nhóm khép hơn squat nông; "
             "tứ đầu tăng như nhau; đùi sau gần như không tăng.", None),
    "rdl": ("Giải phẫu chức năng: đùi sau bắc qua hông và gối; gập hông khi gối gần thẳng làm chúng dài ra tối đa "
            "(Neumann, Kinesiology of the Musculoskeletal System, ch. 12–13).", None),
    "geiser": ("Geiser C, O'Connor K, Papaioannou Y, Montiero S (2006). Hamstrings length changes during drop jump "
               "and squat maneuvers. ISBS Proceedings — đo trên người: nhị đầu đùi đầu dài dài ra trong pha xuống của "
               "squat, đầu ngắn ngắn lại.", None),
    "anat": ("Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskeletal System; Gray's Anatomy).", None),
    "maeo": ("Maeo S, Wu Y, Huang M, et al. (2023). Triceps brachii hypertrophy is substantially greater after elbow "
             "extension training performed in the overhead versus neutral arm position. Eur J Sport Sci 23(7):1240–1250 — "
             "tập ở tư thế tay qua đầu (đầu dài bị kéo dài hơn) làm tam đầu to hơn rõ rệt.", None),
    "split": ("Giải phẫu chức năng: chân sau duỗi hông + gập gối kéo dài thẳng đùi và cơ thắt lưng–chậu; "
              "chân trước gập hông sâu kéo dài mông lớn.", None),
}
SOURCES["kubo"] = (SOURCES["kubo"][0], None)

if __name__ == "__main__":
    sys.exit(1 if main() else 0)
