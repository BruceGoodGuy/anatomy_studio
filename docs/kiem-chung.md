# Kiểm chứng vùng cơ hiển thị

Tạo tự động bởi `tools/validate_muscles.py`. Mô hình: Rajagopal 2016 + Lai 2017 + Uhlrich 2022 (OpenSim). Chiều dài sợi cơ: gân đàn hồi, cơ thả lỏng (kích hoạt 1%).

## A. Chức năng giải phẫu (gập riêng từng khớp từ tư thế đứng)

**68/68 khớp đúng.** Thay đổi là chiều dài cơ + gân (mm).

| Thao tác | Cơ | Kỳ vọng | Mô hình | Đúng |
|---|---|---|---:|:---:|
| Gập hông 60° | Mông lớn – bó trên | dài ra | +46.4 | ✓ |
| Gập hông 60° | Mông lớn – bó giữa | dài ra | +55.1 | ✓ |
| Gập hông 60° | Mông lớn – bó dưới | dài ra | +74.8 | ✓ |
| Gập hông 60° | Nhị đầu đùi – đầu dài | dài ra | +61.6 | ✓ |
| Gập hông 60° | Bán màng | dài ra | +54.8 | ✓ |
| Gập hông 60° | Bán gân | dài ra | +65.3 | ✓ |
| Gập hông 60° | Khép lớn – phần ụ ngồi | dài ra | +58.0 | ✓ |
| Gập hông 60° | Cơ chậu | ngắn lại | -39.8 | ✓ |
| Gập hông 60° | Thắt lưng lớn | ngắn lại | -29.5 | ✓ |
| Gập hông 60° | Thẳng đùi | ngắn lại | -48.3 | ✓ |
| Gập hông 60° | Cơ may | ngắn lại | -56.3 | ✓ |
| Gập hông 60° | Căng mạc đùi | ngắn lại | -58.2 | ✓ |
| Gập hông 60° | Rộng ngoài | không đổi | +0.0 | ✓ |
| Gập hông 60° | Rộng trong | không đổi | +0.0 | ✓ |
| Gập hông 60° | Rộng giữa | không đổi | +0.0 | ✓ |
| Gập hông 60° | Nhị đầu đùi – đầu ngắn | không đổi | +0.0 | ✓ |
| Gập hông 60° | Cơ dép | không đổi | +0.0 | ✓ |
| Gập hông 60° | Bụng chân – đầu trong | không đổi | +0.0 | ✓ |
| Gập hông 60° | Bụng chân – đầu ngoài | không đổi | +0.0 | ✓ |
| Gập gối 60° | Rộng ngoài | dài ra | +42.8 | ✓ |
| Gập gối 60° | Rộng trong | dài ra | +41.0 | ✓ |
| Gập gối 60° | Rộng giữa | dài ra | +42.6 | ✓ |
| Gập gối 60° | Thẳng đùi | dài ra | +46.7 | ✓ |
| Gập gối 60° | Nhị đầu đùi – đầu dài | ngắn lại | -29.8 | ✓ |
| Gập gối 60° | Nhị đầu đùi – đầu ngắn | ngắn lại | -22.2 | ✓ |
| Gập gối 60° | Bán màng | ngắn lại | -36.9 | ✓ |
| Gập gối 60° | Bán gân | ngắn lại | -46.2 | ✓ |
| Gập gối 60° | Cơ thon | ngắn lại | -32.5 | ✓ |
| Gập gối 60° | Cơ may | ngắn lại | -24.7 | ✓ |
| Gập gối 60° | Bụng chân – đầu trong | ngắn lại | -15.4 | ✓ |
| Gập gối 60° | Bụng chân – đầu ngoài | ngắn lại | -18.4 | ✓ |
| Gập gối 60° | Mông lớn – bó trên | không đổi | +0.0 | ✓ |
| Gập gối 60° | Mông lớn – bó giữa | không đổi | +0.0 | ✓ |
| Gập gối 60° | Cơ chậu | không đổi | +0.0 | ✓ |
| Gập gối 60° | Thắt lưng lớn | không đổi | +0.0 | ✓ |
| Gập gối 60° | Cơ dép | không đổi | +0.0 | ✓ |
| Gập gối 60° | Khép dài | không đổi | +0.0 | ✓ |
| Gập mu cổ chân 20° | Cơ dép | dài ra | +13.3 | ✓ |
| Gập mu cổ chân 20° | Bụng chân – đầu trong | dài ra | +14.3 | ✓ |
| Gập mu cổ chân 20° | Bụng chân – đầu ngoài | dài ra | +14.4 | ✓ |
| Gập mu cổ chân 20° | Chày sau | dài ra | +2.6 | ✓ |
| Gập mu cổ chân 20° | Gấp các ngón dài | dài ra | +2.1 | ✓ |
| Gập mu cổ chân 20° | Gấp ngón cái dài | dài ra | +4.1 | ✓ |
| Gập mu cổ chân 20° | Chày trước | ngắn lại | -15.2 | ✓ |
| Gập mu cổ chân 20° | Duỗi các ngón dài | ngắn lại | -12.9 | ✓ |
| Gập mu cổ chân 20° | Duỗi ngón cái dài | ngắn lại | -13.9 | ✓ |
| Gập mu cổ chân 20° | Rộng ngoài | không đổi | +0.0 | ✓ |
| Gập mu cổ chân 20° | Nhị đầu đùi – đầu dài | không đổi | +0.0 | ✓ |
| Gập mu cổ chân 20° | Mông lớn – bó giữa | không đổi | +0.0 | ✓ |
| Dang hông 25° | Khép dài | dài ra | +24.0 | ✓ |
| Dang hông 25° | Khép ngắn | dài ra | +21.8 | ✓ |
| Dang hông 25° | Khép lớn – phần giữa | dài ra | +27.8 | ✓ |
| Dang hông 25° | Khép lớn – phần xa | dài ra | +24.3 | ✓ |
| Dang hông 25° | Cơ thon | dài ra | +27.9 | ✓ |
| Dang hông 25° | Mông nhỡ – bó trước | ngắn lại | -25.2 | ✓ |
| Dang hông 25° | Mông nhỡ – bó giữa | ngắn lại | -23.3 | ✓ |
| Dang hông 25° | Mông nhỡ – bó sau | ngắn lại | -19.6 | ✓ |
| Dang hông 25° | Mông bé – bó giữa | ngắn lại | -21.9 | ✓ |
| Dang hông 25° | Căng mạc đùi | ngắn lại | -28.4 | ✓ |
| Dang hông 25° | Rộng ngoài | không đổi | -0.0 | ✓ |
| Dang hông 25° | Cơ dép | không đổi | +0.0 | ✓ |
| Duỗi hông 20° (ra sau) | Cơ chậu | dài ra | +11.9 | ✓ |
| Duỗi hông 20° (ra sau) | Thắt lưng lớn | dài ra | +8.3 | ✓ |
| Duỗi hông 20° (ra sau) | Thẳng đùi | dài ra | +9.7 | ✓ |
| Duỗi hông 20° (ra sau) | Khép dài | dài ra | +16.4 | ✓ |
| Duỗi hông 20° (ra sau) | Mông lớn – bó giữa | ngắn lại | -22.6 | ✓ |
| Duỗi hông 20° (ra sau) | Nhị đầu đùi – đầu dài | ngắn lại | -14.1 | ✓ |
| Duỗi hông 20° (ra sau) | Bán màng | ngắn lại | -12.6 | ✓ |

