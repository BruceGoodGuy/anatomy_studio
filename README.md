# Anatomy Studio

Công cụ chạy trên máy của bạn để tạo **viewer 3D cơ – xương cho từng bài tập** — thân dưới
(squat, RDL, lunge…) lẫn thân trên (chống đẩy, kéo xà, đẩy ngực, cuốn tạ…). Viewer cho
thấy xương chuyển động và cơ đổi màu theo độ giãn, với số liệu tính bằng mô hình cơ – xương
OpenSim. Có **chế độ chụp ảnh** để lấy hình minh hoạ cho bài viết. Bạn tự định nghĩa bài tập bằng vài tư thế then chốt, bấm một nút và nhận về một
file `viewer.html` để đăng blog. Không cần AI, không cần Blender, không cần biết 3D.

---

## 1. Cài đặt

**Windows**

> **Cần Python 3.11, 3.12 hoặc 3.13 (64-bit).** OpenSim 4.6 chỉ có bản cài cho ba phiên bản
> này — Python 3.14 trở lên hoặc 3.10 trở xuống sẽ không cài được. Máy có sẵn Python 3.14 thì
> cứ cài thêm 3.12, hai bản dùng song song được.

1. Cài Python 3.12: vào python.org/downloads/windows, chọn *Python 3.12.x → Windows installer
   (64-bit)*. Hoặc mở cmd và chạy `winget install Python.Python.3.12`.
2. Giải nén thư mục này, bấm đúp `run_studio.bat`.
   File này tự tìm Python 3.12/3.13/3.11 (kể cả khi bản mặc định của máy là 3.14), tạo môi
   trường riêng trong thư mục `.venv` và cài thư viện. Lần đầu mất vài phút, các lần sau mở ngay.
3. Trình duyệt tự mở `http://127.0.0.1:8000`. Nếu không, tự mở địa chỉ đó.
   Nếu cổng 8000 đang bận, Studio tự chuyển sang 8001, 8002… (xem địa chỉ in trong cửa sổ cmd). Nếu Studio đã mở sẵn ở một cửa sổ khác, nó chỉ mở lại trình duyệt chứ không chạy thêm bản thứ hai.

Nếu bước cài bị lỗi (mất mạng…), file tự xoá `.venv` để lần sau cài lại từ đầu. Nếu môi
trường bị thiếu thư viện (ví dụ báo `No module named 'numpy'`), lần chạy sau nó tự tạo lại.

**Linux:** chạy `./run_studio.sh`.

**macOS:** thư viện OpenSim chưa có bản cài bằng `pip` cho Mac. Hãy dùng conda:

```bash
conda create -n studio python=3.12 -y && conda activate studio
conda install -c opensim-org opensim -y
pip install numpy scipy trimesh fast-simplification rtree fastapi uvicorn
python studio.py
```

Tắt Studio: đóng cửa sổ dòng lệnh, hoặc bấm Ctrl+C.

---

## 2. Dùng Studio

### Bố cục

```
┌ Thư viện ┬──────────── Khung 3D ─────────────┬─ Bảng chỉnh ─────────┐
│ bài tập  │  xương + cơ đổi màu theo độ giãn  │ [Tư thế][Bài tập]    │
│          │                                    │ [Xuất bản][Ảnh]      │
│ + Bài mới├──── Thanh thời gian ──────────────┤ thanh trượt theo vùng │
│          │ ▶ Phát  ◆──◆──────◆──────◆ (0→100%)│ cơ thể, mẫu tay…      │
└──────────┴────────────────────────────────────┴──────────────────────┘
```

- **Khung 3D:** kéo để xoay, cuộn để phóng to. Phía trên có:
  - **Cơ**: bật/tắt lớp cơ Z-Anatomy.
  - **Chụp ảnh**: mở chế độ chụp ảnh (tab **Ảnh**, xem bên dưới).
  - **Kéo giãn / l/l_opt / Tự nhiên**: chọn thang màu (mục 5). *Tự nhiên* tô mọi cơ màu thịt — dùng với "Làm mờ cơ không bị kéo giãn" để làm nổi cơ chính.
  - **Nhóm cơ ▾**: bật/tắt từng nhóm; "Làm mờ cơ không bị kéo giãn".
  - **Bóng đầu**: hiện mờ tư thế lúc bắt đầu để so sánh.

  Góc dưới trái liệt kê các cơ *đang bị kéo giãn* ở thời điểm đang xem. Bấm vào một cơ trên mô hình để xem tên và số liệu của nó.
