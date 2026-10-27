# 08 · Nhật ký quyết định

Ghi lại *vì sao* — để không ai làm lại một cách đã thử và bỏ. Mới nhất ở cuối.

## Số liệu
| Quyết định | Lý do / cách đã bỏ |
|---|---|
| Mô hình thân dưới **RajagopalLaiUhlrich2023** | Chuẩn OpenSim, chỉnh cho gập gối/hông sâu (squat). |
| **Gân đàn hồi + cơ thả lỏng** (Millard, kích hoạt 1%, `equilibrateMuscles`) | Gân cứng đánh giá quá mức giãn ở cuối biên độ (đùi sau đáy RDL 1.78 → 1.64). Thứ tự xếp hạng không đổi. |
| **Thang "kéo giãn" hai bậc** (`stretch.py`) | Tô theo l/l_opt tuyệt đối: cơ thon, may, thắt lưng–chậu đã 1.1–1.2 khi đứng yên → trông như squat kéo giãn chúng (sai). Tô theo % dài thêm: mông lớn chân sau split squat +37% nhưng vẫn < tối ưu (0.89) → trông như giãn (sai). Bản trước đó tô mọi thay đổi nhỏ cũng có màu → đã sửa để vài % gần như không màu. |
| Thân trên bằng **MoBL-ARMS** ghép vào Rajagopal | Tay Rajagopal không có cơ. MoBL là mô hình chi trên chuẩn, có nhịp vai–cánh tay. |
| Ghép tư thế bằng **hướng** cánh tay + cẳng tay, không chép góc | Hai mô hình dùng quy ước góc vai khác nhau; hướng trong hệ trục thân là bất biến. |
| Cơ MoBL đổi sang **Millard** | Schutte1993 (gốc) cân bằng không tin cậy. |
| `assemble` trước mỗi lần đo MoBL | OpenSim nhớ phía quấn → kết quả phụ thuộc thứ tự khung. |
| Quấn sai → **NaN/xám**, không đoán | Nguyên tắc đúng trước. Lỗ ≤ 8 khung mới nội suy. |
| Phát hiện **đổi nhánh quấn** (`branch_glitches`), chỉ loại đoạn giữa ngắn và *ngắn hơn* hai bên | Đi tắt qua xương làm đường cơ ngắn hụt; đoạn ở hai đầu không biết bên nào đúng → chỉ cảnh báo. |
| Mẫu kéo xà treo với **xoay ngoài −45°** | Dang 155–165° xoay 0 nằm ngoài vùng MoBL kiểm chứng và rơi vào nhánh quấn sai của tròn lớn (lưng xô/tròn lớn ra *dài hơn ở đỉnh* — vô lý). |
| Ánh xạ **cổ tay** sang MoBL | Chống đẩy duỗi cổ tay ~90°; bỏ qua thì số cơ cẳng tay sai. |
| E1 dùng gập vai 60°, xoay cẳng tay tới trung tính | Trên 60° cánh tay đòn quạ cánh tay/ngực lớn bó đòn đổi dấu (thật và trong mô hình); cơ ngửa MoBL quấn sai khi úp hẳn. |
| Giữ ✗ cho giãn ngực khung cửa | Không chỉnh tư thế để khớp kỳ vọng. |

## Bộ giải chuyển động
| Quyết định | Lý do |
|---|---|
| Standing: giải hông, cổ chân, dạng/xoay hông, vị trí chậu; ràng buộc **khối tâm trên bàn chân** | Người dùng chỉ cần nghĩ về gối, chậu, lưng; tư thế luôn đứng được. |
| Free: **IK mềm** (neo cứng + kéo nhẹ về góc người dùng) | Người dùng đặt góc không khớp nhau là chuyện thường; báo khớp nào phải chỉnh bao nhiêu. |
| Neo tay sàn/xà; nghiêng thân là ẩn số khi neo cả tay lẫn chân | Chống đẩy: thân phải xoay quanh mũi chân. |
| Cổ tay giải **sau** (dò 1 chiều) | Đưa vào bài toán chung làm thân trượt và cổ chân bẻ −70°. |
| Không giải xoay vai | Có nghiệm thứ hai "khuỷu chỉ ra ngoài". Xoay vai là góc người dùng đặt. |
| Treo xà: khối tâm dưới chỗ nắm | Nếu không, thân trôi tự do theo trục x. |

