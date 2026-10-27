"""Sinh templates/12–25 (mẫu thân trên + giãn tay/vai/ngực) cho hộp thoại "Bài mới".

Chạy từ thư mục gốc:  python tools/make_templates_upper.py
Sau đó dựng + kiểm tra: python tools/build_all.py tpl-upper
Các tư thế đã được chỉnh để qua kiểm tra hình học (xem docs/09-viec-con-lai.md về kéo xà/chin-up).
"""
import os
import json, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from pipeline.motion import COLUMNS

def arms(flex, abd, rot, elbow, fore):
    return {"arm_flexion": flex, "arm_abduction": abd, "arm_rotation": rot, "elbow_flexion": elbow, "forearm_rotation": fore}

def std(knee, tilt, lumbar, a):
    return {"knee_flexion": knee, "pelvis_anterior_tilt": tilt, "lumbar_flexion": lumbar, **a}

def free(tilt, lumbar, r, l, a):
    k = {"pelvis_anterior_tilt": tilt, "lumbar_flexion": lumbar}
    for side, v in (("r", r), ("l", l)):
        hf, ha, hr, kn, an = v
        k.update({f"hip_flexion_{side}": hf, f"hip_adduction_{side}": ha, f"hip_rotation_{side}": hr,
                  f"knee_flexion_{side}": kn, f"ankle_dorsiflexion_{side}": an})
    k.update(a)
    return k

def kfs(*frames):
    return [{"phase": p, **f} for p, f in frames]

