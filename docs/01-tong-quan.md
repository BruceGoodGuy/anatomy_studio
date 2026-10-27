# 01 · Tổng quan

## Sản phẩm là gì

Một công cụ **chạy trên máy cá nhân** (Windows là chính, Linux/macOS được) để tác giả blog
tiếng Việt *From Zero* (chuyên mục Lifestyle / Gym from zero / Running from zero; blog dựng bằng
Astro, host trên Cloudflare) tự tạo **viewer 3D cơ – xương cho từng bài tập**:

- Người dùng đặt vài **tư thế then chốt** bằng thanh trượt (gối, chậu, tay…), không cần biết 3D.
- Chương trình dựng chuyển động hợp lý về vật lý (bàn chân đứng yên, khối tâm trên bàn chân,
  tay chống sàn/nắm xà đứng yên…), chạy qua mô hình cơ – xương OpenSim, tính **chiều dài sợi cơ**
  từng khung hình.
- Xuất **một file `viewer.html`** tự chứa (≈4 MB, three.js từ CDN) để nhúng vào blog bằng iframe:
  xương chuyển động, hình cơ Z-Anatomy đổi màu theo mức bị kéo giãn, bảng xếp hạng cơ, phần
  "Số liệu này đến từ đâu".
- **Chế độ chụp ảnh** trong Studio để xuất PNG minh hoạ cho bài viết.

Không dùng AI khi chạy, không cần Blender (Blender chỉ dùng một lần để trích mesh, kết quả đã có
sẵn trong `assets/`).

## Nguyên tắc số một: đúng trước, đẹp sau

Câu của chủ dự án: *"Nếu sai thì bài blog không còn ý nghĩa gì."* Hệ quả cụ thể:

1. **Màu và con số luôn lấy từ mô hình OpenSim**, không bao giờ từ hình 3D. Hình Z-Anatomy chỉ
   là minh hoạ, được tô theo **tên** cơ.
2. **Không bịa số khi mô hình hỏng.** Khung nào đường cơ quấn sai quanh xương → loại số liệu
   khung đó (cơ hiện xám, có cảnh báo) thay vì nội suy dài hay đoán.
3. **Định nghĩa "bị kéo giãn" thận trọng** (thang hai bậc, `pipeline/stretch.py`): chỉ tô cam–đỏ
   khi sợi cơ dài hơn *cả* lúc bắt đầu *lẫn* chiều dài tối ưu.
4. **Kiểm chứng tự động** trước mỗi lần đóng gói (`tools/validate_muscles.py`): chức năng giải phẫu,
   vị trí hình cơ, đối chiếu nghiên cứu. Kết quả không đạt được **ghi rõ**, không chỉnh tư thế/
   ngưỡng để "cho qua" (ví dụ bài giãn ngực ở khung cửa: 12/13).
5. **QA hình học** mỗi lần tạo bài: hình cơ không được rách, lật, xuyên vào nhau quá ngưỡng.
6. Nói rõ giả định trong viewer: chuyển động dựng từ tư thế then chốt (không đo), màu không phải
   mức kích hoạt, gân đàn hồi + cơ thả lỏng.

## Trạng thái hiện tại (cuối 10/2026)

| Phần | Trạng thái |
|---|---|
| Thân dưới (Rajagopal–Lai–Uhlrich 2023, 80 cơ chân) | Ổn định. Kiểm chứng A 68/68, B 32/32 + 4/4, C 11/11 |
| Thân trên (MoBL-ARMS, 35 cơ tay–vai–ngực–lưng xô) | Mới, chạy được. E1 81/81, E2 34/35, E3 12/13 |
| Bộ giải đứng hai chân | Ổn định |
| Bộ giải tự do: neo chân (phẳng/mũi), neo tay (sàn/xà), nằm, tay trái riêng | Mới, chạy được |
| Studio (thư viện, tư thế, thời gian, hoàn tác, mẫu, xuất bản, chụp ảnh) | Chạy được |
| 25 mẫu bài (11 thân dưới/giãn chân, 14 thân trên/giãn tay) | Đều qua QA |
| 6 bài ví dụ trong `exercises/` (squat, RDL, split squat…) | Đều qua QA |
| Cơ thang, trám, răng cưa trước, bụng, dựng sống | **Chưa có** (không có trong cả hai mô hình) |

## Người dùng và môi trường

- Một người dùng (chủ blog), không phải lập trình viên 3D. UX phải tự giải thích, tiếng Việt.
- Máy Windows; chạy bằng `run_studio.bat` (tự tìm Python 3.11–3.13 vì OpenSim 4.6 chỉ có wheel
  cho các bản đó, tự tạo `.venv`). Cổng mặc định 8000, tự nhảy cổng nếu bận.
- Trang viewer nhúng vào Astro bằng `<iframe>`; Cloudflare nén gzip/brotli (~1,5–2 MB thực tải).

## Giấy phép (ảnh hưởng tới việc phân phối)

- Hình cơ/xương **Z-Anatomy: CC BY-SA 4.0** → phải ghi nguồn; dữ liệu mesh đã chỉnh
  (`assets/zanat_*.json`, phần dữ liệu trong `viewer.html`) cũng chia sẻ theo CC BY-SA.
  Viewer và ảnh chụp có dòng ghi nguồn mặc định.
- Mô hình OpenSim: Rajagopal (opensim-models), MoBL-ARMS (từ `stanfordnmbl/osim-rl`) — cần kiểm
  tra điều khoản SimTK trước khi đăng công khai.
- three.js MIT, OpenSim Apache 2.0.
