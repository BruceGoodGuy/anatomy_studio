"""Chỉ số chất lượng hình học cho mesh cơ đã biến dạng (không phụ thuộc cách biến dạng).

* fold_faces: tam giác bị gập/lật — pháp tuyến ngược chiều với các tam giác kề nó, trong khi
  ở tư thế nghỉ thì cùng chiều. Đây là các "gai", "nếp gấp", chỗ cơ bị bẻ ngược vào trong.
* edge strain: tỉ lệ độ dài cạnh sau / trước biến dạng. Cạnh bị kéo quá dài = "rách",
  bị nén gần 0 = "bẹp".
"""
import numpy as np


def face_normals(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    a = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(a, 1e-12), a[:, 0] * 0.5


def face_adjacency(F):
    """Cặp tam giác dùng chung một cạnh."""
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    fid = np.tile(np.arange(len(F)), 3)
    key = e[:, 0].astype(np.int64) * (1 << 32) + e[:, 1]
    order = np.argsort(key, kind="stable")
    k, f = key[order], fid[order]
    same = k[1:] == k[:-1]
    return np.stack([f[:-1][same], f[1:][same]], 1)


def unique_edges(F):
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    return np.unique(e, axis=0)


class MeshQA:
    """Chuẩn bị một lần ở tư thế nghỉ, đo nhiều lần ở các khung hình."""

    def __init__(self, V0, F):
        self.F = F
        self.adj = face_adjacency(F)
        self.E = unique_edges(F)
        self.L0 = np.linalg.norm(V0[self.E[:, 0]] - V0[self.E[:, 1]], axis=1)
        n0, self.A0 = face_normals(V0, F)
        # tam giác "kim" (góc nhỏ nhất < 10° hoặc diện tích < 1 mm²): lật cũng không thấy được
        # bằng mắt (nhỏ hơn một điểm ảnh) nên đếm riêng, không tính là lỗi hiển thị.
        A = V0[F]
        ang = []
        for i in range(3):
            u, v = A[:, (i + 1) % 3] - A[:, i], A[:, (i + 2) % 3] - A[:, i]
            c = np.sum(u * v, 1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-20)
            ang.append(np.degrees(np.arccos(np.clip(c, -1, 1))))
        self.sliver = (np.min(ang, 0) < 10) | (self.A0 < 1e-6)
        d0 = np.sum(n0[self.adj[:, 0]] * n0[self.adj[:, 1]], 1)
        # chỉ xét các cặp vốn "phẳng" ở tư thế nghỉ (góc giữa hai tam giác < 60°)
        self.smooth_pair = d0 > 0.5
        self.ok_edge = self.L0 > 1e-5

    def local_rotations(self, V0, V):
        """Phép xoay khớp nhất cho vòng 1 lân cận của mỗi đỉnh (Kabsch) → [n,3,3]."""
        E = self.E
        a0, a1 = V0[E[:, 1]] - V0[E[:, 0]], V[E[:, 1]] - V[E[:, 0]]
        C = np.zeros((len(V0), 3, 3))
        outer = a1[:, :, None] * a0[:, None, :]
        np.add.at(C, E[:, 0], outer)
        np.add.at(C, E[:, 1], outer)
        U, _, Vt = np.linalg.svd(C)
        d = np.sign(np.linalg.det(U @ Vt))
        U[:, :, 2] *= d[:, None]
        return U @ Vt

    def measure(self, V, V0=None):
        n, A = face_normals(V, self.F)
        flips = 0
        flipped = np.zeros(len(self.F), bool)
        if V0 is not None:
            # Lật thật sự: pháp tuyến mới ngược với pháp tuyến cũ đã xoay theo chuyển động
            # cục bộ. Không phụ thuộc cách biến dạng, không báo nhầm khi mặt cơ chỉ bị kéo.
            R = self.local_rotations(V0, V)
            n0, _ = face_normals(V0, self.F)
            Rf = R[self.F[:, 0]]
            exp = np.einsum("fij,fj->fi", Rf, n0)
            flipped = np.sum(exp * n, 1) < 0
            flips = int((flipped & ~self.sliver).sum())
        d = np.sum(n[self.adj[:, 0]] * n[self.adj[:, 1]], 1)
        bad = self.smooth_pair & (d < 0.0)          # gập > 90° ở chỗ vốn phẳng
        folded = np.zeros(len(self.F), bool)
        folded[self.adj[bad, 0]] = True
        folded[self.adj[bad, 1]] = True
        r = np.linalg.norm(V[self.E[:, 0]] - V[self.E[:, 1]], axis=1)[self.ok_edge] / self.L0[self.ok_edge]
        return {
            "flip_faces": flips,
            "sliver_flips": int((flipped & self.sliver).sum()),
            "flipped_mask": flipped,
            "fold_faces": int(folded.sum()),
            "fold_pct": float(folded.mean() * 100),
            "edge_max": float(r.max()),
            "edge_min": float(r.min()),
            "edge_over2_pct": float((r > 2.0).mean() * 100),
            "edge_under04_pct": float((r < 0.4).mean() * 100),
            "folded_mask": folded,
        }