## Hiển thị
| Quyết định | Lý do / cách đã bỏ |
|---|---|
| Hình cơ **Z-Anatomy** (CC BY-SA), tô theo tên | Hình đẹp, chuẩn giải phẫu; số liệu vẫn từ OpenSim. |
| Thân dưới: **một trường trọng số điều hoà chung** + DQS | Cách đầu tiên cho mỗi cơ bám theo đường cơ riêng: tứ đầu bị bẻ vào trong khi gập gối, đùi sau xoắn, cơ xuyên nhau, mặt cơ xé (50–120 tam giác lật/cơ, cạnh x33). |
| Thân trên: **trọng số theo đường lực**, không dùng trường thể tích | Trường điều hoà theo khoảng cách gán phần dưới ngực/lưng xô cho xương cánh tay vì tay buông sát thân → giơ tay là phồng (lật 1 428 tam giác, x65). |
| Làm mượt chéo theo nhóm (thân / tay–vai), `SOLO` cho tròn lớn, tròn bé | Không làm mượt chéo: cơ chồng nhau xuyên 13 mm. Nối thân với tay: ngực/lưng xô bị kéo theo tay. Nối tròn lớn: nhận trọng số rò (x6.8). Bỏ đầu ngắn nhị đầu ra khỏi nhóm: xuyên 9 mm. |
| Lưng xô qua bả vai coi là bám thân | Gắn theo bả vai làm cả tấm lưng xô bung ra như cánh khi giơ tay (QA vẫn đạt — chỉ thấy bằng mắt). |
| Bụng đầu ngắn nhị đầu không theo xương quay | Hình Z-Anatomy dừng cách chỗ bám ~7 cm; theo xương quay → rách x7 khi tay qua đầu + gập khuỷu sâu. Tăng sigma thay vì vậy làm hỏng delta trước/tròn bé qua làm mượt chéo. |
| Căn MoBL vào **xương đang hiển thị** + từng đoạn tay theo xương | Căn bằng lồng ngực Rajagopal (bản đầu, tỉ lệ 0.861) làm đường cơ lệch 3–7 cm khỏi hình (E2 chỉ 3/35). Hiện 34/35. |
| Bả vai/xương đòn là **xương ảo** quay theo MoBL quanh khớp vai / ức–đòn | Rajagopal không có bả vai rời; nếu đứng yên, delta/chóp xoay rách khi giơ tay. |
| Trang blog **một file** | Astro chép vào `public/`; tránh đường dẫn tương đối hỏng. |

## Studio
| Quyết định | Lý do |
|---|---|
| FastAPI cục bộ + một file HTML, không framework build | Người dùng chỉ bấm đúp `.bat`; không cần Node. |
| API xem trước đồng bộ + `LOCK`; tối đa một yêu cầu chuyển động đang chạy | Async chặn vòng sự kiện làm nút Lưu chậm; xếp hàng yêu cầu cũ làm treo. |
| Cổng tự nhảy, nhận ra Studio đang chạy | Lỗi 10048 trên Windows khi mở hai lần. Linux: `SO_REUSEADDR`, Windows: `SO_EXCLUSIVEADDRUSE` để kiểm tra cổng. |
| Chế độ ảnh vẽ lại ở độ phân giải đầu ra bằng `setViewOffset` | Phóng ảnh chụp màn hình bị mờ; ảnh phải trùng khung người dùng thấy. |
| Ghi nguồn bật mặc định trên ảnh | Z-Anatomy CC BY-SA yêu cầu ghi công. |