STRAIGHT = (0, 0, 0, 0, 0)
HANG_LEGS = (10, 0, 0, 25, -10)
T = {"hold": 0.3, "down": 1.6, "pause": 0.3, "up": 1.2}
STRETCH_T = {"hold": 0.3, "down": 1.6, "pause": 1.5, "up": 1.2}
UP = "Gym from zero"
TPL = {
 "12-push-up": ({"title": "Chống đẩy", "desc": "Mũi chân và bàn tay neo sàn, thân thẳng như tấm ván.", "tags": ["thân trên", "ngực", "không dụng cụ"]},
   {"name": "Chống đẩy", "category": UP, "mode": "free", "timing": T,
    "options": {"anchor_r": "toes", "anchor_l": "toes", "auto_ankle": True, "anchor_hand_r": "floor", "anchor_hand_l": "floor", "arms": "same"},
    "keyframes": kfs((0, free(75, 0, STRAIGHT, STRAIGHT, arms(74, 22, 0, 0, 170))),
                     (1, free(84, 0, STRAIGHT, STRAIGHT, arms(25, 45, 0, 105, 170)))),
    "notes": "Hai tay rộng hơn vai một chút, khuỷu mở khoảng 45° so với thân, hạ ngực gần chạm sàn."}),
 "13-pull-up": ({"title": "Kéo xà (tay sấp, rộng)", "desc": "Treo xà, kéo người lên tới cằm qua xà.", "tags": ["thân trên", "lưng xô", "xà đơn"]},
   {"name": "Kéo xà tay sấp", "category": UP, "mode": "free", "timing": {"hold": 0.4, "down": 1.2, "pause": 0.3, "up": 1.6},
    "options": {"anchor_r": "none", "anchor_l": "none", "anchor_hand_r": "bar", "anchor_hand_l": "bar", "arms": "same", "pelvis_height_cm": 94},
    "keyframes": kfs((0, free(0, 0, HANG_LEGS, HANG_LEGS, arms(0, 160, -45, 5, 150))),
                     (1, free(0, 0, HANG_LEGS, HANG_LEGS, arms(0, 30, -60, 128, 150)))),
    "notes": "Phase 0 = treo thẳng tay (lưng xô bị kéo dài nhất), phase 1 = kéo lên đỉnh."}),
 "14-chin-up": ({"title": "Kéo xà tay ngửa (chin-up)", "desc": "Nắm xà ngửa tay, rộng bằng vai.", "tags": ["thân trên", "lưng xô", "nhị đầu", "xà đơn"]},
   {"name": "Kéo xà tay ngửa (chin-up)", "category": UP, "mode": "free", "timing": {"hold": 0.4, "down": 1.2, "pause": 0.3, "up": 1.6},
    "options": {"anchor_r": "none", "anchor_l": "none", "anchor_hand_r": "bar", "anchor_hand_l": "bar", "arms": "same", "pelvis_height_cm": 94},
    "keyframes": kfs((0, free(0, 0, HANG_LEGS, HANG_LEGS, arms(175, 15, 0, 5, 10))),
                     (1, free(0, 0, HANG_LEGS, HANG_LEGS, arms(60, 30, 0, 125, 10)))),
    "notes": "Nắm xà ngửa tay. Phase 0 = treo thẳng tay, phase 1 = cằm qua xà."}),
 "15-dips": ({"title": "Chống xà kép (dips)", "desc": "Hai tay chống xà kép, hạ người tới khuỷu ~90°.", "tags": ["thân trên", "ngực", "tam đầu", "xà kép"]},
   {"name": "Chống xà kép (dips)", "category": UP, "mode": "free", "timing": T,
    "options": {"anchor_r": "none", "anchor_l": "none", "anchor_hand_r": "bar", "anchor_hand_l": "bar", "arms": "same", "pelvis_height_cm": 110},
    "keyframes": kfs((0, free(5, 0, (5, 0, 0, 60, -10), (5, 0, 0, 60, -10), arms(0, 12, 0, 5, 85))),
                     (1, free(18, 0, (15, 0, 0, 60, -10), (15, 0, 0, 60, -10), arms(-45, 15, 0, 95, 85)))),
    "notes": "Thân hơi đổ trước, hạ người tới khi khuỷu gập khoảng 90° và vai thấp hơn khuỷu một chút."}),
 "16-bench-press": ({"title": "Đẩy ngực nằm (bench press)", "desc": "Nằm ngửa trên ghế, hạ thanh đòn xuống ngực.", "tags": ["thân trên", "ngực", "tạ đòn"]},
   {"name": "Đẩy ngực nằm (bench press)", "category": UP, "mode": "free", "timing": T,
    "options": {"anchor_r": "none", "anchor_l": "none", "anchor_hand_r": "none", "anchor_hand_l": "none", "arms": "same", "pelvis_height_cm": 55},
    "keyframes": kfs((0, free(-90, -5, (10, -10, 0, 90, 0), (10, -10, 0, 90, 0), arms(88, 12, 0, 0, 170))),
                     (1, free(-90, -5, (10, -10, 0, 90, 0), (10, -10, 0, 90, 0), arms(-5, 60, 0, 95, 170)))),
    "notes": "Hai tay rộng hơn vai, khuỷu mở khoảng 60°; ở đáy khuỷu thấp hơn mặt ghế một chút."}),
 "17-overhead-press": ({"title": "Đẩy vai qua đầu", "desc": "Đứng đẩy tạ từ vai lên thẳng tay qua đầu.", "tags": ["thân trên", "vai", "tạ đòn"]},
   {"name": "Đẩy vai qua đầu (overhead press)", "category": UP, "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 30, "toe_out_deg": 10, "arms": "same"},
    "keyframes": kfs((0, std(2, 0, 0, arms(30, 70, -75, 105, 170))), (1, std(2, 0, -3, arms(15, 165, -10, 8, 170)))),
    "notes": "Phase 0 = thanh tạ ở ngang vai, phase 1 = tay thẳng qua đầu."}),
 "18-lateral-raise": ({"title": "Dang tạ ngang vai", "desc": "Nâng tạ đơn sang hai bên tới ngang vai.", "tags": ["thân trên", "vai", "tạ đơn"]},
   {"name": "Dang tạ ngang vai (lateral raise)", "category": UP, "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 26, "toe_out_deg": 8, "arms": "same"},
    "keyframes": kfs((0, std(5, 3, 0, arms(8, 10, 0, 15, 85))), (1, std(5, 3, 0, arms(15, 90, 0, 15, 85)))),
    "notes": "Khuỷu hơi chùng, nâng tới khi tay ngang vai."}),
 "19-biceps-curl": ({"title": "Cuốn tạ tay (biceps curl)", "desc": "Đứng, cuốn tạ đơn với lòng bàn tay ngửa.", "tags": ["thân trên", "nhị đầu", "tạ đơn"]},
   {"name": "Cuốn tạ tay (biceps curl)", "category": UP, "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 26, "toe_out_deg": 8, "arms": "same"},
    "keyframes": kfs((0, std(3, 0, 0, arms(0, 6, 0, 5, 0))), (1, std(3, 0, 0, arms(8, 6, 0, 140, 0)))),
    "notes": "Phase 0 = tay duỗi (nhị đầu dài nhất), phase 1 = cuốn lên hết."}),
 "20-overhead-triceps": ({"title": "Duỗi tam đầu qua đầu", "desc": "Cánh tay giơ qua đầu, hạ tạ ra sau gáy.", "tags": ["thân trên", "tam đầu", "tạ đơn"]},
   {"name": "Duỗi tam đầu qua đầu", "category": UP, "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 28, "toe_out_deg": 8, "arms": "same"},
    "keyframes": kfs((0, std(3, 0, -2, arms(165, 12, 0, 20, 85))), (1, std(3, 0, -2, arms(165, 12, 0, 140, 85)))),
    "notes": "Cánh tay giữ thẳng đứng cạnh đầu; phase 1 = tạ hạ sâu sau gáy (tam đầu dài nhất)."}),
 "21-triceps-pushdown": ({"title": "Đẩy cáp tam đầu (pushdown)", "desc": "Cánh tay sát thân, khuỷu gập rồi duỗi.", "tags": ["thân trên", "tam đầu", "cáp"]},
   {"name": "Đẩy cáp tam đầu (pushdown)", "category": UP, "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 28, "toe_out_deg": 8, "arms": "same"},
    "keyframes": kfs((0, std(5, 8, 0, arms(5, 8, 0, 5, 170))), (1, std(5, 8, 0, arms(10, 8, 0, 110, 170)))),
    "notes": "Phase 0 = tay duỗi thẳng xuống, phase 1 = khuỷu gập (vị trí tam đầu dài nhất của bài này). So với duỗi tam đầu qua đầu, đầu dài ở đây ngắn hơn hẳn."}),
 "22-bent-over-row": ({"title": "Chèo tạ cúi người", "desc": "Gập hông ~45°, kéo tạ về bụng.", "tags": ["thân trên", "lưng", "tạ đòn"]},
   {"name": "Chèo tạ cúi người (bent-over row)", "category": UP, "mode": "standing", "timing": T,
    "options": {"stance_width_cm": 28, "toe_out_deg": 8, "arms": "same"},
    "keyframes": kfs((0, std(22, 50, 5, arms(55, 8, 0, 5, 150))), (1, std(22, 50, 5, arms(-25, 25, 0, 100, 150)))),
    "notes": "Thân giữ nghiêng ~50°. Phase 0 = tay buông thẳng xuống sàn, phase 1 = kéo tạ chạm bụng."}),
 "23-chest-stretch": ({"title": "Giãn ngực ở khung cửa", "desc": "Cẳng tay tựa khung cửa, xoay người ra trước.", "tags": ["giãn cơ", "ngực", "vai"]},
   {"name": "Giãn ngực ở khung cửa", "category": "Lifestyle", "mode": "standing", "timing": STRETCH_T,
    "options": {"stance_width_cm": 26, "toe_out_deg": 8, "arms": "same"},
    "keyframes": kfs((0, std(0, 0, 0, arms(0, 8, 0, 10, 85))), (0.5, std(0, 0, 0, arms(0, 85, -70, 90, 85))),
                     (1, std(0, 0, -3, arms(-35, 90, -80, 90, 85)))),
    "notes": "Cánh tay dang ngang vai, cẳng tay dựng đứng tựa khung cửa; ngực đẩy ra trước để cánh tay ra sau mặt phẳng thân."}),
 "24-triceps-stretch": ({"title": "Giãn tam đầu qua đầu", "desc": "Giơ tay qua đầu, gập khuỷu để bàn tay chạm lưng.", "tags": ["giãn cơ", "tam đầu"]},
   {"name": "Giãn tam đầu qua đầu", "category": "Lifestyle", "mode": "standing", "timing": STRETCH_T,
    "options": {"stance_width_cm": 26, "toe_out_deg": 8, "arms": "same"},
    "keyframes": kfs((0, std(0, 0, 0, arms(0, 8, 0, 10, 85))), (0.5, std(0, 0, 0, arms(165, 10, 0, 60, 85))),
                     (1, std(0, 0, -3, arms(172, 12, 0, 145, 85)))),
    "notes": "Cánh tay sát tai, khuỷu gập hết cỡ."}),
 "25-cross-body-stretch": ({"title": "Giãn vai sau (kéo tay ngang ngực)", "desc": "Kéo cánh tay ngang qua ngực.", "tags": ["giãn cơ", "vai"]},
   {"name": "Giãn vai sau – kéo tay ngang ngực", "category": "Lifestyle", "mode": "standing", "timing": STRETCH_T,
    "options": {"stance_width_cm": 26, "toe_out_deg": 8, "arms": "same"},
    "keyframes": kfs((0, std(0, 0, 0, arms(0, 8, 0, 10, 85))), (1, std(0, 0, 0, arms(90, -30, 20, 10, 85)))),
    "notes": "Cánh tay ngang vai, kéo ngang qua trước ngực về phía vai bên kia."}),
}
cols = {m: set(c) for m, c in COLUMNS.items()}
for name, (meta, ex) in TPL.items():
    for k in ex["keyframes"]:
        extra = set(k) - cols[ex["mode"]] - {"phase"}
        assert not extra, (name, extra)
    ex = {"template": {**meta, "order": int(name[:2])}, **ex}
    json.dump(ex, open(f"templates/{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(TPL), "templates")
