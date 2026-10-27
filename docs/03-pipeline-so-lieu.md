# 03 · Pipeline số liệu

Ba bước: **tư thế then chốt → chuyển động** (`motion.py`), **chuyển động → chiều dài cơ**
(`export.py` + `upper.py`), **chiều dài → "bị kéo giãn"** (`stretch.py`).

## 1. Từ tư thế then chốt tới chuyển động — `pipeline/motion.py`

### Thời gian
- `keyframes[*].phase` ∈ [0, 1]; phase 0 = lúc bắt đầu, phase 1 = điểm cuối động tác (đáy squat,
  ngực sát sàn…). Mỗi cột được nội suy **PCHIP** qua các tư thế (`curves`).
- `timeline(timing)`: giữ (`hold`) → xuống 0→1 (`down`, ease cos) → dừng (`pause`) → lên 1→0
  (`up`) → giữ. 30 fps. Mỗi phase khác nhau chỉ giải **một lần** (`build` dùng cache), giải theo
  phase tăng dần, lời giải trước làm điểm xuất phát cho lời giải sau (tránh nhảy nhánh).

### Kiểu "standing" (đứng hai chân bám sàn)
Người dùng đặt `knee_flexion`, `pelvis_anterior_tilt`, `lumbar_flexion`, tay. Ẩn số:
`hip, ankle, hip_adduction, hip_rotation, pelvis_tx, pelvis_ty` (giống hai bên). `least_squares`
với phần dư: gót (x, y) tại chỗ cũ, gót z = nửa độ rộng chân, bàn chân phẳng (pitch như lúc
đứng), góc mũi chân = `toe_out_deg`, **khối tâm x = giữa gót–mũi**. Sai số > 1 cm hoặc 3° → cảnh báo.

### Kiểu "free" (tự đặt từng khớp) — IK mềm
- Người dùng đặt từng khớp từng chân + tay, chọn **neo**:
  - chân `anchor_r/l`: `flat` (gót cố định + bàn chân phẳng), `toes` (khớp bàn–ngón cố định, gót
    nhấc được), `none`;
  - tay `anchor_hand_r/l`: `floor` (chống sàn), `bar` (nắm cố định), `none`;
  - `arms`: `same` | `separate` (thêm cột `*_l` cho tay trái);
  - `pelvis_height_cm`: độ cao chậu khi không neo gì; `auto_ankle`: tự giải cổ chân chân neo phẳng.
- `free_reference`: ở phase 0, hạ chậu cho chỗ neo chạm sàn (`floor_only`); lưu vị trí neo
  (gót/mũi chân, cổ tay). Tay `bar` neo tại vị trí cổ tay ở phase 0.
- Ẩn số (`_free_vars`): `pelvis_tx, pelvis_ty`, **`pelvis_tilt` khi neo cả tay lẫn chân** (chống
  đẩy: thân xoay quanh mũi chân), hông–gối–cổ chân của chân neo, `arm_flex/arm_add` của tay neo.
- Phần dư (`_free_eval`): chỗ neo đứng yên (trọng số `100·W_ANCHOR`); **treo xà không chân nào
  chạm đất → khối tâm x ngay dưới chỗ nắm**; "kéo nhẹ" mỗi khớp về góc người dùng đặt
  (`W_PRIOR`; tay neo 0.2×, cổ chân tự giải 0.02×, độ nghiêng thân 0.05×).
- **Cổ tay chống sàn** không phải ẩn số: sau khi giải xong, `_place_wrists` dò `wrist_flex`
  trong (−100, 30) để ngón tay nằm ngang (cổ tay không dời gốc bàn tay nên không ảnh hưởng neo).
  Đưa cổ tay vào bài toán chung từng làm cả thân trượt theo (xem 08).
- `least_squares(xtol=1e-8, ftol=1e-9, gtol=1e-9, max_nfev=150)` — tolerance chặt hơn làm bài
  chống đẩy chậm 10× mà không chính xác hơn.
- Cảnh báo: chỗ neo lệch > 1 cm; một khớp chân phải chỉnh > 8° (không tính tay, cổ tay, cổ chân
  tự giải); cổ chân gập mu > 45°.

### Quy ước góc (giao diện → mô hình)
| Cột giao diện | Toạ độ Rajagopal | Ghi chú |
|---|---|---|
| `pelvis_anterior_tilt` | `pelvis_tilt = −giá trị` | mô hình: + là nghiêng sau. −90 = nằm ngửa |
| `lumbar_flexion` | `lumbar_extension = −giá trị` | |
| `knee_flexion[_r/_l]` | `knee_angle_*` | |
| `ankle_dorsiflexion_*` | `ankle_angle_*` | |
| `arm_flexion` | `arm_flex_*` | 0 buông, 90 ngang vai, 180 qua đầu (so với **thân**) |
| `arm_abduction` | `arm_add_* = −giá trị` | |
| `arm_rotation` | `arm_rot_*` | + = xoay trong |
| `elbow_flexion` | `elbow_flex_*` | |
| `forearm_rotation` | `pro_sup_*` | **0 = ngửa hẳn, 90 = trung tính, 170 = úp hẳn** |
| (tự giải) | `wrist_flex_*` | + = gập về lòng bàn tay; chống sàn ≈ −60…−90 |

## 2. Từ chuyển động tới chiều dài cơ — `pipeline/export.py`

