# 07 · Quy ước và bẫy đã gặp

## Hệ trục, đơn vị
- OpenSim/Rajagopal: **y lên, x ra trước, z sang phải** (bên phải cơ thể z > 0). Mét. Góc trong
  `Poser.set/values` là **độ** (trừ `pelvis_tx/ty/tz` là mét).
- Z-Anatomy gốc: z lên, bên phải x < 0 → `zbind.to_osim` đổi trục.
- Bên trái = gương z (`MIR = diag(1,1,−1)`); mesh trái lật thứ tự đỉnh tam giác (`flipIndex`).
- Xform 7 số: `[x y z qx qy qz qw]` (quaternion Three.js thứ tự xyzw).
- Mesh cơ lưu int16 × 1e-4 m (±3,2 m); xương lưu float32 trong hệ trục body.
- `nfl_u16`: l/l_opt × 10000, **0 = thiếu số liệu**. Đừng dùng 0 cho ý nghĩa khác.

## Quy ước góc dễ nhầm
- `pelvis_anterior_tilt` (giao diện) = **−`pelvis_tilt`** (mô hình). Tương tự `lumbar_flexion` = −`lumbar_extension`, `arm_abduction` = −`arm_add`.
- `forearm_rotation` / `pro_sup` Rajagopal: **0 = ngửa (supination), 90 = trung tính, 170 = úp**.
  Từng ghi ngược trong nhãn/mẫu → mẫu tay sai. MoBL: `pro_sup = Raj − 90` (−90 ngửa).
- `wrist_flex` Rajagopal và `flexion` MoBL: **+ = gập về lòng bàn tay**; chống sàn cần ≈ −60…−90
  (duỗi). Khoá sẵn trong mô hình Rajagopal; `MotionSolver.__init__` mở khoá.
- `arm_flexion` so với **thân**, không so với phương thẳng đứng: chống đẩy với thân nghiêng 75°,
  tay vuông góc sàn ⇔ `arm_flexion` ≈ 75.
- Rajagopal tay: Euler gập → khép → xoay; dang 90 + xoay ngoài −90 + khuỷu 90 = tư thế "cột gôn".
- Phase 1 = **điểm cuối động tác**, không nhất thiết là "đáy" (kéo xà: phase 0 = treo, phase 1 = kéo lên).
  "Bị kéo giãn" luôn so với **phase 0** (khung hợp lệ đầu tiên).

## OpenSim
- **Không an toàn đa luồng** → `studio.LOCK` quanh mọi lệnh chạm mô hình; một mô hình dùng chung
  (`build.tools()`), `UpperExport` riêng cho Studio (`studio.upper()`).
- Mặt quấn (wrap) **nhớ phía quấn của tư thế trước** → `m.assemble(s)` trước mỗi lần đo MoBL.
- MoBL quấn sai theo hai kiểu: (1) đường cơ vòng dài vô lý (MTU/đường thẳng > 1.6) → NaN, đo lại
  lệch ±0.05°; (2) **đổi nhánh** — đường cơ bỏ quấn, đi tắt qua xương, ngắn hụt vài cm trên một đoạn
  góc (ví dụ tròn lớn ở dang tay 120–125° và 150–160° khi không xoay ngoài) → `branch_glitches`.
  Cơ ngửa (SUP) gần như luôn NaN khi úp cẳng tay > ~110 (Raj). ECRL/EDCM quấn kém quanh cổ tay.
- Cân bằng cơ MoBL bằng mô hình Schutte gốc không ổn định → đã đổi sang Millard
  (`tools/mobl_to_millard.py`). Không quay lại file `_J.osim` gốc để tính số.
- `opensim==4.6` chỉ có wheel Python 3.11–3.13. macOS: conda.
- `trimesh.registration.icp(scale=True)` có thể co tỉ lệ về ~0 (thu nhỏ đám điểm) → dùng
  `upper._icp_similarity` (chặn tỉ lệ 0.8–1.25, hai chiều, bỏ 10% cặp xa).
- Xoá `assets/upper_align.json` → tính lại lần đầu khởi tạo `UpperLimb`, **cần** `zanat_upper.json`.
  Đổi phép căn → phải dựng lại `zanat_upper.json` (đường cơ dùng để gán trọng số đổi theo).

## Bộ giải
- Đưa ràng buộc phụ (ngón tay nằm ngang) vào cùng bài toán neo với trọng số lớn → cả thân trượt,
  cổ chân bị bẻ −70°. Ràng buộc chỉ một khớp quyết định (cổ tay) thì giải riêng sau.
- Thêm ẩn số xoay vai cho tay neo → nhảy sang nghiệm "khuỷu chỉ ra ngoài" (xoay 90°). Đã bỏ.
- Treo xà không có ràng buộc khối tâm → thân trôi ra sau 28 cm. Đã thêm.
- Lời giải phụ thuộc nhánh: luôn đi dần từ phase 0 (`pose` tự lặp từ 0 tới phase cần, bước 0.1).
- Tolerance 1e-10 + max_nfev 800 làm chống đẩy mất 160 s mà không đúng hơn → 1e-8/1e-9/150.
- Kéo xà: hình học quyết định góc vai ở đỉnh (khuỷu 120° và tay cao hơn vai 23 cm ⇒ cánh tay gần
  ngang); prior của người dùng chỉ có tác dụng chọn nhánh.

## Hiển thị
- Trang blog phải là **một file** (Astro chép vào `public/`): đừng tách JS/JSON ra file riêng;
  `build.core_js()` bỏ `import`/`export` khi chèn.
- `pickables()` bỏ cơ có opacity ≤ 0.5 — chế độ ảnh để cơ mờ thì không bấm chọn được (chủ ý).
- Đọc canvas WebGL ngay sau `render` trong cùng tác vụ (không cần `preserveDrawingBuffer`).
- Chế độ ảnh đặt `scene.background = null`, nền vẽ bằng CSS của `#viewport` (xem trước) và bằng
  canvas 2D (xuất). Thoát chế độ ảnh phải trả lại nền sân khấu (`applyLook`).
- Hai cảnh báo bằng mắt mà QA không bắt: lưng xô bung ra khi giơ tay (do gán phần lưng xô qua bả
  vai cho bả vai), đường cơ MoBL lệch 3–7 cm khỏi hình cơ (do căn chỉ bằng lồng ngực Rajagopal).
  Cả hai đã sửa; khi đổi gắn hình phải nhìn lại.

## Môi trường phát triển (máy chủ của các phiên AI trước)
- Không có GPU: Chromium headless `--use-gl=swiftshader --enable-webgl --ignore-gpu-blocklist`.
- Mạng bị chặn trừ kho gói; font Google không tải được trong ảnh chụp kiểm thử (ảnh dùng font dự phòng).
- `pkill -f <tên>` có thể giết chính shell đang chạy lệnh (dòng lệnh chứa tên đó) → dùng `pgrep` lấy PID.
- Tiến trình nền bị dừng khi phiên kết thúc; dựng toàn bộ (31 bài) mất ~45–60 phút.