- **Thanh thời gian:** trục 0% → 100% của động tác. Các đường cong là góc gối (liền), hông (gạch), thân nghiêng (chấm); với bài thân trên (tay chuyển động nhiều hơn chân) là góc khuỷu và góc vai. Mỗi ◆ là một **tư thế then chốt**.
  - Kéo trên thanh để xem từng thời điểm.
  - Bấm ◆ để chỉnh tư thế đó; kéo ◆ ở giữa sang ngang để dời nó.
  - **▶ Phát** chạy cả lần lặp (xuống → giữ → lên) đúng nhịp đã đặt.
  - **+ Thêm tư thế tại đây** chèn một tư thế mới đúng vào chuyển động hiện có, rồi chỉnh tiếp.
- **Tab Tư thế:**
  - Thanh trượt nhóm theo vùng: *Chân*, *Thân & chậu*, *Chân phải/trái* (kiểu tự do), *Tay*. Bấm đúp vào tên để trả về mặc định.
  - **Tay** có 7 mẫu dáng sẵn (buông xuôi, duỗi ra trước, ôm tạ trước ngực, khoanh tay, chống hông, hai tay sau đầu, giơ qua đầu) và ô *Giữ tay giống nhau ở mọi tư thế*. Muốn hai tay khác nhau (tạ một tay, giãn một bên…): tab Bài tập → *Hai tay* → **Chỉnh riêng tay trái**, sẽ có thêm nhóm *Tay trái*.
  - Kiểu tự do có thêm *Hai chân giống nhau* và **⇄ Đổi chân**.
  - **Chép / Dán** để chép nguyên một tư thế sang tư thế khác.
  - Ô kiểm tra phía trên báo ngay nếu bàn chân bị trượt, phải chỉnh góc nhiều, hay cổ chân gập quá mức người thật làm được.
- **Tab Bài tập:** tên, chuyên mục, ghi chú, kiểu bài, tuỳ chọn (độ rộng chân, kiểu neo…), nhịp một lần lặp.
- **Tab Xuất bản:**
  - **Xem thử**: bản nháp trang blog, khoảng 5 giây, mở ngay trong Studio.
  - **Tạo bản đăng blog**: bản chính thức có kiểm tra hình học, 30–90 giây, cho tải gói `.zip`.

- **Tab Ảnh (chụp ảnh cho bài viết):** khung sáng trên khung 3D là đúng phần sẽ thành ảnh — xoay/zoom như thường, kéo thanh thời gian để chọn thời điểm.
  - **Kiểu nhanh:** *Bài viết (nền trắng)*, *Nền tối*, *Chỉ cơ, không chữ*, *Xuyên thấu (thấy xương)*.
  - **Khung hình** 1:1, 4:5, 3:4, 9:16, 16:9, 3:2; cạnh dài 1080 → 4320 px (ảnh được vẽ lại ở độ phân giải đó, không phóng to ảnh màn hình). **Căn người vào giữa khung** đặt máy ảnh vừa khít cả động tác.
  - **Nền:** một màu, chuyển màu hai màu, hoặc **trong suốt** (PNG để ghép vào thiết kế khác).
  - **Độ đậm:** cơ, cơ được làm mờ (khi bật "Làm mờ cơ không bị kéo giãn" hoặc khi bấm chọn một cơ), xương — kéo cơ xuống thấp để thấy xương bên trong.
  - **Chữ trên ảnh:** tên các cơ bị kéo giãn nhiều nhất (có đường chỉ tới cơ, chọn 1–8 nhãn), thang màu, tên bài + thời điểm, dòng ghi nguồn (Z-Anatomy CC BY-SA yêu cầu ghi công — nên để bật), lưới sàn.
  - **Tải ảnh PNG**, **Chép ảnh** (dán thẳng vào trình soạn bài), **Tải chuỗi khung** (các tư thế then chốt đặt cạnh nhau, hoặc 0–50–100%). Nút **Đến lúc giãn nhất** nhảy tới thời điểm có nhiều cơ bị kéo giãn nhất.