## B. Hình cơ 3D có đúng là cơ được tô số liệu không

Màu của mỗi hình cơ lấy theo **tên**: hình *Vastus lateralis* của Z-Anatomy chỉ nhận số liệu của cơ `vaslat` trong OpenSim, nên không thể tô nhầm sang cơ khác. Bảng dưới kiểm tra thêm hai nguồn dữ liệu khớp nhau về **vị trí**: điểm bám đầu và cuối của đường cơ OpenSim (được đặt theo số liệu tử thi) phải nằm trên hoặc sát hình cơ Z-Anatomy đã căn vào bộ xương (ngưỡng 25 mm — cỡ chênh lệch giải phẫu giữa hai người khác nhau).

Phần giữa của đường cơ OpenSim có thể lệch khỏi bụng cơ 1–3 cm: đó là chủ ý của mô hình (các điểm uốn được chọn để cánh tay đòn mô men đúng như đo trên tử thi), không phải lỗi căn chỉnh.

**32/32 đường cơ khớp vị trí.**

| Hình cơ (Z-Anatomy) | Cơ OpenSim | Điểm bám đầu (mm) | Điểm bám cuối (mm) | Đúng | Ghi chú |
|---|---|---:|---:|:---:|---|
| Gluteus maximus muscle | Mông lớn – bó trên | 9 | 9 | ✓ |  |
| Gluteus maximus muscle | Mông lớn – bó giữa | 1 | 0 | ✓ |  |
| Gluteus maximus muscle | Mông lớn – bó dưới | 21 | 6 | ✓ |  |
| Gluteus medius muscle | Mông nhỡ – bó trước | 9 | 13 | ✓ |  |
| Gluteus medius muscle | Mông nhỡ – bó giữa | 2 | 7 | ✓ |  |
| Gluteus medius muscle | Mông nhỡ – bó sau | 7 | 1 | ✓ |  |
| Gluteus minimus muscle | Mông bé – bó trước | 15 | 20 | ✓ |  |
| Gluteus minimus muscle | Mông bé – bó giữa | 4 | 19 | ✓ |  |
| Gluteus minimus muscle | Mông bé – bó sau | 8 | 9 | ✓ |  |
| Tensor fasciae latae | Căng mạc đùi | 2 | 395 | ✓ | bám xuống xương chày qua dải chậu–chày |
| Piriformis muscle | Cơ hình lê | 24 | 5 | ✓ |  |
| Iliacus muscle | Cơ chậu | 9 | 10 | ✓ |  |
| Psoas major | Thắt lưng lớn | 9 | 10 | ✓ |  |
| Sartorius muscle | Cơ may | 6 | 7 | ✓ |  |
| Rectus femoris muscle | Thẳng đùi | 21 | 0 | ✓ |  |
| Vastus lateralis muscle | Rộng ngoài | 1 | 11 | ✓ |  |
| Vastus medialis muscle | Rộng trong | 10 | 8 | ✓ |  |
| Vastus intermedius muscle | Rộng giữa | 2 | 4 | ✓ |  |
| Long head of biceps femoris | Nhị đầu đùi – đầu dài | 20 | 16 | ✓ |  |
| Short head of biceps femoris | Nhị đầu đùi – đầu ngắn | 5 | 13 | ✓ |  |
| Semimembranosus muscle | Bán màng | 19 | 11 | ✓ |  |
| Semitendinosus muscle | Bán gân | 18 | 12 | ✓ |  |
| Adductor magnus / (Adductor minimus) | Khép lớn – phần gần | 24 | 23 | ✓ |  |
| Adductor magnus | Khép lớn – phần giữa | 17 | 4 | ✓ |  |
| Adductor magnus | Khép lớn – phần xa | 3 | 6 | ✓ |  |
| Adductor magnus | Khép lớn – phần ụ ngồi | 12 | 3 | ✓ |  |
| Adductor longus | Khép dài | 16 | 11 | ✓ |  |
| Adductor brevis | Khép ngắn | 22 | 12 | ✓ |  |
| Gracilis muscle | Cơ thon | 3 | 7 | ✓ |  |
| Lateral head of gastrocnemius | Bụng chân – đầu ngoài | 10 | 164 | ✓ | bám vào gót qua gân Achilles |
| Medial head of gastrocnemius | Bụng chân – đầu trong | 6 | 150 | ✓ | bám vào gót qua gân Achilles |
| Soleus muscle | Cơ dép | 11 | 81 | ✓ | bám vào gót qua gân Achilles |

