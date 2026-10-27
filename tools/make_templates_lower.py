"""Sinh templates/01–11 (mẫu thân dưới + giãn chân) cho hộp thoại "Bài mới".

Chạy từ thư mục gốc:  python tools/make_templates_lower.py
Sửa TPL bên dưới rồi chạy lại; sau đó dựng + kiểm tra: python tools/build_all.py tpl-lower
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from pipeline.motion import ARM_PRESETS, COLUMNS
A = {k: v for k, (_, v) in ARM_PRESETS.items()}
T = {"hold": 0.3, "down": 2.0, "pause": 0.4, "up": 1.4}

def std(knee, tilt, lumbar, arms):
    return {"knee_flexion": knee, "pelvis_anterior_tilt": tilt, "lumbar_flexion": lumbar, **arms}

def free(tilt, lumbar, r, l, arms):
    k = {"pelvis_anterior_tilt": tilt, "lumbar_flexion": lumbar}
    for side, v in (("r", r), ("l", l)):
        hf, ha, hr, kn, an = v
        k.update({f"hip_flexion_{side}": hf, f"hip_adduction_{side}": ha, f"hip_rotation_{side}": hr,
                  f"knee_flexion_{side}": kn, f"ankle_dorsiflexion_{side}": an})
    k.update(arms)
    return k

def kfs(*frames):
    return [{"phase": p, **f} for p, f in frames]

WALL = {**A["forward"], "arm_flexion": 80, "arm_abduction": 12, "elbow_flexion": 20}   # hai tay chống tường
hang_vertical = lambda trunk: {**A["hang"], "arm_flexion": trunk, "elbow_flexion": 5}   # tay buông thẳng xuống sàn khi thân gập

TPL = {
 "01-squat": ({"title": "Squat không tạ", "desc": "Squat sâu, hai tay đưa ra trước giữ thăng bằng.", "tags": ["đứng", "gym"]},
   {"name": "Squat không tạ", "category": "Gym from zero", "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 32, "toe_out_deg": 15},
    "keyframes": kfs((0, std(0, 0, 0, A["forward"])), (0.25, std(30, 5, 1, A["forward"])), (0.5, std(70, 14, 4, A["forward"])),
                     (0.75, std(100, 23, 7, A["forward"])), (1, std(120, 30, 10, A["forward"]))),
    "notes": "Squat sâu, hai tay đưa ra trước để giữ thăng bằng."}),
 "02-goblet-squat": ({"title": "Goblet squat", "desc": "Ôm tạ trước ngực, thân thẳng hơn squat thường.", "tags": ["đứng", "gym", "tạ đơn"]},
   {"name": "Goblet squat", "category": "Gym from zero", "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 36, "toe_out_deg": 20},
    "keyframes": kfs((0, std(0, 0, 0, A["goblet"])), (0.5, std(65, 10, 2, A["goblet"])), (1, std(118, 22, 6, A["goblet"]))),
    "notes": "Ôm tạ đơn sát ngực; thân giữ thẳng hơn nên gối gập sâu hơn."}),
 "03-sumo-squat": ({"title": "Sumo squat", "desc": "Chân rộng, mũi chân xoay ra nhiều.", "tags": ["đứng", "gym"]},
   {"name": "Sumo squat", "category": "Gym from zero", "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 62, "toe_out_deg": 35},
    "keyframes": kfs((0, std(0, 0, 0, A["goblet"])), (0.5, std(55, 8, 2, A["goblet"])), (1, std(105, 18, 4, A["goblet"]))),
    "notes": "Hai chân rộng hơn vai, mũi chân xoay ra ~35°."}),
 "04-rdl": ({"title": "Romanian deadlift (RDL)", "desc": "Gập hông, gối hơi chùng, tay buông theo thanh tạ.", "tags": ["đứng", "gym", "bản lề hông"]},
   {"name": "Romanian deadlift", "category": "Gym from zero", "mode": "standing", "timing": {**T, "down": 2.2, "pause": 0.3},
    "options": {"stance_width_cm": 24, "toe_out_deg": 5},
    "keyframes": kfs((0, std(5, 0, 0, hang_vertical(0))), (0.5, std(15, 38, 2, hang_vertical(40))), (1, std(20, 72, 5, hang_vertical(77)))),
    "notes": "Đẩy hông ra sau, lưng giữ trung tính, gối chỉ hơi chùng."}),
 "05-good-morning": ({"title": "Good morning", "desc": "Gập hông với hai tay sau đầu, gối gần thẳng.", "tags": ["đứng", "gym", "bản lề hông"]},
   {"name": "Good morning", "category": "Gym from zero", "mode": "standing", "timing": {**T, "pause": 0.3},
    "options": {"stance_width_cm": 28, "toe_out_deg": 8},
    "keyframes": kfs((0, std(0, 0, 0, A["prisoner"])), (1, std(8, 65, 5, A["prisoner"]))),
    "notes": "Hai tay đan sau đầu, gập hông tới khi thân gần song song sàn."}),
 "06-split-squat": ({"title": "Split squat", "desc": "Chân phải trước neo phẳng, chân trái sau nhón mũi.", "tags": ["một chân", "gym"]},
   {"name": "Split squat (chân phải trước)", "category": "Gym from zero", "mode": "free", "timing": {**T, "down": 1.8, "pause": 0.3, "up": 1.3},
    "options": {"anchor_r": "flat", "anchor_l": "toes", "auto_ankle": True},
    "keyframes": kfs((0, free(4, 0, (32, 0, 0, 8, 0), (-20, 0, 0, 12, -22), A["hips"])),
                     (1, free(10, 3, (84, 0, 0, 95, 0), (15, 0, 0, 90, -37), A["hips"]))),
    "notes": "Chân phải phía trước neo phẳng, chân trái phía sau neo mũi chân."}),
 "07-single-leg-rdl": ({"title": "RDL một chân", "desc": "Đứng chân phải, chân trái duỗi ra sau theo thân.", "tags": ["một chân", "bản lề hông"]},
   {"name": "RDL một chân (đứng chân phải)", "category": "Gym from zero", "mode": "free", "timing": {**T, "down": 2.2, "pause": 0.4},
    "options": {"anchor_r": "flat", "anchor_l": "none", "auto_ankle": True},
    "keyframes": kfs((0, free(0, 0, (0, 0, 0, 8, 0), (0, 0, 0, 10, 0), hang_vertical(0))),
                     (1, free(70, 4, (68, 0, 0, 20, 0), (-2, 0, 0, 5, 0), {**hang_vertical(74), "arm_abduction": 14}))),
    "notes": "Đứng trên chân phải, chân trái duỗi ra sau cùng lúc thân gập xuống."}),
 "08-calf-raise": ({"title": "Nhón gót", "desc": "Hai chân neo mũi, gót nhấc lên.", "tags": ["đứng", "bắp chân"]},
   {"name": "Nhón gót", "category": "Gym from zero", "mode": "free", "timing": {"hold": 0.3, "down": 1.2, "pause": 0.6, "up": 1.4},
    "options": {"anchor_r": "toes", "anchor_l": "toes", "auto_ankle": False},
    "keyframes": kfs((0, free(0, 0, (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), A["hips"])),
                     (1, free(0, 0, (0, 0, 0, 0, -35), (0, 0, 0, 0, -35), A["hips"]))),
    "notes": "Nhón lên bằng mũi chân, gối duỗi thẳng."}),
 "09-quad-stretch": ({"title": "Giãn đùi trước (đứng)", "desc": "Đứng chân phải, gập gối trái kéo gót về mông.", "tags": ["giãn cơ", "chạy bộ"]},
   {"name": "Giãn đùi trước khi đứng", "category": "Running from zero", "mode": "free", "timing": {"hold": 0.3, "down": 1.6, "pause": 1.5, "up": 1.2},
    "options": {"anchor_r": "flat", "anchor_l": "none", "auto_ankle": True},
    "keyframes": kfs((0, free(0, 0, (0, 0, 0, 5, 0), (0, 0, 0, 5, 0), A["hips"])),
                     (0.5, free(0, 0, (0, 0, 0, 5, 0), (5, 0, 0, 90, -20), A["hips"])),
                     (1, free(-4, 0, (0, 0, 0, 5, 0), (-15, 0, 0, 110, -30), A["hips"]))),
    "notes": "Gót trái kéo sát mông, đùi trái hơi đưa ra sau, chậu không ưỡn."}),
 "10-hamstring-stretch": ({"title": "Gập người chạm mũi chân", "desc": "Giãn đùi sau: gối thẳng, gập hông và lưng.", "tags": ["giãn cơ", "chạy bộ"]},
   {"name": "Gập người chạm mũi chân", "category": "Running from zero", "mode": "standing", "timing": {"hold": 0.3, "down": 2.2, "pause": 1.2, "up": 1.8},
    "options": {"stance_width_cm": 20, "toe_out_deg": 5},
    "keyframes": kfs((0, std(0, 0, 0, hang_vertical(0))), (0.5, std(0, 40, 12, hang_vertical(55))), (1, std(0, 70, 30, hang_vertical(105)))),
    "notes": "Gối duỗi thẳng, gập dần từ hông rồi tới lưng, tay vươn về mũi chân."}),
 "11-calf-stretch": ({"title": "Giãn bắp chân (dựa tường)", "desc": "Chân sau thẳng, gót bám sàn, dồn người về trước.", "tags": ["giãn cơ", "chạy bộ"]},
   {"name": "Giãn bắp chân dựa tường (chân trái sau)", "category": "Running from zero", "mode": "free", "timing": {"hold": 0.3, "down": 1.6, "pause": 1.5, "up": 1.2},
    "options": {"anchor_r": "flat", "anchor_l": "flat", "auto_ankle": True},
    "keyframes": kfs((0, free(0, 0, (25, 0, 0, 20, 0), (-15, 0, 0, 0, 0), WALL)),
                     (1, free(0, 0, (31, 0, 0, 50, 0), (-25, 0, 0, 0, 0), WALL))),
    "notes": "Chân trái phía sau duỗi thẳng, gót trái giữ chạm sàn; dồn hông về trước để kéo giãn bắp chân trái."}),
}
cols = {m: set(c) for m, c in COLUMNS.items()}
for name, (meta, ex) in TPL.items():
    for k in ex["keyframes"]:
        extra = set(k) - cols[ex["mode"]] - {"phase"}
        assert not extra, (name, extra)
    ex = {"template": {**meta, "order": int(name[:2])}, **ex}
    json.dump(ex, open(f"templates/{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(TPL), "templates")