Phím tắt: **Ctrl+S** lưu · **Ctrl+Z / Ctrl+Y** hoàn tác / làm lại · **Space** phát / dừng · **← →** chuyển tư thế.

### Tạo bài mới trong 4 bước

1. **+ Bài mới** → chọn một **mẫu** gần giống nhất → đặt tên. Có 25 mẫu:
   - thân dưới: squat, goblet squat, sumo squat, RDL, good morning, split squat, RDL một chân, nhón gót;
   - thân trên: chống đẩy, kéo xà tay sấp, chin-up, xà kép (dips), đẩy ngực nằm, đẩy vai qua đầu, dang tạ ngang vai, cuốn tạ tay, duỗi tam đầu qua đầu, đẩy cáp tam đầu, chèo tạ cúi người;
   - giãn cơ: đùi trước, gập người chạm mũi chân, bắp chân, ngực ở khung cửa, tam đầu qua đầu, vai sau (kéo tay ngang ngực).

   Mọi mẫu đều đã qua kiểm tra hình học.
2. Bấm ◆ cuối (100%) → chỉnh tư thế cuối bằng thanh trượt. Khung 3D cập nhật gần như tức thì.
3. **▶ Phát** để xem cả động tác. Muốn đường đi cong theo ý mình thì **+ Thêm tư thế tại đây** ở giữa rồi chỉnh.
4. **Xuất bản → Xem thử** cho tới khi ưng, rồi **Tạo bản đăng blog**.

### Hai kiểu bài

**Đứng hai chân bám sàn** — squat, sumo, RDL, good morning, gập người.

Bạn nhập **gập gối**, **chậu nghiêng trước**, **gập lưng dưới** và **tay**.
Chương trình tự giải **góc hông, cổ chân, độ dạng và xoay hông** sao cho:

- gót đứng yên và bàn chân phẳng trên sàn,
- đúng **độ rộng hai gót** và **góc mũi chân** ở tab Bài tập,
- **khối tâm luôn nằm trên giữa bàn chân**, tức là người không bị ngã.

**Tự đặt từng khớp** — split squat, lunge, đứng một chân, nhón gót, các bài giãn cơ.

Bạn đặt từng khớp cho từng chân, rồi chọn cách **neo** từng bàn chân:

| Kiểu neo | Ý nghĩa |
|---|---|
| Neo cả bàn chân | Bàn chân phẳng, đứng yên trên sàn |
| Neo mũi chân | Gót được nhấc lên (chân sau split squat, nhón gót, chống đẩy) |
| Không neo | Chân tự do, như chân đang nhấc khỏi sàn |

Và cách **neo từng bàn tay**:

| Kiểu neo tay | Ý nghĩa |
|---|---|
| Chống xuống sàn | Bàn tay úp phẳng trên sàn (chống đẩy, plank). Cổ tay tự gập để bàn tay nằm phẳng |
| Nắm cố định | Bàn tay giữ nguyên chỗ (xà đơn, xà kép, tay cầm). Không chân nào chạm đất thì trọng tâm tự nằm ngay dưới chỗ nắm |
| Không neo | Tay theo đúng góc bạn đặt |

Chương trình dời chậu và **chỉnh nhẹ hông – gối – cổ chân của chân được neo** để bàn chân
đứng yên. Nếu phải chỉnh quá 8°, Studio báo khớp nào bị chỉnh bao nhiêu. Khi neo cả tay lẫn
chân (chống đẩy), độ nghiêng thân và góc vai do các điểm neo quyết định: bạn chỉ cần đặt góc
khuỷu, thân xoay quanh mũi chân như tấm ván. Không neo gì cả (đẩy ngực nằm, bài ngồi) thì đặt
*Chậu nghiêng trước* = −90 để nằm ngửa và chỉnh *Độ cao hông*.

### Cảnh báo thường gặp

- **"Cổ chân gập mu quá 45°"** → tăng *chậu nghiêng trước* hoặc giảm *gập gối*.
- **"Bàn chân lệch … cm khỏi chỗ neo"** → các góc mâu thuẫn nhau (ví dụ hông gập nhiều mà gối gập ít).
- **"Phải chỉnh … °"** (kiểu tự do) → đưa góc về gần con số được gợi ý.

---

## 3. Kết quả

Mỗi bài cho ra một thư mục `output/<tên-bài>/`:

| File | Dùng để |
|---|---|
| `viewer.html` | **File để đăng blog.** Một file duy nhất, tự chứa toàn bộ dữ liệu (~4 MB), three.js tải từ CDN. |
| `muscles.csv` | Bảng xếp hạng: cơ nào bị kéo giãn, độ dài lúc đầu / dài nhất, % dài thêm. Mở bằng Excel hoặc Google Sheets. |
| `angles.csv` | Góc khớp theo thời gian, dùng cho bảng hoặc biểu đồ trong bài. |
| `motion.mot` | Chuyển động, mở được bằng OpenSim GUI nếu muốn kiểm tra. |
| `qa.json` | Kết quả kiểm tra chất lượng hình học của cơ (mục 4). |
| `data/` | Dữ liệu rời, nếu muốn tự dựng trang riêng. |
| `_preview.html` | Bản dùng three.js trong máy, chỉ để Studio xem không cần mạng. |

### Đưa lên blog (Astro)

Cách đơn giản nhất là chép `viewer.html` vào `public/viewers/squat.html` rồi nhúng:

```html
<iframe src="/viewers/squat.html" style="width:100%;height:1500px;border:0" loading="lazy"
        title="Viewer 3D: squat kéo giãn cơ nào"></iframe>
```

Trên Cloudflare Pages, file HTML được nén gzip/brotli khi gửi đi, nên ~3–4 MB thực tế còn khoảng 1,5–2 MB khi tải.

### Viewer có gì

- **Xoay 360°:** kéo chuột hoặc một ngón tay. Cuộn hoặc chụm hai ngón để phóng to.
  Chuột phải hoặc hai ngón kéo để dời khung. Nút **Tự xoay** và **Đặt lại** ở góc khung.
- **Góc nhìn có sẵn:** Trước / Nghiêng / Chéo / Sau.
- **Kiểu hiển thị:** *Giải phẫu* (hình cơ Z-Anatomy) hoặc *Đường lực* (đường cơ OpenSim).
- **Màu theo:** *Kéo giãn* (mặc định) hoặc *l/l_opt* — xem mục 5.
- **Bảng nhóm cơ:**
  - biểu tượng mắt để hiện/ẩn nhóm,
  - **Tập trung** để làm nổi một nhóm và làm mờ phần còn lại,
  - bấm tên nhóm để xem từng cơ,
  - bấm một cơ (trong bảng hoặc trên mô hình) để xem nó có bị kéo giãn không, đường cong độ dài
    và thời điểm dài nhất.
- **Thanh thời gian:** kéo để xem từng khung hình; có nút chậm 0.5× và 0.25×.

---

## 4. Hình cơ chuyển động thế nào, và cách kiểm tra lỗi hiển thị

### Cách biến dạng

Mọi cơ dùng **chung một trường biến dạng**. Mỗi điểm trong vùng hông – đùi – cẳng chân có một
bộ trọng số cho các xương (chậu, đùi, chày, thân); điểm sát xương nào thì đi theo xương đó, điểm
nằm giữa hai xương thì trộn mượt chuyển động của cả hai bằng *dual quaternion*. Trọng số là
nghiệm phương trình Laplace với bề mặt xương làm biên — hàm "mượt nhất có thể", đổi dần theo góc
quanh khớp — cộng một đĩa ảo ở giữa đùi và giữa cẳng chân để trọng số không rò từ khớp này sang
khớp kia. Trường dựng sẵn một lần (`python -m pipeline.zbind`), dùng cho mọi bài.

Vì là một trường liên tục dùng chung: cơ **không rách**, cơ **kề nhau đi cùng nhau** (không
xuyên vào nhau), và **không xoắn** (không có hệ trục dọc đường cơ như cách cũ).

**Thân trên** dùng cách khác, vì cơ vai – ngực – lưng xô trải rộng qua nhiều xương và một trường
thể tích làm chúng phồng lên khi giơ tay: mỗi điểm trên hình cơ đi theo **xương mà đoạn đường
cơ gần nó nhất đang bám** (bả vai, xương đòn, cánh tay, cẳng tay…), làm mượt dọc chiều dài cơ, rồi
làm mượt thêm ở mặt tiếp giáp giữa các cơ kề nhau để chúng không tách hay xuyên vào nhau. Bả vai và
xương đòn chuyển động theo mô hình MoBL-ARMS (nhịp bả vai – cánh tay). Dựng một lần bằng
`python -m pipeline.zbind_upper`.