Cơ có nhiều bó (mông lớn 3 bó, khép lớn 4 phần…): mỗi vùng của hình cơ lấy màu của bó gần nhất. Kiểm tra thứ tự các bó trên hình:

- ✓ Gluteus maximus muscle: trên → dưới = Mông lớn – bó trên → Mông lớn – bó giữa → Mông lớn – bó dưới
- ✓ Gluteus medius muscle: trước → sau = Mông nhỡ – bó trước → Mông nhỡ – bó giữa → Mông nhỡ – bó sau
- ✓ Gluteus minimus muscle: trước → sau = Mông bé – bó trước → Mông bé – bó giữa → Mông bé – bó sau
- ✓ Adductor magnus: trên → dưới = Khép lớn – phần gần → Khép lớn – phần giữa → Khép lớn – phần xa

## C. Đối chiếu bài tập với nghiên cứu

### squat-khong-ta

- ✓ Mông lớn, khép lớn và các cơ rộng (tứ đầu một khớp) bị kéo giãn ở đáy squat sâu *(nguồn: Kubo K, Ikebukuro T, Yata H (2019). Effects of squat training with different depths on lower limb muscle volumes. Eur J Appl Physiol 119:1933–1942 — squat sâu tăng thể tích mông lớn & nhóm khép hơn squat nông; tứ đầu tăng như nhau; đùi sau gần như không tăng.)*
- ✓ Thẳng đùi (tứ đầu hai khớp) KHÔNG bị kéo giãn — gập hông bù cho gập gối *(nguồn: Kubo K, Ikebukuro T, Yata H (2019). Effects of squat training with different depths on lower limb muscle volumes. Eur J Appl Physiol 119:1933–1942 — squat sâu tăng thể tích mông lớn & nhóm khép hơn squat nông; tứ đầu tăng như nhau; đùi sau gần như không tăng.)*
- ✓ Đùi sau dài thêm ít hơn hẳn so với RDL (squat gần như không kéo đùi sau) *(nguồn: Kubo K, Ikebukuro T, Yata H (2019). Effects of squat training with different depths on lower limb muscle volumes. Eur J Appl Physiol 119:1933–1942 — squat sâu tăng thể tích mông lớn & nhóm khép hơn squat nông; tứ đầu tăng như nhau; đùi sau gần như không tăng.)*
- ✓ Nhị đầu đùi đầu dài vẫn dài ra trong pha xuống; đầu ngắn (một khớp, chỉ bắc qua gối) thì ngắn lại *(nguồn: Geiser C, O'Connor K, Papaioannou Y, Montiero S (2006). Hamstrings length changes during drop jump and squat maneuvers. ISBS Proceedings — đo trên người: nhị đầu đùi đầu dài dài ra trong pha xuống của squat, đầu ngắn ngắn lại.)*
- ✓ Bụng chân (hai khớp) chỉ giãn nhẹ thoáng qua lúc cổ chân gập trước, rồi ngắn lại ở đáy vì gối gập sâu *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskeletal System; Gray's Anatomy).)*
- ✓ Cơ dép (một khớp, chỉ bắc qua cổ chân) bị kéo giãn ở đáy — cổ chân gập mu sâu *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskeletal System; Gray's Anatomy).)*

  Bị kéo giãn nhiều nhất: Khép lớn – phần ụ ngồi 0.82→1.48, Mông lớn – bó dưới 0.77→1.46, Cơ dép 1.02→1.39, Nhị đầu đùi – đầu dài 0.91→1.33, Khép lớn – phần xa 0.81→1.31, Mông nhỡ – bó sau 0.82→1.27

### rdl

- ✓ Đùi sau là nhóm bị kéo giãn mạnh nhất *(nguồn: Giải phẫu chức năng: đùi sau bắc qua hông và gối; gập hông khi gối gần thẳng làm chúng dài ra tối đa (Neumann, Kinesiology of the Musculoskeletal System, ch. 12–13).)*
- ✓ Các cơ rộng không bị kéo giãn vì gối gần như giữ nguyên *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskeletal System; Gray's Anatomy).)*
- ✓ Thẳng đùi ngắn lại (gập hông, gối gần thẳng) *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskeletal System; Gray's Anatomy).)*

  Bị kéo giãn nhiều nhất: Nhị đầu đùi – đầu dài 0.88→1.64, Bán màng 0.89→1.62, Nhị đầu – đầu dài 1.34→1.89, Bán gân 1.08→1.53, Khép lớn – phần ụ ngồi 0.81→1.39, Mông lớn – bó dưới 0.77→1.38

### split-squat

- ✓ Chân sau: thẳng đùi bị kéo giãn (hông duỗi + gối gập) *(nguồn: Giải phẫu chức năng: chân sau duỗi hông + gập gối kéo dài thẳng đùi và cơ thắt lưng–chậu; chân trước gập hông sâu kéo dài mông lớn.)*
- ✓ Chân trước: mông lớn bị kéo giãn; chân sau thì không (vẫn ngắn hơn chiều dài tối ưu) *(nguồn: Giải phẫu chức năng: chân sau duỗi hông + gập gối kéo dài thẳng đùi và cơ thắt lưng–chậu; chân trước gập hông sâu kéo dài mông lớn.)*

  Bị kéo giãn nhiều nhất: Thẳng đùi (T) 1.11→1.48, Mông lớn – bó dưới (P) 1.00→1.32, Khép lớn – phần ụ ngồi (P) 0.97→1.30, Cơ dép (P) 0.74→1.27, Mông lớn – bó giữa (P) 0.96→1.20, Mông nhỡ – bó sau (P) 1.12→1.31

## D. Vì sao màu mặc định là *mức kéo giãn do động tác*

Tô theo độ dài tuyệt đối (l/l_opt) làm các cơ sau có màu "giãn" ngay khi đứng yên, dù squat không kéo chúng:

- Khép dài: l/l_opt lúc đứng 1.12, động tác chỉ đổi +0%
- Nhị đầu đùi – đầu ngắn: l/l_opt lúc đứng 1.15, động tác chỉ đổi +0%
- Cơ thon: l/l_opt lúc đứng 1.20, động tác chỉ đổi +0%
- Cơ chậu: l/l_opt lúc đứng 1.10, động tác chỉ đổi +0%
- Thắt lưng lớn: l/l_opt lúc đứng 1.13, động tác chỉ đổi +0%
- Cơ may: l/l_opt lúc đứng 1.14, động tác chỉ đổi +0%
- Delta – bó sau: l/l_opt lúc đứng 1.12, động tác chỉ đổi +0%
- Tam đầu – đầu dài: l/l_opt lúc đứng 1.29, động tác chỉ đổi +0%
- Nhị đầu – đầu dài: l/l_opt lúc đứng 1.17, động tác chỉ đổi +0%
- Nhị đầu – đầu ngắn: l/l_opt lúc đứng 1.27, động tác chỉ đổi +0%
- Cánh tay quay: l/l_opt lúc đứng 1.14, động tác chỉ đổi +0%
- Gấp cổ tay quay: l/l_opt lúc đứng 1.11, động tác chỉ đổi +0%
- Gan tay dài: l/l_opt lúc đứng 1.11, động tác chỉ đổi +0%
- Sấp tròn: l/l_opt lúc đứng 1.35, động tác chỉ đổi +0%
- Sấp vuông: l/l_opt lúc đứng 1.11, động tác chỉ đổi +0%
- Duỗi các ngón: l/l_opt lúc đứng 1.87, động tác chỉ đổi +0%

Ngược lại, tô theo mức thay đổi làm cơ mông lớn chân sau của split squat trông như "giãn" (dài thêm 37%) trong khi nó vẫn ngắn hơn chiều dài tối ưu (0.87); mông lớn chân trước mới thật sự bị kéo giãn (1.20).

Vì vậy viewer dùng thang hai bậc (định nghĩa trong `pipeline/stretch.py`): một cơ chỉ được tô cam–đỏ khi nó dài hơn **cả** độ dài lúc bắt đầu **lẫn** chiều dài tối ưu. Dài ra mà chưa tới tối ưu thì tô vàng. Chế độ l/l_opt tuyệt đối vẫn có để bàn về vị trí trên đường cong lực–chiều dài.

## E. Thân trên (mô hình MoBL-ARMS)

Cơ vai, ngực, lưng xô, cánh tay và cẳng tay lấy từ mô hình chi trên MoBL-ARMS (Holzbaur 2005; Saul 2015). Góc tay bạn đặt (kiểu Rajagopal) được chuyển sang khớp vai của MoBL-ARMS bằng cách khớp hướng cánh tay và cẳng tay; bảng dưới kiểm tra **cả chuỗi** đó.

### E1. Chức năng giải phẫu

**81/81 đúng.** Thay đổi là chiều dài cơ + gân (mm).

| Thao tác | Cơ | Kỳ vọng | Mô hình | Đúng |
|---|---|---|---:|:---:|
| Gập khuỷu 10° → 90° | Tam đầu – đầu dài | dài ra | +30.8 | ✓ |
| Gập khuỷu 10° → 90° | Tam đầu – đầu ngoài | dài ra | +30.8 | ✓ |
| Gập khuỷu 10° → 90° | Tam đầu – đầu trong | dài ra | +30.8 | ✓ |
| Gập khuỷu 10° → 90° | Cơ khuỷu | dài ra | +16.3 | ✓ |
| Gập khuỷu 10° → 90° | Nhị đầu – đầu dài | ngắn lại | -44.3 | ✓ |
| Gập khuỷu 10° → 90° | Nhị đầu – đầu ngắn | ngắn lại | -44.3 | ✓ |
| Gập khuỷu 10° → 90° | Cơ cánh tay | ngắn lại | -21.7 | ✓ |
| Gập khuỷu 10° → 90° | Cánh tay quay | ngắn lại | -67.5 | ✓ |
| Gập khuỷu 10° → 90° | Delta – bó trước | không đổi | +0.0 | ✓ |
| Gập khuỷu 10° → 90° | Delta – bó giữa | không đổi | -0.0 | ✓ |
| Gập khuỷu 10° → 90° | Delta – bó sau | không đổi | -0.0 | ✓ |
| Gập khuỷu 10° → 90° | Trên gai | không đổi | -0.0 | ✓ |
| Gập khuỷu 10° → 90° | Dưới gai | không đổi | -0.0 | ✓ |
| Gập khuỷu 10° → 90° | Dưới vai | không đổi | -0.0 | ✓ |
| Gập khuỷu 10° → 90° | Tròn bé | không đổi | +0.0 | ✓ |
| Gập khuỷu 10° → 90° | Tròn lớn | không đổi | +0.0 | ✓ |
| Gập khuỷu 10° → 90° | Ngực lớn – phần đòn | không đổi | +0.0 | ✓ |
| Gập khuỷu 10° → 90° | Ngực lớn – phần ức sườn | không đổi | +0.0 | ✓ |
| Gập khuỷu 10° → 90° | Ngực lớn – phần bụng | không đổi | +0.0 | ✓ |
| Gập khuỷu 10° → 90° | Lưng xô – bó trên | không đổi | -0.0 | ✓ |
| Gập khuỷu 10° → 90° | Lưng xô – bó giữa | không đổi | +0.0 | ✓ |
| Gập khuỷu 10° → 90° | Lưng xô – bó dưới | không đổi | +0.0 | ✓ |
| Gập khuỷu 10° → 90° | Quạ cánh tay | không đổi | +0.0 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Delta – bó sau | dài ra | +27.6 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Lưng xô – bó trên | dài ra | +32.6 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Lưng xô – bó giữa | dài ra | +41.9 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Lưng xô – bó dưới | dài ra | +44.6 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Tròn lớn | dài ra | +33.1 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Tam đầu – đầu dài | dài ra | +21.9 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Delta – bó trước | ngắn lại | -46.5 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Quạ cánh tay | ngắn lại | -5.3 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Ngực lớn – phần đòn | ngắn lại | -18.4 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Nhị đầu – đầu dài | ngắn lại | -13.4 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Cơ cánh tay | không đổi | -0.0 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Cánh tay quay | không đổi | -0.0 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Tam đầu – đầu trong | không đổi | +0.0 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Tam đầu – đầu ngoài | không đổi | +0.0 | ✓ |
| Đưa tay ra trước (gập vai) 60° | Cơ khuỷu | không đổi | +0.0 | ✓ |
| Dang tay ngang vai 90° | Lưng xô – bó trên | dài ra | +30.3 | ✓ |
| Dang tay ngang vai 90° | Lưng xô – bó giữa | dài ra | +43.1 | ✓ |
| Dang tay ngang vai 90° | Lưng xô – bó dưới | dài ra | +95.8 | ✓ |
| Dang tay ngang vai 90° | Tròn lớn | dài ra | +33.6 | ✓ |
| Dang tay ngang vai 90° | Ngực lớn – phần ức sườn | dài ra | +39.9 | ✓ |
| Dang tay ngang vai 90° | Ngực lớn – phần bụng | dài ra | +55.6 | ✓ |
| Dang tay ngang vai 90° | Delta – bó giữa | ngắn lại | -55.6 | ✓ |
| Dang tay ngang vai 90° | Trên gai | ngắn lại | -14.7 | ✓ |
| Dang tay ngang vai 90° | Cơ cánh tay | không đổi | -0.0 | ✓ |
| Dang tay ngang vai 90° | Tam đầu – đầu trong | không đổi | -0.0 | ✓ |
| Đưa tay ra sau (duỗi vai) 30° | Delta – bó trước | dài ra | +23.2 | ✓ |
| Đưa tay ra sau (duỗi vai) 30° | Quạ cánh tay | dài ra | +18.7 | ✓ |
| Đưa tay ra sau (duỗi vai) 30° | Ngực lớn – phần đòn | dài ra | +9.2 | ✓ |
| Đưa tay ra sau (duỗi vai) 30° | Nhị đầu – đầu dài | dài ra | +15.6 | ✓ |
| Đưa tay ra sau (duỗi vai) 30° | Delta – bó sau | ngắn lại | -37.0 | ✓ |
| Đưa tay ra sau (duỗi vai) 30° | Tam đầu – đầu dài | ngắn lại | -20.5 | ✓ |
| Đưa tay ra sau (duỗi vai) 30° | Cơ cánh tay | không đổi | +0.0 | ✓ |
| Xoay ngoài vai 45° (khuỷu 90°, cánh tay sát thân) | Dưới vai | dài ra | +13.5 | ✓ |
| Xoay ngoài vai 45° (khuỷu 90°, cánh tay sát thân) | Ngực lớn – phần đòn | dài ra | +9.6 | ✓ |
| Xoay ngoài vai 45° (khuỷu 90°, cánh tay sát thân) | Ngực lớn – phần ức sườn | dài ra | +9.2 | ✓ |
| Xoay ngoài vai 45° (khuỷu 90°, cánh tay sát thân) | Tròn lớn | dài ra | +8.4 | ✓ |
| Xoay ngoài vai 45° (khuỷu 90°, cánh tay sát thân) | Dưới gai | ngắn lại | -17.8 | ✓ |
| Xoay ngoài vai 45° (khuỷu 90°, cánh tay sát thân) | Tròn bé | ngắn lại | -12.1 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Cơ ngửa | dài ra | +12.1 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Nhị đầu – đầu dài | dài ra | +7.9 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Nhị đầu – đầu ngắn | dài ra | +7.9 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Sấp tròn | ngắn lại | -12.5 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Sấp vuông | ngắn lại | -5.6 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Delta – bó trước | không đổi | +0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Delta – bó giữa | không đổi | -0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Delta – bó sau | không đổi | -0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Trên gai | không đổi | -0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Dưới gai | không đổi | -0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Dưới vai | không đổi | +0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Tròn bé | không đổi | -0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Tròn lớn | không đổi | +0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Ngực lớn – phần đòn | không đổi | +0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Ngực lớn – phần ức sườn | không đổi | +0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Ngực lớn – phần bụng | không đổi | -0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Lưng xô – bó trên | không đổi | +0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Lưng xô – bó giữa | không đổi | +0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Lưng xô – bó dưới | không đổi | +0.0 | ✓ |
| Xoay cẳng tay từ ngửa hẳn về trung tính | Quạ cánh tay | không đổi | +0.0 | ✓ |

### E2. Hình cơ 3D ↔ đường cơ MoBL-ARMS

**34/35 đường cơ khớp vị trí** (ngưỡng 25 mm; cơ cẳng tay bám vào bàn tay qua gân dài nên chỉ xét điểm bám đầu).

| Hình cơ (Z-Anatomy) | Cơ MoBL-ARMS | Điểm bám đầu (mm) | Điểm bám cuối (mm) | Đúng | Ghi chú |
|---|---|---:|---:|:---:|---|
| Brachioradialis muscle | Cánh tay quay | 5 | 3 | ✓ | bám mỏm trâm quay qua gân dẹt |
| Brachialis muscle | Cơ cánh tay | 2 | 3 | ✓ |  |
| Anconeus muscle | Cơ khuỷu | 8 | 1 | ✓ |  |
| Supinator | Cơ ngửa | 2 | 2 | ✓ |  |
| Acromial part of deltoid muscle | Delta – bó giữa | 17 | 7 | ✓ |  |
| Scapular spinal part of deltoid muscle | Delta – bó sau | 26 | 5 | ✗ |  |
| Clavicular part of deltoid muscle | Delta – bó trước | 6 | 13 | ✓ |  |
| Extensor digitorum | Duỗi các ngón | 12 | 12 | ✓ | bám đốt ngón qua gân dài |
| Extensor carpi radialis longus | Duỗi cổ tay quay dài | 3 | 34 | ✓ | bám xương bàn tay qua gân dài |
| Extensor carpi radialis brevis | Duỗi cổ tay quay ngắn | 17 | 21 | ✓ | bám xương bàn tay qua gân dài |
| Humeral head of extensor carpi ulnaris | Duỗi cổ tay trụ | 18 | 32 | ✓ | bám xương bàn tay qua gân dài |
| Infraspinatus muscle | Dưới gai | 0 | 0 | ✓ |  |
| Subscapularis muscle | Dưới vai | 4 | 3 | ✓ |  |
| Palmaris longus muscle | Gan tay dài | 6 | 6 | ✓ | nối vào cân gan tay qua gân dài |
| Humero-ulnar head of flexor digitorum superficialis | Gấp các ngón nông | 6 | 11 | ✓ | bám đốt ngón qua gân dài |
| Flexor digitorum profundus | Gấp các ngón sâu | 0 | 18 | ✓ | bám đốt ngón qua gân dài |
| Flexor carpi radialis | Gấp cổ tay quay | 4 | 19 | ✓ | bám xương bàn tay qua gân dài |
| Humeral head of flexor carpi ulnaris | Gấp cổ tay trụ | 9 | 32 | ✓ | bám xương đậu qua gân |
| Latissimus dorsi muscle | Lưng xô – bó dưới | 4 | 32 | ✓ | bám rãnh gian củ xương cánh tay qua gân dẹt dài |
| Latissimus dorsi muscle | Lưng xô – bó giữa | 1 | 41 | ✓ | bám rãnh gian củ xương cánh tay qua gân dẹt dài |
| Latissimus dorsi muscle | Lưng xô – bó trên | 7 | 30 | ✓ | bám rãnh gian củ xương cánh tay qua gân dẹt dài |
| (Abdominal part of pectoralis major muscle) | Ngực lớn – phần bụng | 6 | 61 | ✓ | phần bụng xoắn vào gân chung của ngực lớn trước khi bám xương cánh tay |
| Clavicular head of pectoralis major muscle | Ngực lớn – phần đòn | 4 | 8 | ✓ |  |
| Sternocostal head of pectoralis major muscle | Ngực lớn – phần ức sườn | 4 | 10 | ✓ |  |
| Long head of biceps brachii | Nhị đầu – đầu dài | 8 | 2 | ✓ | đầu dài đi qua rãnh gian củ bằng một gân dài tới củ trên ổ chảo |
| Short head of biceps brachii | Nhị đầu – đầu ngắn | 2 | 72 | ✓ | nhập vào gân chung với đầu dài, bám lồi củ xương quay |
| Coracobrachialis muscle | Quạ cánh tay | 1 | 5 | ✓ |  |
| Superficial head of pronator teres | Sấp tròn | 6 | 4 | ✓ |  |
| Pronator quadratus | Sấp vuông | 4 | 4 | ✓ |  |
| Long head of triceps brachii | Tam đầu – đầu dài | 17 | 1 | ✓ |  |
| Lateral head of triceps brachii | Tam đầu – đầu ngoài | 4 | 3 | ✓ |  |
| Medial head of triceps brachii | Tam đầu – đầu trong | 3 | 0 | ✓ |  |
| Supraspinatus muscle | Trên gai | 2 | 15 | ✓ |  |
| Teres minor muscle | Tròn bé | 1 | 13 | ✓ |  |
| Teres major muscle | Tròn lớn | 1 | 29 | ✓ | bám mép trong rãnh gian củ qua gân dẹt (~5 cm) |

### E3. Đối chiếu bài tập thân trên

#### overhead-triceps

- ✓ Tam đầu đầu dài dài hơn hẳn khi duỗi tam đầu qua đầu so với đẩy cáp (pushdown) — cánh tay giơ qua đầu kéo đầu dài (bắc qua vai) dài thêm *(nguồn: Maeo S, Wu Y, Huang M, et al. (2023). Triceps brachii hypert…)*
- ✓ Đầu ngoài và đầu trong (một khớp) dài như nhau ở hai bài — chỉ phụ thuộc góc khuỷu *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

#### pull-up

- ✓ Lưng xô và cơ tròn lớn dài nhất khi treo thẳng tay (phase 0), ngắn lại khi kéo người lên *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*
- ✓ Nhị đầu và cơ cánh tay ngắn lại khi kéo lên (gập khuỷu) *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

#### push-up

- ✓ Ngực lớn và delta trước dài ra ở đáy (cánh tay ra sau mặt phẳng thân) *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*
- ✓ Tam đầu đầu ngoài/đầu trong dài ra (khuỷu gập) *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

#### bench-press

- ✓ Ngực lớn và delta trước dài ra khi hạ thanh đòn xuống ngực *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

#### biceps-curl

- ✓ Nhị đầu, cơ cánh tay, cánh tay quay ngắn lại; tam đầu dài ra *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

#### lateral-raise

- ✓ Delta giữa và cơ trên gai ngắn lại; lưng xô, tròn lớn, ngực lớn bó ức sườn dài ra *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

#### bent-over-row

- ✓ Delta sau ngắn lại, delta trước dài ra khi kéo tạ về bụng *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

#### chest-stretch

- ✗ Ngực lớn (bó đòn và ức sườn) bị kéo giãn *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*
  - Ghi chú: phần ức sườn bị kéo giãn rõ (vượt chiều dài tối ưu ~7%); phần đòn dài thêm 15% nhưng chỉ vừa chạm chiều dài tối ưu (1.02) nên chưa tính là "bị kéo giãn". Kết luận này được giữ nguyên là ✗ thay vì chỉnh tư thế cho khớp.

#### triceps-stretch

- ✓ Tam đầu đầu dài, lưng xô bó dưới và cơ tròn lớn bị kéo giãn *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

#### cross-body-stretch

- ✓ Delta sau và cơ dưới gai bị kéo giãn *(nguồn: Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskel…)*

Giới hạn: mô hình không có cơ thang, cơ trám, răng cưa trước, cơ bụng và cơ dựng sống — các cơ này không được tô.

## Nguồn

- Kubo K, Ikebukuro T, Yata H (2019). Effects of squat training with different depths on lower limb muscle volumes. Eur J Appl Physiol 119:1933–1942 — squat sâu tăng thể tích mông lớn & nhóm khép hơn squat nông; tứ đầu tăng như nhau; đùi sau gần như không tăng.
- Giải phẫu chức năng: đùi sau bắc qua hông và gối; gập hông khi gối gần thẳng làm chúng dài ra tối đa (Neumann, Kinesiology of the Musculoskeletal System, ch. 12–13).
- Geiser C, O'Connor K, Papaioannou Y, Montiero S (2006). Hamstrings length changes during drop jump and squat maneuvers. ISBS Proceedings — đo trên người: nhị đầu đùi đầu dài dài ra trong pha xuống của squat, đầu ngắn ngắn lại.
- Giải phẫu chức năng (Neumann, Kinesiology of the Musculoskeletal System; Gray's Anatomy).
- Maeo S, Wu Y, Huang M, et al. (2023). Triceps brachii hypertrophy is substantially greater after elbow extension training performed in the overhead versus neutral arm position. Eur J Sport Sci 23(7):1240–1250 — tập ở tư thế tay qua đầu (đầu dài bị kéo dài hơn) làm tam đầu to hơn rõ rệt.
- Giải phẫu chức năng: chân sau duỗi hông + gập gối kéo dài thẳng đùi và cơ thắt lưng–chậu; chân trước gập hông sâu kéo dài mông lớn.
