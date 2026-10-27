# Tài liệu bối cảnh dự án — Anatomy Studio

Bộ tài liệu này mô tả **toàn bộ** dự án để một người (hoặc một AI) chưa từng thấy code có thể
tiếp tục phát triển mà không phải đoán. Viết cho người làm tiếp, không phải cho người dùng cuối
(hướng dẫn sử dụng nằm ở `README.md` ở thư mục gốc).

Đọc theo thứ tự nếu mới vào; tra cứu theo chủ đề nếu đã quen.

| File | Nội dung | Đọc khi |
|---|---|---|
| [01-tong-quan.md](01-tong-quan.md) | Mục tiêu, người dùng, nguyên tắc "đúng trước, đẹp sau", trạng thái hiện tại | Luôn đọc đầu tiên |
| [02-kien-truc.md](02-kien-truc.md) | Sơ đồ khối, luồng dữ liệu, bản đồ từng file, tài sản (assets) | Trước khi sửa bất cứ gì |
| [03-pipeline-so-lieu.md](03-pipeline-so-lieu.md) | Bộ giải chuyển động, tính chiều dài cơ (thân dưới + thân trên MoBL-ARMS), định nghĩa "bị kéo giãn" | Sửa `pipeline/motion.py`, `export.py`, `upper.py`, `stretch.py` |
| [04-hien-thi.md](04-hien-thi.md) | Gắn hình cơ Z-Anatomy, biến dạng (DQS), viewer blog, Studio, chế độ chụp ảnh | Sửa `web/*`, `zbind*.py`, `skin.py` |
| [05-dinh-dang-du-lieu.md](05-dinh-dang-du-lieu.md) | JSON bài tập, mẫu, `motion.json`, file trong `output/`, API của Studio | Thêm cột/tuỳ chọn, đổi định dạng |
| [06-kiem-tra.md](06-kiem-tra.md) | QA hình học, kiểm chứng giải phẫu/nghiên cứu, selftest, quy trình test | Trước khi báo "xong" |
| [07-quy-uoc-va-bay.md](07-quy-uoc-va-bay.md) | Quy ước góc, hệ trục, mã hoá; các bẫy đã gặp | Khi kết quả "lạ" |
| [08-nhat-ky-quyet-dinh.md](08-nhat-ky-quyet-dinh.md) | Vì sao chọn cách hiện tại, các cách đã thử và bỏ | Trước khi đề xuất làm lại theo cách khác |
| [09-viec-con-lai.md](09-viec-con-lai.md) | Hạn chế đã biết, việc nên làm tiếp (có ưu tiên) | Chọn việc để làm |
| [10-lam-viec-nhieu-ai.md](10-lam-viec-nhieu-ai.md) | Chia việc giữa nhiều AI/người, vùng sở hữu, bất biến, checklist bàn giao | Khi nhiều tác nhân làm song song |
| [kiem-chung.md](kiem-chung.md) | Báo cáo kiểm chứng tự động (do `tools/validate_muscles.py` sinh ra — **không sửa tay**) | Trích dẫn trong blog |

Tóm tắt một câu: *Studio cục bộ (FastAPI + Three.js) biến vài tư thế then chốt thành một trang
`viewer.html` 3D cho blog, trong đó màu từng cơ là chiều dài sợi cơ tính bằng mô hình OpenSim
(Rajagopal cho thân dưới, MoBL-ARMS cho thân trên), vẽ trên hình cơ Z-Anatomy.*

Ngôn ngữ: giao diện, chú thích code và tài liệu bằng **tiếng Việt** (blog tiếng Việt); tên biến,
hàm, khoá JSON bằng tiếng Anh. Giữ nguyên quy ước này.
