# 02 · Kiến trúc

## Sơ đồ khối

```
                        ┌──────────────────────── CHẠY MỘT LẦN (tài sản dựng sẵn, đã có trong assets/) ───────────────────────┐
 Z-Anatomy FBX ──bpy──► tools/extract_zanatomy*.py ──► assets/zanat_lowerlimb.npz, zanat_upper.npz (mesh gốc)
 OpenSim .vtp ────────► pipeline/geometry.py ────────► assets/osim.bones.json (xương hiển thị)
 MoBL_ARMS_J.osim ────► tools/mobl_to_millard.py ────► assets/model/MoBL_ARMS_millard.osim
 npz + mô hình ───────► pipeline/zbind.py ───────────► assets/zanat_binding.json (+ zanat_field.npz cho QA)   [thân dưới]
 npz + mô hình ───────► pipeline/zbind_upper.py ─────► assets/zanat_upper.json                                 [thân trên]
 (tự động lần đầu) ───► pipeline/upper.py ───────────► assets/upper_align.json (căn MoBL ↔ xương hiển thị)
                        └──────────────────────────────────────────────────────────────────────────────────────────────────────┘

 exercises/<slug>.json (vài tư thế then chốt)
        │
        ▼
 pipeline/motion.py  MotionSolver.build ──► times + toạ độ khớp Rajagopal mỗi khung (30 fps), cảnh báo
        │                                  (bộ giải "standing" hoặc "free" — xem 03)
        ▼
 pipeline/export.py  Exporter.run
        ├─ thân dưới: Rajagopal, gân đàn hồi, equilibrateMuscles → l/l_opt, đường cơ, xương
        └─ thân trên: UpperExport → pipeline/upper.py UpperLimb (MoBL-ARMS) → l/l_opt, đường cơ,
                       tư thế xương ảo bả vai / xương đòn
        ▼
 pipeline/build.py   ghép motion.json + osim.bones.json + zanat_*.json + web/anatomy-core.js
                      vào web/viewer.html  ──►  output/<slug>/viewer.html (+ csv, mot, qa.json)
        │
        └─ pipeline/qa.py chạy đúng phép biến dạng của viewer → qa.json (pass / warn / fail)

 studio.py (FastAPI)  ── phục vụ web/studio.html, gọi MotionSolver/Exporter để xem trước,
                         gọi build.build để xuất bản; khoá LOCK vì OpenSim không an toàn đa luồng.
```

## Bản đồ file

### Gốc
| File | Vai trò |
|---|---|
| `studio.py` | Ứng dụng FastAPI: API (xem 05), phục vụ `web/`, `assets/`, `output/`. Chọn cổng trống, phát hiện Studio đã chạy. `--port`, `--no-browser`. |
| `run_studio.bat` / `.sh` | Tìm Python 3.11–3.13, tạo `.venv`, cài `requirements.txt`, chạy Studio. |
| `requirements.txt` | `opensim==4.6, numpy, scipy, trimesh, fast-simplification, rtree, fastapi, uvicorn` (+ `pyamg pymeshlab` chỉ khi dựng lại trường thân dưới). |
| `README.md` | Hướng dẫn người dùng (tiếng Việt). |

### `pipeline/` (Python)
| File | Vai trò chính |
|---|---|
| `common.py` | Đường dẫn (`ROOT, ASSETS, MODEL_PATH, …`), `load_model(rigid_tendons)`, `Poser` (đặt toạ độ theo **độ**, đọc vị trí/quay body, khối tâm, `body_xforms` → `[x y z qx qy qz qw]`), `slugify`. |
| `motion.py` | Định nghĩa cột (`COLUMNS`, `ARM_COLUMNS`, `ARM_COLUMNS_L`, `SECTIONS`, `ARM_PRESETS`, `OPTIONS`), `validate`, `curves` (PCHIP qua tư thế then chốt), `timeline` (giữ–xuống–dừng–lên–giữ, ease cos), `MotionSolver` (bộ giải đứng & tự do), `write_mot`, `load_exercise`. |
| `export.py` | `Exporter` (chạy chuyển động qua mô hình, gân đàn hồi), `UpperExport` (thân trên mỗi khung), `equilibrate`, `fill_gaps` (nội suy lỗ ≤ 8 khung), `branch_glitches` (phát hiện đường cơ đổi nhánh quấn), `is_symmetric` (bài đối xứng → chỉ lưu bên phải), `VIRTUAL` (xương ảo). |
| `upper.py` | `UpperLimb`: ghép tư thế tay Rajagopal → 3 góc vai MoBL (fit hướng cánh tay + cẳng tay), đo l/l_opt 35 cơ (`SHOWN`), đường cơ đã chuyển sang xương đang hiển thị (`to_torso`), tư thế bả vai/xương đòn, cờ ngoài vùng kiểm chứng (`ROM`), phát hiện quấn sai (`WRAP_RATIO_MAX`). |
| `stretch.py` | **Định nghĩa duy nhất** của "bị kéo giãn": `index`, `summarize`, `rank_key`. Viewer JS dùng công thức y hệt. |
| `build.py` | `build(ex, slug, log, run_qa)` → toàn bộ `output/<slug>/`. `core_js()` chèn `web/anatomy-core.js` vào trang (trang blog phải là MỘT file). CLI `python -m pipeline.build exercises/*.json [--no-qa]`. |
| `muscle_names.py` | `GROUPS` (nhóm hiển thị, tiếng Việt), `LOWER_GROUPS`, `UPPER_GROUPS`, `MUSCLES` (id gốc → (tên Việt, Latin, nhóm)). |
| `skin.py` | Bản Python tham chiếu của phép biến dạng viewer: dual quaternion (`skin_dq`, `apply_dqs`), `WeightField`/`FieldSet` (trường điều hoà thân dưới), `jacobian_det`. |
| `zbind.py` | Dựng tài sản thân dưới: căn xương Z-Anatomy vào OpenSim (ICP), giải trường Laplace trên lưới 6 mm, dựng lại lưới cơ, gán bó cơ → `zanat_binding.json` + `zanat_field.npz`. |
| `zbind_upper.py` | Dựng tài sản thân trên: căn xương, trọng số "theo đường lực" (`line_weights`), làm mượt chéo (`cross_smooth`), `LABEL_OVERRIDE`, `SIGMA_OVERRIDE`, `SOLO` → `zanat_upper.json`. |
| `qa.py`, `qa_metrics.py` | QA hình học (lật, kéo dài cạnh, Jacobian âm, xuyên giữa cơ), `LIMITS`, `bindings()`, `run_all`, `selftest` (so JS ↔ Python). |
| `geometry.py` | Gộp `.vtp` OpenSim thành `osim.bones.json` (bỏ `hat_ribs_scap.vtp` vì lồng ngực Z-Anatomy thay thế). |

