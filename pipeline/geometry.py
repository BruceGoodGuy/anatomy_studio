"""Gộp hình xương OpenSim (.vtp) thành assets/osim.bones.json cho viewer.

Mỗi body của mô hình: toạ độ đỉnh (trong hệ trục của body) + chỉ số mặt, dạng base64.
Viewer tự giải mã — không cần GLTFLoader và không dùng URL data: (trang nhúng hay chặn).

Chỉ cần chạy lại khi đổi mô hình:  python -m pipeline.geometry
"""
import base64
import json
import os
import xml.etree.ElementTree as ET

import numpy as np
import opensim as osim
import trimesh

from .common import ASSETS, GEOMETRY_DIR, load_model


def read_vtp(path):
    root = ET.parse(path).getroot()
    piece = root.find("PolyData/Piece")
    pts = np.array(piece.find("Points/DataArray").text.split(), dtype=np.float64).reshape(-1, 3)
    polys = piece.find("Polys")
    conn = off = None
    for da in polys.findall("DataArray"):
        vals = np.array(da.text.split(), dtype=np.int64)
        if da.get("Name") == "connectivity":
            conn = vals
        elif da.get("Name") == "offsets":
            off = vals
    faces, start = [], 0
    for end in off:
        poly = conn[start:end]
        for k in range(1, len(poly) - 1):  # fan triangulation
            faces.append([poly[0], poly[k], poly[k + 1]])
        start = end
    return pts, np.array(faces, dtype=np.int64)


def tidy(mesh, target_faces):
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    if len(mesh.faces) < 1200:
        # Hình xương gốc rất thô (~200 mặt): chia nhỏ cho mượt khi xem gần.
        try:
            mesh = mesh.subdivide_loop(iterations=2)
        except ValueError:  # mesh không kín (non-manifold): giữ nguyên
            pass
    if len(mesh.faces) > target_faces:
        mesh = mesh.simplify_quadric_decimation(face_count=target_faces)
    return mesh


# Hình OpenSim được thay bằng xương Z-Anatomy chuyển động được (pipeline/zbind_upper.py): lồng ngực OpenSim
# gắn liền bả vai — giữ lại thì bả vai đứng yên trong khi bả vai Z-Anatomy xoay theo tay.
EXCLUDE = {"hat_ribs_scap.vtp"}


def build(out=os.path.join(ASSETS, "osim.bones.json"), max_faces=3500):
    model, _ = load_model()
    per_body = {}
    for comp in model.getComponentsList():
        if comp.getConcreteClassName() != "Mesh":
            continue
        g = osim.Mesh.safeDownCast(comp)
        if g.get_mesh_file() in EXCLUDE:
            continue
        body = g.getFrame().findBaseFrame().getName()
        sf = g.get_scale_factors()
        pts, faces = read_vtp(os.path.join(GEOMETRY_DIR, g.get_mesh_file()))
        pts = pts * np.array([sf.get(0), sf.get(1), sf.get(2)])
        per_body.setdefault(body, []).append(trimesh.Trimesh(pts, faces, process=False))
    enc = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")
    bodies = []
    for body, parts in per_body.items():
        budget = max(max_faces // len(parts), 150)
        mesh = trimesh.util.concatenate([tidy(p, budget) for p in parts])
        mesh.fix_normals()
        v = np.asarray(mesh.vertices, dtype="<f4")
        bodies.append({"body": body, "nv": len(v), "v": enc(v),
                       "idx": enc(np.asarray(mesh.faces, dtype="<u2" if len(v) < 65535 else "<u4"))})
    with open(out, "w", encoding="utf-8") as fp:
        json.dump({"bodies": bodies}, fp, separators=(",", ":"))
    print(f"OK: {len(bodies)} xương -> {out} ({os.path.getsize(out) / 1024:.0f} KB)")


if __name__ == "__main__":
    build()
