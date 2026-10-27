# 04 · Hiển thị: hình cơ, biến dạng, viewer, Studio, chụp ảnh

## Nguyên tắc
Hình cơ Z-Anatomy là **minh hoạ**. Mỗi vùng của một hình cơ mang **id đường cơ OpenSim/MoBL**
(theo tên, bảng `MAP` trong `zbind.py` / `zbind_upper.py`) và lấy màu từ số liệu của đúng đường
đó. Hình chỉ cần đi theo xương hợp lý, không rách/lật/xuyên — QA đo điều đó (06).

## Tài sản gắn hình (dựng một lần)

### Thân dưới — `pipeline/zbind.py` → `assets/zanat_binding.json` (+ `zanat_field.npz`)
- Căn xương chậu/đùi/bánh chè/cẳng chân Z-Anatomy vào OpenSim ở tư thế trung tính (ICP có co
  giãn), uốn mesh cơ theo xương gần nó (`register_bones`).
- **Trường trọng số điều hoà** chung trên lưới 6 mm (`GRID_H`) phủ hông–đùi–cẳng chân: giải
  Laplace với bề mặt xương làm biên (bỏ mặt khớp `JOINT_GAP` = 25 mm, cầu quanh tâm khớp),
  cộng "đĩa giữa đoạn chi" (`SEGMENT_DISKS`) để trọng số không rò qua hai khớp. `ALLOWED` giới hạn
  xương mỗi cơ được nhận.
- Dựng lại lưới cơ cho đều cạnh, mịn hơn ở vùng chuyển tiếp quanh khớp (`remesh_adaptive`).
- Đỉnh mang `bw` (trọng số K xương theo `skinBodies` = torso, pelvis, femur_r, tibia_r), `l`/`w`
  (hai đường cơ gần nhất + tỉ lệ trộn màu). Bên trái = đối xứng gương của bên phải.

### Thân trên — `pipeline/zbind_upper.py` → `assets/zanat_upper.json`
- Xương: lồng ngực gắn `torso` (không thay xương OpenSim, `replace: false`); cánh tay/trụ/quay/
  bàn tay thay xương OpenSim (`replace: true`); **bả vai, xương đòn là xương ảo** `scapula_r`,
  `clavicle_r` (tư thế nghỉ = thân, chạy theo MoBL — xem 03).
- **Trọng số theo đường lực** (`line_weights`): mỗi đỉnh tìm điểm gần nhất trên đường cơ MoBL
  của nó; mỗi điểm đường cơ thuộc một xương; nhãn xương được làm mượt dọc chiều dài (Gauss
  `LINE_SIGMA` = 0.12 m, `SIGMA_OVERRIDE`), rồi `LINE_SMOOTH` = 100 vòng trên bề mặt.
- `cross_smooth`: làm mượt trọng số qua các cặp điểm tiếp giáp (r = 2 cm, 60 vòng, λ 0.5) giữa
  cơ **cùng nhóm**: nhóm thân (ngực lớn, lưng xô) và nhóm tay–vai; `SOLO` (tròn lớn, tròn bé) đứng riêng.
- `LABEL_OVERRIDE`: lưng xô đoạn qua bả vai → thân; bụng đầu ngắn nhị đầu không theo xương quay;
  FCU/ECU/FDP/FDS/PL theo xương trụ thay vì xương quay.
- Mọi thay đổi ở file này phải chạy lại QA các bài thân trên (06) — các tham số đã được dò để
  vừa qua ngưỡng; sửa một cơ có thể làm cơ kề bên hỏng (đã gặp: chỉnh nhị đầu → tròn bé rách).

## Biến dạng — dual quaternion skinning (DQS)
- `skinDQ(rest, cur)` cho mỗi xương: dual quaternion của `X_cur · X_rest⁻¹`.
- `dqsDeform`: trộn DQ theo trọng số từng đỉnh. Bên trái: gương z.
- Bản Python `pipeline/skin.py` dùng cho QA; `python -m pipeline.qa --selftest` so với code JS
  trích từ giữa marker `// <dqs>` … `// </dqs>` trong `anatomy-core.js` (sai khác hiện ≈ 0.0001 mm).
  **Sửa một bên phải sửa bên kia.**

## `web/anatomy-core.js` (dùng chung viewer + Studio)
- `ZAnatomy(scene, zan, bodyNodes, bodyIdx, muscleOf, mirror)`: một instance cho mỗi file gắn
  hình (thân dưới, thân trên). `update(valueOf, colourOf, look, neutral)`; `look(muscles)` →
  `"hide" | "dim" | "on" | "picked"`; `style = {on, dim}` độ đậm; `setBoneOpacity`; `pickables`,
  `muscleAt(hit)`; `anchors()` → trọng tâm phần hình thuộc từng cơ (gắn nhãn ảnh).