### Thân dưới (Rajagopal–Lai–Uhlrich 2023)
- `load_model(rigid_tendons=False)`; mỗi khung `Poser.set` rồi `equilibrate`: kích hoạt 0.01,
  `model.equilibrateMuscles` → `getNormalizedFiberLength` = **l/l_opt** (sợi cơ), `getLength` =
  chiều dài cơ + gân (MTU). Tức là **mức giãn thụ động**, gân đàn hồi.
- Đường cơ lấy mẫu lại `N_PTS = 14` điểm (vẽ chế độ "Đường lực").
- `is_symmetric(rows)` (sai khác ≤ 0.05°, cổ tay ≤ 1°): bài đối xứng → chỉ lưu bên phải
  (`mirror: true`), viewer dùng chung số cho bên trái.

### Thân trên (MoBL-ARMS) — `pipeline/upper.py`, `UpperExport`
1. `raj_dirs`: đặt tay trên một bản Rajagopal riêng, lấy hai hướng trong hệ trục thân: trục dọc
   cánh tay `u` và hướng cẳng tay `f` *như khi khuỷu 90°* (để xoay trục cánh tay luôn xác định).
2. `fit`: `least_squares` 3 góc vai MoBL `elv_angle, shoulder_elv, shoulder_rot` (biên
   [−90, 0, −90]–[130, 180, 75]) cho hai hướng trùng; thử thêm 4 điểm xuất phát nếu chưa khớp.
   Lời giải trước làm điểm xuất phát (`self._x[side]`).
3. `elbow_flexion` lấy nguyên (MoBL ≤ 130°); `pro_sup_MoBL = pro_sup_Raj − 90`;
   `flexion = wrist_flex`, `deviation = wrist_dev`.
4. `_measure`: `assemble` (xoá "trí nhớ" phía quấn của OpenSim), kích hoạt 0.01, cân bằng, đọc
   l/l_opt và MTU của 35 cơ `SHOWN`. **Quấn sai** khi MTU / đường thẳng qua các điểm > 1.6
   (`WRAP_RATIO_MAX`) → đo lại ở 4 tư thế lệch ±0.05°; vẫn sai → NaN.
5. Tay trái: đối xứng qua mặt phẳng giữa (`MIR = diag(1,1,−1)`), dùng chính mô hình tay phải.
   Bài `arms: same` → tay trái chép số tay phải.
6. Cờ `out_of_rom` khi `shoulder_rot > 20°` (ngoài vùng Holzbaur/Saul kiểm chứng) → cảnh báo.
7. Sau cả chuỗi khung (`Exporter.run`):
   - `branch_glitches(mtu)`: MTU nhảy > 12 mm giữa hai khung liền nhau = đường cơ đổi nhánh quấn.
     Đoạn **ở giữa**, ngắn ≤ 12 khung, **ngắn hơn** hai bên (đi tắt qua xương) → NaN. Còn lại → cảnh báo.
   - `fill_gaps`: lỗ NaN ≤ 8 khung nội suy theo thời gian; dài hơn giữ NaN (viewer tô xám).
   - NaN được mã hoá **0** trong `nfl_u16` (xem 05).
8. Xương ảo: bả vai xoay quanh tâm khớp vai Rajagopal, xương đòn quanh khớp ức–đòn, theo **độ
   xoay chênh lệch** của MoBL so với tư thế nghỉ (tư thế MoBL khớp tư thế nghỉ Rajagopal, không
   phải mọi góc = 0).

### Căn hệ trục MoBL ↔ xương hiển thị (chỉ ảnh hưởng hình vẽ)
`assets/upper_align.json` (tự tạo lần đầu, xoá để tính lại):
- `mobl_to_torso`: ICP có co giãn (chặn 0.8–1.25; `_icp_similarity` tự viết vì ICP co giãn của
  trimesh bị co về 0) lồng ngực + bả vai + xương đòn MoBL lên **xương Z-Anatomy đang hiển thị**.
  Hiện tại: co giãn 0.926, sai lệch TB 9 mm.
- `segments`: mỗi đoạn tay MoBL → xương Rajagopal (ICP; cổ tay/bàn tay không co giãn).
  `to_torso(p, body)` chuyển từng điểm đường cơ theo **xương nó bám**.
- Cần `assets/zanat_upper.json` đã tồn tại (dùng xương của nó làm đích).

## 3. "Bị kéo giãn" — `pipeline/stretch.py` (định nghĩa DUY NHẤT)

Với `l` = l/l_opt hiện tại, `l0` = lúc bắt đầu (khung hợp lệ đầu tiên):
```
a = l/l0 − 1                      (dài thêm so với lúc bắt đầu)
b = max(0, l − max(1, l0))        (phần vượt quá CẢ lúc bắt đầu LẪN chiều dài tối ưu)
a ≤ 0:  S = a                     → xanh (ngắn lại)
a > 0:  S = min(a/0.25, 1) + b/0.4 → vàng (đủ màu ở +25%) rồi cam → đỏ khi b > 0
"bị kéo giãn" (xếp hạng, bảng, câu mở đầu)  ⇔  b > 0.02 và a > 5%
rank_key = (round(b, 3), a)
```
JS: `stretchIndex` trong `web/anatomy-core.js` — **phải giữ giống hệt**. Lý do của thang hai bậc
xem 08. Ngưỡng "chùng": l/l_opt < 0.5 (`SLACK`) — viewer ghi "chùng" thay cho số.