Cách cũ (bản trước) cho mỗi cơ tự bám theo đường cơ OpenSim của riêng nó. Ba lỗi bạn thấy
đều từ đó: phần dưới cơ tứ đầu gắn theo xương chày nên bị bẻ vào trong khi gập gối; hệ trục
dọc đường cơ đùi sau xoay theo xương chày nên cơ bị xoắn; mỗi cơ đi một kiểu nên các nhóm cơ
xuyên vào nhau, và bó nào bám đường nào nhảy cóc giữa các đỉnh kề nhau nên mặt cơ bị xé (ở mông,
gối). Đo ở đáy squat: 50–120 tam giác bị lật mỗi cơ, có cạnh bị kéo dài tới 33 lần.

### Kiểm tra chất lượng tự động

Mỗi lần **Tạo dữ liệu**, `pipeline/qa.py` chạy **đúng phép biến dạng mà viewer chạy** (có test
so sánh viewer JS với bản Python: `python -m pipeline.qa --selftest`) trên mọi cơ, cả hai chân,
các khung hình từ đầu đến cuối, và đo:

| Chỉ số | Lỗi người xem thấy | Ghi chú khi | KHÔNG ĐẠT khi |
|---|---|---|---|
| Tam giác bị lật | gai, cơ "bẻ vào trong", lỗ thủng | > 0 | > 25 trong một cơ |
| Cạnh bị kéo dài | rách | > x4,5 | > x6 |
| Thể tích bị gập ngược | cơ tự xuyên qua chính nó | > 0% | > 6% của một cơ |
| Xuyên giữa hai cơ | các nhóm cơ chồng lên nhau | > 4 mm | > 8 mm |

Ngưỡng ở đầu file `pipeline/qa.py` (`LIMITS`). Ở 6 bài mẫu và 25 mẫu: lật ≤ 17 tam giác nhỏ, kéo
dài ≤ x4,9, gập ngược ≤ 5,3% (chỉ ở nếp háng và khoeo lúc gập sâu nhất), xuyên giữa cơ ≤ 8 mm
(thường ở nách, nơi cơ ngực/lưng xô sát cơ cánh tay) → tất cả ĐẠT, có ghi chú. Cơ thân trên
không có chỉ số "gập ngược" (chỉ áp dụng cho trường trọng số thân dưới).

**Ghi chú "mô bị ép vào nhau ở nếp khớp"** là bình thường ở đáy squat sâu: ngoài đời thịt
đùi ép vào bắp chân, háng gập sát bụng. Viewer vẽ cơ hai mặt nên không bao giờ lộ lỗ thủng.

Kiểm tra lại toàn bộ trước khi đăng:

```bash
python -m pipeline.qa --selftest     # viewer và bản Python cho cùng kết quả
python -m pipeline.qa --all          # mọi bài đã tạo; trả mã lỗi 1 nếu có bài KHÔNG ĐẠT
```

## 5. Đọc số liệu cho đúng, và vì sao tin được

### Màu nghĩa là gì

Mặc định (**Kéo giãn**), một cơ chỉ có màu **cam → đỏ** khi sợi cơ dài hơn **cả** độ dài lúc
bắt đầu động tác **lẫn** chiều dài tối ưu của chính nó, tức là động tác thật sự kéo nó vào vùng giãn.
**Vàng** = đang dài ra nhưng chưa tới chiều dài tối ưu. **Xanh** = ngắn lại. **Be** = gần như không đổi.

Vì sao không tô thẳng theo độ dài? Có hai cách đơn giản, và cả hai đều đánh lừa người đọc:

- Tô theo độ dài tuyệt đối: cơ thon, cơ may, thắt lưng–chậu đã ở mức 1.1–1.2 ngay khi **đứng yên**, nên trông như "squat kéo giãn chúng", trong khi squat không làm chúng dài thêm chút nào.
- Tô theo mức dài thêm: mông lớn **chân sau** của split squat dài thêm 37%, nhưng vẫn **ngắn hơn** chiều dài tối ưu (0.87), tức là chưa hề bị giãn.