- NaN (không có số liệu) → màu `neutral` xám.
- `makePalette(css)` đọc màu từ biến CSS `--short --optimal --lengthen --long --longest`.

## Viewer blog — `web/viewer.html` → `output/<slug>/viewer.html`
- Một file: `build.page` chèn `<script type="application/json" id="data-motion|data-bones|data-zanat|data-zanat-upper">`
  và thay `// @@ANATOMY_CORE@@`. three.js 0.160 từ jsDelivr (`_preview.html` dùng bản cục bộ).
- Tính năng: góc nhìn Trước/Nghiêng/Chéo/Sau, Tự xoay; *Giải phẫu* (Z-Anatomy) / *Đường lực*;
  màu *Kéo giãn* / *l/l_opt*; danh sách "Giãn nhiều nhất"; bảng nhóm cơ (ẩn/hiện, Tập trung,
  từng cơ); chi tiết một cơ (đường cong độ dài, lúc dài nhất); thanh tiến trình động tác + tốc độ;
  phần "Số liệu này đến từ đâu" + câu kiểm chứng (`docs/kiem-chung.json`).
- Câu mở đầu và xếp hạng theo `rank_key` (vượt tối ưu trước).

## Studio — `web/studio.html`
Bố cục: Thư viện | Khung 3D + thanh thời gian | Bảng chỉnh (tab Tư thế / Bài tập / Xuất bản / Ảnh).
- **Trạng thái** `S` (bài, tư thế đang chọn, phase, mẫu chuyển động, hiển thị…), hoàn tác `H`
  (lưu JSON bài, gộp thay đổi 400 ms), móc kiểm thử `window.studio = {S, PH, camera, controls, setView, selectRow, setPlaying, render, setTab, snap}`.
- **Xem trước**: `/api/preview_motion` (21 mẫu phase + các phase của tư thế) mỗi khi bài đổi
  (gộp, tối đa 1 yêu cầu đang chạy), `/api/preview` khi kéo thanh trượt (tư thế đang sửa, có `x0`
  ấm). Nội suy giữa mẫu: vị trí tuyến tính, quay slerp, nfl tuyến tính.
- **Tab Tư thế**: thanh trượt theo `META.sections` (+ "Tay trái" khi `arms: separate`), mẫu tay
  (`ARM_PRESETS`, áp cho tay phải hoặc trái), "Giữ tay giống nhau ở mọi tư thế", Hai chân giống
  nhau / Đổi chân, Chép/Dán tư thế, kiểm tra tức thì (bàn chân trượt, góc phải chỉnh…).
- **Thanh thời gian**: ◆ tư thế then chốt (kéo để dời), đường cong góc gối/hông/thân — hoặc
  khuỷu/vai khi tay chuyển động nhiều hơn chân (`S.armView`).
- **Xuất bản**: Xem thử (bản nháp không QA, iframe) / Tạo bản đăng blog (có QA, tải zip).
- Phím: Ctrl+S, Ctrl+Z/Y, Space, ← →.

### Chế độ chụp ảnh (tab Ảnh; trạng thái `PH`)
- Khung sáng (`#guide`) = vùng ảnh; `photoCam(rect)` = bản sao camera với `setViewOffset` cắt
  đúng vùng đó → ảnh trùng khung trên màn hình ở mọi tỉ lệ.
- `snap({phase, bg, caption})`: đặt renderer = kích thước đầu ra (cạnh dài 1080–4320, chặn theo
  `MAX_RENDERBUFFER_SIZE`, tối đa 8192), render, vẽ lên canvas 2D: nền (màu / chuyển màu / trong
  suốt) → ảnh WebGL → lớp chữ (`paintOverlay`), rồi trả renderer về cũ. Renderer tạo với `alpha: true`.
- Lớp chữ: tên cơ bị kéo giãn nhiều nhất (xếp như `rank_key`, một tên mỗi cơ, chọn bên gần máy
  ảnh, hai cột trái/phải có đường chỉ), thang màu, tên bài + thời điểm, dòng ghi nguồn (mặc định
  bật — CC BY-SA). Màu chữ tự đổi theo độ sáng nền. Xem trước vẽ cùng hàm trên `#overlay`.
- Kiểu nhanh (`PRESETS`), "Căn người vào giữa khung" (`fitToFrame`: tìm khoảng cách bằng chia đôi
  để cả động tác lọt khung), "Đến lúc giãn nhất", Tải PNG / Chép ảnh / Tải chuỗi khung.
- Màu "Tự nhiên" (`NATURAL`) dùng với "Làm mờ cơ không bị kéo giãn" để làm nổi cơ chính.
