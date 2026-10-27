"""Biến dạng mesh cơ theo xương: trường trọng số điều hoà + dual-quaternion skinning (DQS).

Ý tưởng
-------
Thay vì cho từng cơ tự bám theo đường cơ của riêng nó (cách cũ — mỗi cơ một kiểu, nên cơ
cạnh nhau tách ra hoặc đâm vào nhau, và hệ trục dọc đường cơ bị xoắn khi gập gối), ta dựng
MỘT trường biến dạng chung cho cả vùng hông – đùi – cẳng chân:

* Mỗi xương (chậu, đùi, bánh chè, cẳng chân, bàn chân, thân) có một trọng số w_b(p) tại mọi
  điểm p trong không gian. w_b là nghiệm phương trình Laplace (hàm điều hoà): bằng 1 trên bề
  mặt xương b, bằng 0 trên các xương khác. Hàm điều hoà là hàm "mượt nhất có thể" nối các
  xương; quanh một khớp nó chuyển dần theo góc — đúng kiểu cần cho khớp gập sâu.
* Một điểm di chuyển bằng cách trộn chuyển động cứng của các xương theo trọng số, dùng dual
  quaternion (không bị "kẹo xoắn" như trộn ma trận).

Vì mọi cơ dùng chung một trường liên tục: không thể rách (trường liên tục), cơ kề nhau đi
cùng nhau, và nếu định thức Jacobian của trường > 0 ở mọi nơi có cơ thì phép biến dạng không
gấp — không tạo chồng lấn mới. Đó chính là điều pipeline/qa.py kiểm tra cho mỗi bài.

Hàm ở đây là bản tham chiếu; web/viewer.html làm đúng các phép tính này (test so sánh trong
pipeline/qa.py --selftest).
"""
import numpy as np

# ---------------------------------------------------------------- quaternion (x, y, z, w)


def qmul(a, b):
    ax, ay, az, aw = np.moveaxis(a, -1, 0)
    bx, by, bz, bw = np.moveaxis(b, -1, 0)
    return np.stack([aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw,
                     aw * bw - ax * bx - ay * by - az * bz], -1)


def qconj(q):
    return q * np.array([-1, -1, -1, 1.0])


def qrot(q, v):
    """Xoay vector v bằng quaternion đơn vị q (broadcast)."""
    u, w = q[..., :3], q[..., 3:4]
    t = 2.0 * np.cross(u, v)
    return v + w * t + np.cross(u, t)


def mat_to_quat(R):
    m = R
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.array(q)
    return q / np.linalg.norm(q)


# ---------------------------------------------------------------- dual quaternion skinning


def skin_dq(rest_xf, cur_xf):
    """Dual quaternion của phép biến đổi cứng S = X_cur · X_rest⁻¹ cho từng xương.

    rest_xf, cur_xf: [K, 7] = (x y z qx qy qz qw). Trả về (q0 [K,4], qe [K,4])."""
    rest_xf, cur_xf = np.asarray(rest_xf, float), np.asarray(cur_xf, float)
    qr = rest_xf[:, 3:] / np.linalg.norm(rest_xf[:, 3:], axis=1, keepdims=True)
    qc = cur_xf[:, 3:] / np.linalg.norm(cur_xf[:, 3:], axis=1, keepdims=True)
    q0 = qmul(qc, qconj(qr))
    t = cur_xf[:, :3] - qrot(q0, rest_xf[:, :3])
    qe = 0.5 * qmul(np.concatenate([t, np.zeros((len(t), 1))], 1), q0)
    return q0, qe


def apply_dqs(V, bi, bw, q0, qe, return_rot=False):
    """V [n,3] tư thế nghỉ; bi [n,k] chỉ số xương; bw [n,k] trọng số (tổng 1)."""
    a0, ae = q0[bi], qe[bi]                                  # [n,k,4]
    # Đưa mọi quaternion về cùng bán cầu với xương có trọng số LỚN NHẤT của đỉnh đó.
    # (q và −q là cùng một phép xoay; trộn khi khác dấu sẽ đi "đường vòng" → cơ bị ép bẹp.)
    ref = a0[np.arange(len(bw)), np.argmax(bw, 1)][:, None, :]
    s = np.sign(np.sum(a0 * ref, -1, keepdims=True))
    s[s == 0] = 1
    w = bw[..., None] * s
    b0, be = np.sum(w * a0, 1), np.sum(w * ae, 1)
    n = np.linalg.norm(b0, axis=1, keepdims=True)
    b0, be = b0 / n, be / n
    v0, w0 = b0[:, :3], b0[:, 3:4]
    ve, we = be[:, :3], be[:, 3:4]
    t = 2.0 * (w0 * ve - we * v0 + np.cross(v0, ve))
    if return_rot:
        return qrot(b0, V) + t, b0
    return qrot(b0, V) + t