Thang hai bậc tránh được cả hai trường hợp. Công thức nằm ở `pipeline/stretch.py` và được dùng
chung cho màu, bảng xếp hạng và `muscles.csv`. Chế độ **l/l_opt** vẫn có, khi bạn muốn bàn
về vị trí trên đường cong lực–chiều dài.

### Các giả định

- **Màu không phải mức kích hoạt cơ.** Chỉ có chuyển động, không có dữ liệu lực.
- **Gân đàn hồi, cơ thả lỏng:** chiều dài sợi cơ tính ở trạng thái cân bằng của mô hình cơ Millard với kích hoạt 1%, tức mức giãn *thụ động*.
  - So với giả định gân cứng (bản trước): thứ tự xếp hạng không đổi, giá trị cuối biên độ thấp hơn tới ~0.15 (ví dụ đùi sau ở đáy RDL: 1.78 → 1.64).
  - Khi cơ đang gồng mạnh, gân giãn thêm nên sợi cơ giãn ít hơn một chút.
- **"Chùng":** khi sợi cơ ngắn dưới 0.5 lần tối ưu (ví dụ thẳng đùi ở đáy RDL), ngoài đời cơ và gân đã chùng. Viewer ghi "chùng" thay cho một con số vô nghĩa.
- **Chuyển động được dựng từ tư thế then chốt, không phải đo.** Hãy nói rõ điều này trong bài.
- **Hình cơ Z-Anatomy là minh hoạ**, chuyển động theo xương. Màu và con số luôn lấy từ đường cơ OpenSim cùng tên.
- **Thân trên dùng mô hình MoBL-ARMS** (mục 5, tầng E). Chưa có cơ thang, cơ trám, răng cưa trước, cơ bụng, cơ dựng sống — các cơ đó không được tô.
- **Mô hình vai có giới hạn:** ở tư thế cực đoan (xoay trong vai > 20°, úp cẳng tay hết cỡ…), vài đường cơ của MoBL-ARMS quấn sai quanh xương. Chương trình phát hiện và **loại các khung đó** (cơ hiện xám, có cảnh báo) thay vì đưa ra con số sai; đoạn ngắn thì nội suy từ hai bên.

### Kiểm chứng tự động — `python tools/validate_muscles.py`

Kết quả ghi ra `docs/kiem-chung.md`; câu tóm tắt tự chèn vào cuối mỗi trang viewer. Kiểm tra ba tầng độc lập:

| Tầng | Kiểm tra gì | Kết quả |
|---|---|---|
| A. Chức năng giải phẫu | Gập riêng từng khớp (hông, gối, cổ chân, dạng hông, duỗi hông): mỗi cơ phải dài ra / ngắn lại / giữ nguyên đúng như sách giải phẫu | 68/68 đúng |
| B. Hình cơ ↔ số liệu | Màu mỗi hình cơ lấy theo **tên** (không thể tô nhầm). Thêm: điểm bám đầu–cuối của đường cơ OpenSim nằm sát hình cơ Z-Anatomy (< 25 mm), thứ tự các bó (mông lớn trên→dưới, mông nhỡ trước→sau…) đúng | 32/32 đường cơ, 4/4 thứ tự bó |
| C. Đối chiếu nghiên cứu | Squat kéo giãn mông lớn, khép lớn, cơ rộng nhưng **không** kéo thẳng đùi, đùi sau dài thêm ít hơn RDL (Kubo et al. 2019); nhị đầu đùi đầu dài dài ra, đầu ngắn ngắn lại khi squat (Geiser et al. 2006); RDL kéo giãn đùi sau mạnh nhất; split squat kéo giãn thẳng đùi chân sau và mông lớn chân trước | 11/11 khớp |
| E1. Thân trên — chức năng | Gập khuỷu, đưa tay ra trước, dang tay, đưa tay ra sau, xoay ngoài vai, xoay cẳng tay: đi qua **cả chuỗi** góc tay → khớp vai MoBL-ARMS → chiều dài cơ | 81/81 đúng |
| E2. Thân trên — vị trí | Điểm bám đường cơ MoBL-ARMS so với hình cơ Z-Anatomy (< 25 mm; cơ bám qua gân dài chỉ xét đầu kia) | 34/35 (delta sau lệch 26 mm ở điểm bám gai vai) |
| E3. Thân trên — bài tập | Duỗi tam đầu qua đầu làm đầu dài dài hơn hẳn pushdown (Maeo et al. 2023); kéo xà: lưng xô dài nhất khi treo thẳng tay; chống đẩy/đẩy ngực: ngực lớn, delta trước dài ra; cuốn tạ, dang tay, chèo tạ, các bài giãn | 12/13 — giãn ngực ở khung cửa: phần ức sườn bị kéo giãn, phần đòn chỉ dài tới đúng chiều dài tối ưu (ghi rõ trong báo cáo, không chỉnh tư thế cho khớp) |

