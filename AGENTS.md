# Hướng dẫn cho AI / người làm tiếp — Anatomy Studio

Đọc trước khi sửa: `docs/README.md` (mục lục) → `docs/01-tong-quan.md` → `docs/02-kien-truc.md`
→ tài liệu của vùng bạn làm → `docs/07-quy-uoc-va-bay.md`. Chia việc và bất biến:
`docs/10-lam-viec-nhieu-ai.md`.

Tóm tắt:
- Studio cục bộ (FastAPI `studio.py` + `web/studio.html`, Three.js) tạo `output/<slug>/viewer.html`
  (một file) cho blog tiếng Việt *From Zero*. Màu cơ = chiều dài sợi cơ từ OpenSim
  (Rajagopal thân dưới, MoBL-ARMS thân trên), vẽ trên hình cơ Z-Anatomy (CC BY-SA).
- **Đúng trước, đẹp sau.** Không bịa số; thiếu số liệu → xám. Định nghĩa "bị kéo giãn" duy nhất ở
  `pipeline/stretch.py` (+ `stretchIndex` trong `web/anatomy-core.js`, phải giống hệt).
- Trước khi báo xong: `python tools/build_all.py all` (không `fail`), `python tools/validate_muscles.py`
  (không tụt), `python -m pipeline.qa --selftest`, soát mắt Studio. Chi tiết: `docs/06-kiem-tra.md`.
- Không nới ngưỡng QA, không chỉnh tư thế để kết quả kiểm chứng "khớp".
- Tiếng Việt cho giao diện, chú thích, tài liệu; tiếng Anh cho tên biến/khoá JSON.
- Python 3.11–3.13 (opensim==4.6). Chạy: `python studio.py --port 8765 --no-browser`.
