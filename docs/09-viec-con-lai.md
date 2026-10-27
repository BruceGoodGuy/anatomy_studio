# 09 · Hạn chế đã biết và việc nên làm tiếp

Ưu tiên: **P1** ảnh hưởng tính đúng hoặc bài blog sắp viết · **P2** chất lượng/trải nghiệm rõ rệt · **P3** nên có.

## Tính đúng của số liệu
| Ưu tiên | Việc | Ghi chú |
|---|---|---|
| P1 | **Thiếu cơ**: thang, trám, răng cưa trước, bụng, dựng sống, chậu–sườn… | Không có trong Rajagopal lẫn MoBL. Hướng (ứng viên, chưa kiểm tra giấy phép/độ phù hợp): các mô hình cột sống–thân của OpenSim (Christophy 2012, Bruno 2015, Raabe & Chaudhari 2016), ghép theo cách đã làm với MoBL. Ảnh hưởng bài kéo xà, chèo, plank, deadlift. Khi chưa có, viewer phải tiếp tục ghi rõ là thiếu. |
| P1 | Câu hỏi giãn ngực khung cửa (E3 12/13): phần đòn ngực lớn chỉ tới chiều dài tối ưu | Xem lại bằng tư thế tay thấp hơn/ra sau hơn có nguồn tham chiếu; không chỉnh để khớp. |
| P2 | Cơ ngửa (SUP) NaN khi úp cẳng tay; ECRL, EDCM quấn kém quanh cổ tay | Lỗi mặt quấn MoBL. Có thể sửa mặt quấn trong `MoBL_ARMS_millard.osim` rồi chạy lại E1/E2. |
| P2 | Vai ngoài vùng kiểm chứng (`shoulder_rot > 20°`) và đổi nhánh quấn (tròn lớn, quạ cánh tay, lưng xô bó dưới) | Đã cảnh báo/loại; cân nhắc nhóm "kém tin cậy" trong bảng của viewer. |
| P2 | E2: delta sau lệch 26 mm ở gai vai | Có thể do hình bả vai Z-Anatomy vs MoBL; xem `upper_align.json`. |
| P3 | Chỉ một mô hình người (nam ~1.70 m) | Không scale theo người dùng. |

## Chuyển động
| Ưu tiên | Việc | Ghi chú |
|---|---|---|
| P2 | Kéo xà/chin-up: hình học đỉnh phụ thuộc độ rộng nắm; mẫu đã chỉnh để qua QA | Cân nhắc cho người dùng đặt "cằm qua xà" thay vì góc khuỷu. |
| P2 | Bài nằm (đẩy ngực): không có ghế, chân lơ lửng theo góc đặt | Thêm neo "lưng trên ghế" / "chân trên sàn" khi nằm. |
| P3 | Neo "đầu gối" (quỳ, chống đẩy gối), neo "mông" (ngồi) | Mở rộng `_free_eval`. |
| P3 | Nghiêng/xoay thân sang bên (lateral flexion, rotation) | Chưa có cột; cần cho bài giãn lưng xô một bên, woodchop. |
| P3 | Tạ/dụng cụ hiển thị (thanh đòn, tạ đơn, xà) | Chỉ minh hoạ. |

## Hiển thị / Studio / viewer
| Ưu tiên | Việc | Ghi chú |
|---|---|---|
| P2 | Viewer blog: thanh tiến trình/`angles.csv` chỉ có góc chân | Thêm góc vai/khuỷu cho bài thân trên (Studio đã có `S.armView`). |
| P2 | Viewer blog: bài không đối xứng liệt kê cả (phải)/(trái) trong câu mở đầu | Gộp khi hai bên gần bằng nhau. |
| P2 | Chế độ ảnh trong **viewer blog** (người đọc tự chụp) | Hiện chỉ trong Studio; `paintOverlay`/`snap` có thể chuyển sang `anatomy-core.js`. |
| P3 | Nhãn ảnh: tránh chồng nhau khi nhiều cơ cùng phía | Hiện dàn theo cột, đủ dùng ≤ 6 nhãn. |
| P3 | Huy hiệu "Đang tính chuyển động…" che nút HUD ở cửa sổ hẹp | CSS. |
| P3 | Bộ test tự động cho giao diện (Playwright) chạy được trong CI | Có kịch bản trong `tools/dev/`, chưa có khẳng định (assert). |
| P3 | Hiệu năng: xem trước bài chống đẩy ~7 s | Giảm số mẫu khi đang kéo thanh trượt; cache theo phần tư thế không đổi. |

## Phân phối
| Ưu tiên | Việc |
|---|---|
| P1 | Kiểm tra điều khoản SimTK của Rajagopal và MoBL-ARMS trước khi đăng công khai. |
| P2 | Bản cài macOS (conda) chưa thử trên máy thật. |