Tầng B còn giải thích một điều bạn có thể thấy ở chế độ *Đường lực*: phần giữa đường cơ OpenSim
có thể lệch khỏi bụng cơ 1–3 cm. Đó là chủ ý của mô hình (các điểm uốn được chọn để cánh tay đòn
mô men đúng như đo trên tử thi), không phải lỗi căn chỉnh. Điểm bám hai đầu thì khớp.

---

## 6. Dòng lệnh (không cần giao diện)

```bash
python -m pipeline.build exercises/squat-khong-ta.json      # tạo một bài (kèm kiểm tra)
python -m pipeline.build exercises/*.json                   # tạo tất cả
python -m pipeline.build exercises/*.json --no-qa           # bỏ bước kiểm tra (nhanh, chỉ để thử)
```

Định dạng file bài tập (`exercises/*.json`):

```json
{
  "name": "Squat không tạ",
  "category": "Gym from zero",
  "mode": "standing",
  "timing": {"hold": 0.3, "down": 2.0, "pause": 0.4, "up": 1.4},
  "options": {"stance_width_cm": 32, "toe_out_deg": 15},
  "keyframes": [
    {"phase": 0, "knee_flexion": 0,   "pelvis_anterior_tilt": 0,  "lumbar_flexion": 0,
     "arm_flexion": 85, "arm_abduction": 0, "arm_rotation": 0, "elbow_flexion": 6, "forearm_rotation": 0},
    {"phase": 1, "knee_flexion": 120, "pelvis_anterior_tilt": 30, "lumbar_flexion": 10,
     "arm_flexion": 85, "arm_abduction": 0, "arm_rotation": 0, "elbow_flexion": 6, "forearm_rotation": 0}
  ],
  "notes": "Hiện dưới tiêu đề trang."
}
```

Danh sách đầy đủ các cột và tuỳ chọn, kèm khoảng giá trị, nằm ở đầu file `pipeline/motion.py`
(`COLUMNS`, `ARM_COLUMNS`, `OPTIONS`, `ARM_PRESETS`). Cột nào thiếu thì lấy giá trị mặc định.
Mẫu bài cho hộp thoại "Bài mới" nằm trong `templates/` (cùng định dạng, thêm khối `"template"`).

---

## 7. Cấu trúc thư mục

