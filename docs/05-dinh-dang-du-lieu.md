# 05 · Định dạng dữ liệu và API

## File bài tập — `exercises/<slug>.json`
```jsonc
{
  "name": "Split squat (chân phải trước)",   // tiêu đề trang; slug = slugify(name) khi tạo mới
  "category": "Gym from zero",               // dòng nhỏ trên tiêu đề
  "notes": "…",                              // hiện dưới tiêu đề
  "mode": "standing" | "free",
  "timing": {"hold": 0.3, "down": 1.8, "pause": 0.3, "up": 1.3},   // giây
  "options": { … },                          // theo OPTIONS[mode]
  "keyframes": [ {"phase": 0.0, <cột>: số, …}, …, {"phase": 1.0, …} ]   // ≥ 2, phase tăng dần, đầu 0, cuối 1
}
```
- **Cột** theo `COLUMNS[mode]` (+ `ARM_COLUMNS` cho cả hai kiểu; + `ARM_COLUMNS_L` = các cột tay
  có hậu tố `_l` khi `options.arms == "separate"`). Mỗi cột: `(nhãn, min, max, mặc định, gợi ý)`.
  Cột thiếu → mặc định (Studio `normalize` cũng điền khi mở bài cũ). Cột tay trái thiếu → lấy theo tay phải.
  - standing: `knee_flexion, pelvis_anterior_tilt, lumbar_flexion` + tay.
  - free: `pelvis_anterior_tilt (−90…90), lumbar_flexion`, `hip_flexion_r/l, hip_adduction_r/l,
    hip_rotation_r/l, knee_flexion_r/l, ankle_dorsiflexion_r/l` + tay.
  - tay: `arm_flexion (−60…180), arm_abduction (−30…170), arm_rotation (−90…90), elbow_flexion (0…150),
    forearm_rotation (0…170)`.
- **Tuỳ chọn** `OPTIONS`:
  - standing: `stance_width_cm (10–90, 30)`, `toe_out_deg (−10–45, 10)`, `arms (same|separate)`.
  - free: `anchor_r/l (flat|toes|none)`, `auto_ankle (bool)`, `anchor_hand_r/l (none|floor|bar)`,
    `arms`, `pelvis_height_cm (20–130, 94)`.
- `validate(ex)` trả danh sách lỗi tiếng Việt (Studio hiện cho người dùng).
- Thêm cột/tuỳ chọn mới: sửa `motion.py` (COLUMNS/OPTIONS/SECTIONS), `_free_base`/`_standing_pose`,
  nhãn tuỳ chọn trong `studio.html` (`optField` → `names`), README + tài liệu này.

## Mẫu — `templates/NN-ten.json`
Giống bài tập + khối `"template": {"title", "desc", "tags": [...], "order": NN}`. **Nguồn thật**
là `tools/make_templates_lower.py` (01–11) và `tools/make_templates_upper.py` (12–25). Mọi mẫu
phải qua QA (`python tools/build_all.py tpl-upper|tpl-lower`).

## Kết quả — `output/<slug>/`
| File | Nội dung |
|---|---|
| `viewer.html` | Trang blog một file (three.js CDN). |
| `_preview.html` | Như trên, three.js cục bộ (Studio xem thử không cần mạng). |
| `data/motion.json` | Dữ liệu viewer (dưới). |
| `data/osim.bones.json`, `data/zanat_binding.json`, `data/zanat_upper.json` | Bản sao tài sản (cho ai muốn tự dựng trang). |
| `muscles.csv` | Xếp hạng: `co, latin, nhom, bi_keo_gian (co/khong), luc_bat_dau_l/lopt, dai_nhat_l/lopt, vuot_toi_uu, thoi_diem_s, soi_co_dai_them_%, co_va_gan_dai_them_%`. |
| `angles.csv` | Mỗi khung: `time, phase, knee/hip/ankle r/l, trunk_lean, pelvis_height_cm, foot_error_cm`. (Chưa có góc tay.) |
| `motion.mot` | Chuyển động OpenSim (mở bằng OpenSim GUI). |
| `qa.json` | `status (pass|warn|fail), limits, frames_checked, sides, summary{flips_max, edge_max, jac_neg_pct_max, penetration_max_mm}, issues[{level, muscle, text}], muscles` |
| `result.json` | Tóm tắt trả về Studio: `slug, seconds, warnings, top[10], frames, symmetric, size_mb, qa`. |

