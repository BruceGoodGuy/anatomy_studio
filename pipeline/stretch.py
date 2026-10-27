"""Định nghĩa DUY NHẤT của "cơ bị động tác kéo giãn" — dùng chung cho bảng số, xếp hạng và màu.

Hai cách tô đơn giản đều dễ đánh lừa người đọc:
  * theo độ dài tuyệt đối l/l_opt: cơ thon, cơ may... đã ở 1.1–1.2 ngay khi đứng yên → trông như
    "đang giãn" dù động tác không kéo chúng;
  * theo mức thay đổi so với lúc bắt đầu: mông lớn chân sau trong split squat dài thêm 37% nhưng vẫn
    ngắn hơn chiều dài tối ưu (0.89) → trông như "đang giãn" dù chưa hề giãn.

Vì vậy dùng thang hai bậc. Với a = l/l0 − 1 (mức dài thêm so với lúc bắt đầu) và
b = max(0, l − max(1, l0)) (phần vượt quá CẢ độ dài lúc bắt đầu LẪN chiều dài tối ưu):
  a ≤ 0:  S = a                                   ngắn lại (xanh)
  a > 0:  S = min(a / 0.25, 1) + b / 0.4          dài ra (vàng, đủ màu ở +25%) + bị kéo giãn (cam → đỏ)
S liên tục; thay đổi nhỏ (vài %) gần như không màu; S > 1 chỉ khi cơ vượt chiều dài tối ưu.
"Bị kéo giãn" (dùng cho xếp hạng, bảng số, câu mở đầu): b > 0.02 và a > 5%.
Viewer (web/anatomy-core.js, hàm stretchIndex) dùng đúng công thức này.
"""
import numpy as np

SPAN = 0.4        # l/l_opt vượt quá thêm 0.4 → đỏ đậm nhất
GROW = 0.25       # dài thêm 25% → đủ màu "dài ra"


def index(l, l0):
    l = np.asarray(l, float)
    a = l / l0 - 1
    b = np.maximum(0.0, l - max(1.0, l0))
    return np.where(a <= 0, a, np.minimum(a / GROW, 1.0) + b / SPAN)


def summarize(series):
    """series: l/l_opt theo thời gian của một cơ (NaN = khung không có số liệu tin cậy)."""
    s = np.asarray(series, float)
    ok = np.isfinite(s) & (s > 0)
    if not ok.any():
        return {"start": None, "max": None, "argmax": 0, "change": 0.0, "beyond": 0.0, "peak_index": 0.0,
                "stretched": False, "valid_pct": 0.0}
    l0 = float(s[np.argmax(ok)])          # khung đầu tiên có số liệu
    k = int(np.nanargmax(np.where(ok, s, np.nan)))
    beyond = max(0.0, float(s[k]) - max(1.0, l0))
    return {"start": l0, "max": float(s[k]), "argmax": k, "change": float(s[k] / l0 - 1),
            "beyond": beyond, "peak_index": float(index(s[k], l0)), "stretched": bool(beyond > 0.02 and s[k] / l0 - 1 > 0.05),
            "valid_pct": float(ok.mean() * 100)}


def rank_key(summary):
    """Xếp hạng: trước hết theo mức vượt quá R (giãn thật), sau đó theo mức dài thêm."""
    return (round(summary["beyond"], 3), summary["change"])
