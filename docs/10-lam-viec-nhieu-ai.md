# 10 · Làm việc với nhiều AI / nhiều người cùng lúc

## Đọc gì trước
Mỗi tác nhân mới: `AGENTS.md` (gốc) → `docs/README.md` → `01` → `02` → file của vùng mình làm →
`07` (bẫy). Không cần đọc toàn bộ code.

## Vùng làm việc (để song song mà ít đụng nhau)
| Vùng | File sở hữu | Giao diện với vùng khác (giữ ổn định) |
|---|---|---|
| **A. Chuyển động** | `pipeline/motion.py`, `tools/make_templates_*.py`, `templates/` | Định dạng bài tập (05), `MotionSolver.build/pose` trả toạ độ Rajagopal, `/api/meta` |
| **B. Số liệu cơ** | `pipeline/export.py`, `pipeline/upper.py`, `pipeline/stretch.py`, `pipeline/muscle_names.py`, `assets/model/` | `motion.json` (05); `stretch.py` ⇔ `stretchIndex` JS |
| **C. Gắn hình & QA** | `pipeline/zbind*.py`, `pipeline/skin.py`, `pipeline/qa*.py`, `assets/zanat_*` | Định dạng `zanat_*.json`; DQS JS ⇔ Python |
| **D. Viewer blog** | `web/viewer.html`, phần dùng chung trong `web/anatomy-core.js` | Đọc `motion.json`; một file |
| **E. Studio** | `studio.py`, `web/studio.html` | API (05) |
| **F. Kiểm chứng & tài liệu** | `tools/validate_muscles.py`, `docs/`, `README.md` | Nguồn trích dẫn |

`web/anatomy-core.js` là vùng chung D/E/C: thay đổi phải giữ tương thích cả viewer lẫn Studio và
chạy `python -m pipeline.qa --selftest` nếu chạm phần `// <dqs>`.

## Bất biến (không được phá)
1. Màu/số chỉ từ mô hình OpenSim; định nghĩa "bị kéo giãn" chỉ ở `stretch.py` (+ bản JS giống hệt).
2. Thiếu số liệu → NaN → 0 trong `nfl_u16` → xám. Không đoán.
3. Mọi bài ví dụ và mẫu qua QA (`pass|warn`). Không nới `LIMITS`.
4. Kiểm chứng không tụt: A 68/68, B 32/32 + 4/4, C 11/11, E1 81/81, E2 ≥ 34/35, E3 ≥ 12/13.
   Kết quả không đạt được giải thích, không "chỉnh cho khớp".
5. `viewer.html` đầu ra là **một file**; giao diện và chữ cho người đọc bằng tiếng Việt.
6. Ghi nguồn Z-Anatomy (CC BY-SA) trên viewer và (mặc định) trên ảnh.
7. `.bat` chạy được trên Windows sạch với Python 3.11–3.13.

## Tài sản dựng sẵn — ai được dựng lại
`assets/zanat_binding.json`, `zanat_field.npz`, `zanat_upper.json`, `upper_align.json`,
`osim.bones.json`, `MoBL_ARMS_millard.osim` là **đầu ra** của script. Chỉ vùng C (hoặc B với
mô hình) dựng lại, và khi dựng lại phải: chạy QA mọi bài thân trên/dưới, chạy kiểm chứng, dựng
lại `exercises/`, ghi vào `08-nhat-ky-quyet-dinh.md`. Hai tác nhân **không** được dựng lại cùng một
tài sản song song (file lớn, không gộp được).

## Quy ước làm việc
- Không có git trong thư mục giao nhận hiện tại → nên khởi tạo repo (`git init`) và bỏ `.venv/`,
  `output/_*`, `__pycache__/` khỏi theo dõi; mỗi vùng một nhánh.
- Thay đổi hành vi → cập nhật `docs/` liên quan trong cùng lần sửa (bảng file ở 02, định dạng ở 05,
  số kiểm chứng ở 06, quyết định ở 08, việc còn lại ở 09).
- Chú thích code bằng tiếng Việt, giải thích *vì sao* (giữ phong cách hiện tại).
- Script thử nghiệm để ở `tools/dev/`; đầu ra thử nghiệm đặt slug bắt đầu bằng `_` và xoá sau.

## Checklist bàn giao (dán vào cuối mỗi lượt làm)
```
Vùng: …            File đã sửa: …
Đã chạy: [ ] build_all  [ ] validate_muscles (số: …)  [ ] qa --selftest  [ ] soát mắt Studio
Tài sản dựng lại: …   Tài liệu đã cập nhật: …
Còn dở / rủi ro: …
```
