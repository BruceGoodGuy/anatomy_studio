# 06 · Kiểm tra: QA hình học, kiểm chứng, selftest

Không có bộ unit test truyền thống. "Đúng" được bảo vệ bởi ba lớp tự động + soát bằng mắt.

## 1. QA hình học — `pipeline/qa.py` (chạy trong mỗi lần build có QA)
Chạy **đúng phép biến dạng của viewer** trên mọi cơ, mọi bên, mỗi 2 khung (`stride=2`).

| Chỉ số | Lỗi người xem thấy | Ghi chú khi | KHÔNG ĐẠT khi |
|---|---|---|---|
| Tam giác lật (`flips`, bỏ tam giác < 1 mm²) | gai, bẻ vào trong, lỗ | > 0 | > 25 / cơ |
| Cạnh bị kéo dài (`edge_max`) | rách | > x4.5 | > x6 |
| Jacobian âm (`jac_neg`, chỉ thân dưới — trường thể tích) | tự xuyên | > 0% | > 6% đỉnh / cơ |
| Xuyên giữa hai cơ kề nhau (mới so với tư thế nghỉ) | chồng lên nhau | > 4 mm | > 8 mm |

`LIMITS` ở đầu `qa.py`. **Không nới ngưỡng để cho qua** — sửa gắn hình hoặc tư thế mẫu.
`fail` → Studio báo đỏ, khoá tải zip; CLI trả mã 1.

Hiện trạng (6 bài + 25 mẫu): tất cả `warn` (đạt, có ghi chú); tệ nhất: lật 17 (giãn đùi trước),
kéo dài x4.9 (squat sâu), Jacobian âm 5.3%, xuyên 7.9 mm.

```bash
python -m pipeline.qa <slug> | --all [--stride N]
python -m pipeline.qa --selftest      # JS (trích từ anatomy-core.js) == Python, sai khác < 1e-4 mm
```

## 2. Kiểm chứng số liệu — `tools/validate_muscles.py` → `docs/kiem-chung.md`, `.json`
| Tầng | Cách làm | Hiện tại |
|---|---|---|
| A | Gập riêng từng khớp chân từ tư thế đứng; mỗi cơ dài ra/ngắn lại/không đổi (ngưỡng 2 mm / 4 mm) theo giải phẫu | 68/68 |
| B | Điểm bám đầu–cuối đường cơ OpenSim cách hình cơ Z-Anatomy < 25 mm (trừ cơ bám qua gân dài, `LONG_TENDON`); thứ tự bó cơ | 32/32, 4/4 |
| C | Bài thân dưới đã dựng (`output/<slug>`) so với nghiên cứu: Kubo 2019, Geiser 2006, giải phẫu chức năng | 11/11 |
| E1 | Như A cho thân trên, đi qua **cả chuỗi** góc Rajagopal → MoBL (`UPPER_TESTS`) | 81/81 |
| E2 | Như B cho thân trên (`UP_TENDON` cho cơ bám qua gân) | 34/35 (delta sau lệch 26 mm) |
| E3 | Mẫu thân trên đã dựng (`output/_tpl-*`): Maeo 2023 (tam đầu qua đầu > pushdown), kéo xà, chống đẩy, đẩy ngực, curl, dang tay, chèo, các bài giãn | 12/13 (giãn ngực khung cửa: phần đòn chỉ chạm chiều dài tối ưu) |

- Tầng C/E3 cần các bài/mẫu **đã dựng** — chạy `python tools/build_all.py all` trước.
- Câu `sentence` trong `kiem-chung.json` được chèn vào mỗi viewer lúc build → sau khi kiểm chứng
  lại, **dựng lại các bài** trong `exercises/` để câu cập nhật.
- Kết quả không đạt được giữ nguyên và giải thích (`UPPER_NOTES`), **không** chỉnh tư thế hay ngưỡng
  cho khớp. Muốn thêm kỳ vọng: chỉ thêm điều có nguồn (sách giải phẫu chức năng, bài báo) và ghi nguồn trong `SOURCES`.
- Chú ý: E1 cố ý dùng gập vai **60°** (không phải 90°) vì trên 60° cánh tay đòn của quạ cánh tay /
  ngực lớn bó đòn đổi dấu; và xoay cẳng tay chỉ tới trung tính vì cơ ngửa của MoBL quấn sai khi úp hẳn.

## 3. Soát bằng mắt (bắt buộc khi đổi hiển thị/gắn hình)
- `tools/dev/template_shots.js "slug1,slug2" three` — chụp phase 0 và 1 của từng bài qua chế độ ảnh.
- `tools/dev/studio_photo_test.js <url> <prefix> "<js>"` — chụp giao diện + một ảnh `snap()`.
- Cần Studio chạy (`python studio.py --no-browser --port 8765`), Playwright + Chromium (swiftshader).
  Đã gặp lỗi chỉ thấy bằng mắt: lưng xô "bung như cánh" khi giơ tay (QA vẫn đạt) → luôn nhìn
  góc sau và 3/4 cho bài thân trên.

## 4. Quy trình trước khi bàn giao / đóng gói
1. Nếu đổi `zbind*.py` hoặc tài sản: chạy lại `python -m pipeline.zbind_upper` (hoặc `zbind`),
   rồi QA nhanh 4 động tác thử thân trên (giơ tay, dang tay, chống đẩy, curl) và vài mẫu:
   `python -m pipeline.build tools/dev/test_motions/_t-*.json --no-qa` rồi
   `python -m pipeline.qa _t-flex _t-abd _t-push _t-curl`.
2. `python tools/build_all.py all` → mọi dòng `pass|warn`, không `fail`.
3. `python tools/validate_muscles.py` → không tụt so với số hiện tại (bảng trên).
4. `python -m pipeline.build exercises/*.json` (để câu kiểm chứng mới vào viewer).
5. `python -m pipeline.qa --selftest`.
6. Soát mắt Studio: mở một bài, kéo thanh trượt, phát, tab Ảnh chụp thử.
7. Xoá `output/_tpl-*`, `output/_t-*`, `output/_q-*`, `__pycache__`; đóng gói không kèm `.venv`.
8. Cập nhật `README.md` (người dùng) và `docs/` (người làm) nếu hành vi đổi.