```
studio.py               ứng dụng Studio (FastAPI)
run_studio.bat / .sh    chạy nhanh
exercises/              bài tập của bạn (JSON)
templates/              mẫu cho hộp thoại "Bài mới"
output/                 kết quả từng bài
docs/                   tài liệu cho người/AI làm tiếp (bắt đầu từ docs/README.md, AGENTS.md)
docs/kiem-chung.md      báo cáo kiểm chứng vùng cơ (tools/validate_muscles.py tạo)
pipeline/
  motion.py             tư thế then chốt → chuyển động (bộ giải đứng hai chân + IK mềm)
  export.py             chuyển động → đường cơ, chiều dài sợi cơ (gân đàn hồi), vị trí xương
  stretch.py            định nghĩa "cơ bị kéo giãn" dùng chung cho màu, xếp hạng, bảng số
  build.py              ghép tất cả thành output/<bài>/
  skin.py               trường trọng số + dual quaternion skinning (bản tham chiếu của viewer)
  qa.py, qa_metrics.py  kiểm tra chất lượng hình học
  zbind.py              dựng trường trọng số, lưới cơ, gắn Z-Anatomy vào OpenSim (chạy một lần)
  upper.py              thân trên: ghép góc tay → mô hình MoBL-ARMS, chiều dài cơ, đường cơ, bả vai
  zbind_upper.py        gắn cơ Z-Anatomy thân trên (trọng số theo đường lực; chạy một lần)
  geometry.py           xương OpenSim → assets/osim.bones.json (chạy một lần)
  muscle_names.py       tên cơ tiếng Việt / Latin, nhóm cơ
web/
  viewer.html           mẫu trang viewer (blog)
  anatomy-core.js       lõi hiển thị cơ dùng chung cho viewer và Studio (build chèn vào viewer)
  studio.html           giao diện Studio
  vendor/three/         three.js (MIT) để Studio chạy không cần mạng
assets/
  model/                mô hình OpenSim RajagopalLaiUhlrich2023 + MoBL-ARMS (cơ Millard) + hình xương
  zanat_upper.json      mesh cơ Z-Anatomy thân trên + trọng số xương
  upper_align.json      phép căn MoBL-ARMS ↔ bộ xương đang hiển thị (tự tạo)
  zanat_binding.json    mesh cơ Z-Anatomy + trọng số xương (viewer dùng)
  zanat_field.npz       trường trọng số trên lưới 3D (bộ kiểm tra dùng)
tools/validate_muscles.py  kiểm chứng vùng cơ (giải phẫu, vị trí hình cơ, đối chiếu nghiên cứu)
tools/build_all.py         dựng + kiểm tra hàng loạt (bài và mẫu)
tools/make_templates_*.py  nguồn của templates/ (sửa ở đây rồi chạy lại)
tools/dev/                 kịch bản chụp Studio (Playwright) + 4 động tác thử thân trên
tools/extract_zanatomy.py  trích lại mesh từ FBX Z-Anatomy (cần `pip install bpy`)
tools/extract_zanatomy_upper.py  như trên, cho cơ thân trên
tools/mobl_to_millard.py   chuyển cơ của MoBL-ARMS sang mô hình cơ Millard 2012
```

**Muốn thêm cơ Z-Anatomy khác?** Sửa danh sách trong `tools/extract_zanatomy.py` và bảng
`MAP` trong `pipeline/zbind.py`, rồi chạy:

```bash
pip install pyamg pymeshlab          # chỉ cần cho bước này
python tools/extract_zanatomy.py MuscularSystem100.fbx SkeletalSystem100.fbx --out assets/zanat_lowerlimb.npz
python -m pipeline.zbind
python -m pipeline.build exercises/*.json   # tạo lại các bài và kiểm tra
```

---

## 8. Giấy phép và trích dẫn (ghi ở cuối bài blog)

- **Mô hình:**
  - Rajagopal A. et al. (2016), *IEEE Trans Biomed Eng*, doi:10.1109/TBME.2016.2586891
  - Millard M. et al. (2013), *J Biomech Eng*, doi:10.1115/1.4023390 (mô hình cơ – gân)
  - Lai A.K.M. et al. (2017), *Ann Biomed Eng*, doi:10.1007/s10439-017-1920-7
  - Uhlrich S.D. et al. (2022), *Sci Rep*, doi:10.1038/s41598-022-13386-9

  - Saul K.R. et al. (2015), *Comput Methods Biomech Biomed Engin* 18(13):1445–1458 (MoBL-ARMS)
  - Holzbaur K.R.S. et al. (2005), *Ann Biomed Eng* 33(6):829–840 (mô hình chi trên gốc)

  Lấy từ kho opensim-org/opensim-models và stanfordnmbl/osim-rl (MoBL-ARMS; cơ đã đổi sang mô hình
  Millard bằng `tools/mobl_to_millard.py`, hình học giữ nguyên). Trước khi đăng công khai, kiểm tra điều khoản trên
  trang SimTK của dự án full_body.
- **Hình cơ và xương Z-Anatomy:** CC BY-SA 4.0. Phải ghi nguồn, và các mesh đã chỉnh sửa
  (`assets/zanat_binding.json`, phần dữ liệu trong `viewer.html`) cũng chia sẻ theo CC BY-SA 4.0.
- **Kiểm chứng:** Kubo K. et al. (2019), *Eur J Appl Physiol* 119:1933–1942; Geiser C. et al. (2006), ISBS Proceedings; Maeo S. et al. (2023), *Eur J Sport Sci* 23(7):1240–1250.
- **three.js:** giấy phép MIT.
- **OpenSim:** giấy phép Apache 2.0.