### `data/motion.json`
| Khoá | Ý nghĩa |
|---|---|
| `title, category, notes` | Từ bài tập. |
| `model` | Tên mô hình, trích dẫn, giả định. |
| `fps, times[]` | 30 fps; thời gian từng khung. |
| `phase[]` | Phase mỗi khung (0→1→0). |
| `mirror` | `true` = bài đối xứng, chỉ có cơ bên phải; viewer dùng chung cho bên trái. |
| `bodies[]` | Tên body theo thứ tự trong `xforms` (Rajagopal + `scapula_r, clavicle_r, scapula_l, clavicle_l`). |
| `muscles[]` | `{id, base, side, vi, latin, group, region (lower|upper), fmax, lopt, lts}`; id thân trên dạng `DELT1_r`. |
| `summary[]` | Theo cùng thứ tự: `{id, nfl_start, nfl_max, nfl_min, t_max, fiber_change_pct, mtu_change_pct, beyond_opt, stretched, valid_pct}` (null nếu không có số liệu). |
| `groups` | `GROUPS` (tên nhóm tiếng Việt). |
| `nPts` | 14 điểm mỗi đường cơ. |
| `xforms_f32` | base64 float32 `[khung][body][x y z qx qy qz qw]`. |
| `nfl_u16` | base64 uint16 `[khung][cơ]` = round(l/l_opt × 10000); **0 = không có số liệu** (NaN). |
| `paths_mm_i16` | base64 int16 `[khung][cơ][14][3]` mm. |
| `angles` | `{columns, rows}` cho đồ thị. |
| `upper_notes` | `{gaps: {id: [đã lấp, còn thiếu]}, rom: [...], fit_err_deg_max}` |
| `warnings[]` | Cảnh báo (tiếng Việt) từ bộ giải + thân trên. |
| `validation` | Câu tóm tắt kiểm chứng (`docs/kiem-chung.json`). |

### Tài sản gắn hình (`zanat_binding.json`, `zanat_upper.json`)
`{version, region?, weights ("line" cho thân trên), skinBodies[], rest {body: xf7}, lines[{id}],
muscles[{name, lines[], nv, nf, bones, v (int16 ×1e-4 m), idx (u16/u32), bw (u16 [nv×K]/65535),
l (u1 [nv×2] chỉ số đường cơ), w (f32 tỉ lệ trộn)}], bones[{group, body, replace, nv, v (f32, hệ
trục body), idx}]}`. Toạ độ cơ: thế giới ở tư thế nghỉ Rajagopal (bên phải).

## API Studio (`studio.py`)
| Method | Đường dẫn | Vào → Ra |
|---|---|---|
| GET | `/api/meta` | `columns, options, timing, sections, arm_presets, arm_left_columns` |
| GET | `/api/muscles` | `muscles[{id, vi, latin, group, side, region}], groups, bodies` — thứ tự = thứ tự mảng `nfl` của preview (`muscle_ids`: Rajagopal rồi MoBL `_r`, `_l`) |
| GET | `/api/templates` | danh sách mẫu (sắp theo `order`) |
| GET | `/api/exercises` | `[{slug, name, mode, built, has_output}]` |
| GET/PUT/DELETE | `/api/exercises/{slug}` | đọc (kèm `result`) / lưu (422 nếu `validate` lỗi) / xoá (kèm output) |
| POST | `/api/exercises` | `{exercise}` → tạo slug mới |
| POST | `/api/preview` | `{exercise, phase, x0?}` → `bodies, xforms, info, solved, com, nfl` (một tư thế) |
| POST | `/api/preview_motion` | `{exercise, samples=21}` → `phases, xforms[] (phẳng), nfl[], info[], solved[], x[], muscles, timeline` |
| POST | `/api/build/{slug}?draft=` | dựng bài (draft = không QA) → `result, log` |
| GET | `/api/download/{slug}` | zip thư mục output (bỏ file bắt đầu bằng `_`) + `exercise.json`; 409 nếu QA = fail |
| static | `/web`, `/assets`, `/output` | |

Các API xem trước là hàm **đồng bộ** (FastAPI chạy ở luồng riêng) và giữ `LOCK` khi chạm OpenSim.
`nfl` thân trên có thể là `null` (JS đổi thành NaN). `_REF` lưu tạm chỗ neo theo (tư thế phase 0, tuỳ chọn).