### `web/`
| File | Vai trò |
|---|---|
| `anatomy-core.js` | Lõi dùng chung viewer + Studio: giải mã base64, `stretchIndex` (= `stretch.py`), `makePalette`, `buildBones`, `setPose`, DQS (`skinDQ`, `dqsDeform` — giữa marker `// <dqs>` để selftest trích), lớp `ZAnatomy` (mesh cơ, tô màu, độ đậm `style`, `anchors()` cho nhãn ảnh). |
| `viewer.html` | Mẫu trang blog (một file). `build.py` thay các placeholder dữ liệu và `// @@ANATOMY_CORE@@`. |
| `studio.html` | Toàn bộ giao diện Studio (một file, ES module, three.js cục bộ trong `web/vendor/three/`). Móc kiểm thử: `window.studio`. |

### `tools/`
| File | Vai trò |
|---|---|
| `validate_muscles.py` | Kiểm chứng A/B/C/E → `docs/kiem-chung.md` + `.json` (câu tóm tắt chèn vào viewer). |
| `build_all.py` | Dựng + QA hàng loạt (`all | ex | tpl-upper | tpl-lower`), mẫu vào `output/_tpl-*`. |
| `make_templates_lower.py`, `make_templates_upper.py` | Nguồn của `templates/01–11`, `12–25`. **Sửa ở đây rồi chạy lại**, đừng sửa tay JSON mẫu. |
| `extract_zanatomy.py`, `extract_zanatomy_upper.py` | Trích mesh từ FBX Z-Anatomy (cần `bpy`, Python 3.11). |
| `mobl_to_millard.py` | Đổi cơ MoBL-ARMS (Schutte1993) sang Millard2012EquilibriumMuscle. |
| `dev/*.js` | Kịch bản Playwright chụp Studio / mẫu để soát bằng mắt. |

### Dữ liệu
| Thư mục | Nội dung |
|---|---|
| `assets/model/` | `RajagopalLaiUhlrich2023.osim` + `Geometry/`, `MoBL_ARMS_J.osim` (gốc), `MoBL_ARMS_millard.osim` (dùng) + `GeometryMoBL/` |
| `assets/` | `osim.bones.json` (1,1 MB), `zanat_binding.json` (1,5 MB, thân dưới), `zanat_field.npz` (QA), `zanat_upper.json` (1,5 MB), `upper_align.json`, `*.npz` mesh gốc Z-Anatomy |
| `exercises/` | Bài của người dùng (JSON). 6 bài ví dụ. |
| `templates/` | 25 mẫu cho hộp thoại "Bài mới" (JSON bài + khối `"template"`). |
| `output/<slug>/` | Kết quả (xem 05). `output/_tpl-*`, `_t-*`, `_q-*` là rác thử nghiệm — xoá trước khi đóng gói. |
| `docs/` | Tài liệu này + báo cáo kiểm chứng. |

## Hai mô hình, một bộ xương

- **Bộ xương hiển thị và chuyển động** là của Rajagopal (26 body + 4 xương ảo `scapula_r/l`,
  `clavicle_r/l`). Mọi tư thế người dùng đặt là toạ độ Rajagopal.
- **Cơ thân dưới**: chính mô hình Rajagopal (gân đàn hồi).
- **Cơ thân trên**: một mô hình MoBL-ARMS riêng (tay phải). Mỗi khung, tư thế tay Rajagopal được
  chuyển sang MoBL bằng cách khớp *hướng* cánh tay và cẳng tay trong hệ trục thân; tay trái = đối
  xứng. Bả vai/xương đòn hiển thị lấy chuyển động từ MoBL (nhịp vai–cánh tay). Chi tiết ở 03.

## Chạy

```bash
python studio.py --port 8765 --no-browser             # Studio
python -m pipeline.build exercises/squat-khong-ta.json  # một bài, có QA
python tools/build_all.py all                           # mọi bài + mọi mẫu
python tools/validate_muscles.py                        # kiểm chứng → docs/kiem-chung.*
python -m pipeline.qa --selftest                        # viewer JS == Python
```

Thời gian tham khảo (máy chủ 1 nhân): một bài 60–200 s có QA, 5–15 s không QA; xem trước toàn bộ
chuyển động trong Studio 1–10 s (bài chống đẩy chậm nhất vì nhiều ẩn).