# ---------------------------------------------------------------- weight field (grid)


class WeightField:
    """Trọng số trên lưới đều: W [K, nx, ny, nz], gốc o, bước h."""

    def __init__(self, W, origin, h, names):
        self.W, self.o, self.h, self.names = np.asarray(W, np.float32), np.asarray(origin, float), float(h), list(names)

    def sample(self, P):
        """Nội suy tam tuyến → [n, K]."""
        g = (np.asarray(P, float) - self.o) / self.h
        K, nx, ny, nz = self.W.shape
        g = np.clip(g, 0, np.array([nx, ny, nz]) - 1.000001)
        i = np.floor(g).astype(int)
        f = g - i
        out = np.zeros((len(g), K))
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    c = (np.where(dx, f[:, 0], 1 - f[:, 0]) * np.where(dy, f[:, 1], 1 - f[:, 1])
                         * np.where(dz, f[:, 2], 1 - f[:, 2]))
                    out += c[:, None] * self.W[:, i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz].T
        return out

    def weights(self, P):
        """Trọng số của TẤT CẢ xương tại P → (bi [n,K], bw [n,K]).

        Không cắt bớt còn "4 xương mạnh nhất" như skinning thông thường: khi thứ hạng xương
        thứ 4/5 đổi chỗ giữa hai đỉnh kề nhau, trọng số nhảy bậc → mesh bị xé thành nếp."""
        w = np.clip(self.sample(P), 0, None)
        w /= np.maximum(w.sum(1, keepdims=True), 1e-9)
        bi = np.tile(np.arange(w.shape[1]), (len(w), 1))
        return bi, w

    top4 = weights   # tên cũ

    def save(self, path):
        np.savez_compressed(path, W=self.W.astype(np.float16), o=self.o, h=self.h, names=np.array(self.names))

    @classmethod
    def load(cls, path):
        d = np.load(path)
        return cls(d["W"].astype(np.float32), d["o"], float(d["h"]), [str(x) for x in d["names"]])


class SubField:
    """Trường của một nhóm xương, trả trọng số theo đủ K xương (0 cho xương ngoài nhóm)."""

    def __init__(self, field, all_names, mirror=False):
        self.field, self.mirror = field, mirror
        self.cols = [all_names.index(n) for n in field.names]
        self.K = len(all_names)

    def weights(self, X):
        X = np.asarray(X, float)
        if self.mirror:
            X = X * np.array([1.0, 1.0, -1.0])
        _, w = self.field.weights(X)
        out = np.zeros((len(X), self.K))
        out[:, self.cols] = w
        return np.tile(np.arange(self.K), (len(X), 1)), out


class FieldSet:
    """Một trường trọng số điều hoà cho mỗi nhóm xương mà một cơ được phép theo."""

    def __init__(self, fields, all_names):
        self.fields = {tuple(k): v for k, v in fields.items()}
        self.names = list(all_names)

    def for_bones(self, bones, mirror=False):
        key = tuple(n for n in self.names if n in bones)
        return SubField(self.fields[key], self.names, mirror)

    def save(self, path):
        d = {"all": np.array(self.names)}
        for i, (k, f) in enumerate(self.fields.items()):
            d[f"W{i}"] = f.W.astype(np.float16)
            d[f"n{i}"] = np.array(k)
            d["o"], d["h"] = f.o, f.h
        np.savez_compressed(path, **d)

    @classmethod
    def load(cls, path):
        d = np.load(path)
        fields, i = {}, 0
        while f"W{i}" in d:
            names = [str(x) for x in d[f"n{i}"]]
            fields[tuple(names)] = WeightField(d[f"W{i}"].astype(np.float32), d["o"], float(d["h"]), names)
            i += 1
        return cls(fields, [str(x) for x in d["all"]])


def jacobian_det(field, P, q0, qe, eps=0.002):
    """Định thức Jacobian của phép biến dạng tại các điểm P (sai phân trung tâm).

    < 0: không gian bị gập ngược (mesh xuyên qua chính nó / cơ khác); ≈ 0: bị ép bẹp."""
    J = np.zeros((len(P), 3, 3))
    for k in range(3):
        d = np.zeros(3)
        d[k] = eps
        bi, bw = field.weights(P + d)
        a = apply_dqs(P + d, bi, bw, q0, qe)
        bi, bw = field.weights(P - d)
        b = apply_dqs(P - d, bi, bw, q0, qe)
        J[:, :, k] = (a - b) / (2 * eps)
    return np.linalg.det(J)
