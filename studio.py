"""Anatomy Studio — công cụ tạo bài tập và dữ liệu cơ, chạy trên máy của bạn.

    python studio.py          (rồi mở http://127.0.0.1:8000 nếu trình duyệt không tự mở)

Không cần mạng (trừ font chữ), không cần AI. Mọi bài tập lưu trong thư mục exercises/,
kết quả trong output/<tên-bài>/.
"""
import io
import json
import os
import shutil
import threading
import webbrowser
import zipfile

import numpy as np
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from pipeline.common import ASSETS, EXERCISES_DIR, OUTPUT_DIR, WEB_DIR, slugify, body_names
from pipeline.motion import COLUMNS, OPTIONS, DEFAULT_TIMING, SECTIONS, ARM_PRESETS, ARM_COLUMNS_L, validate, curves, timeline
from pipeline.export import equilibrate, UpperExport, VIRTUAL
from pipeline.common import load_model
from pipeline.upper import SHOWN as UPPER_SHOWN
from pipeline.muscle_names import GROUPS, MUSCLES
from pipeline import build as builder

app = FastAPI(title="Anatomy Studio")
LOCK = threading.Lock()          # OpenSim model không an toàn đa luồng
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
os.makedirs(EXERCISES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def ex_path(slug):
    if slug != slugify(slug):
        raise HTTPException(400, "Tên file không hợp lệ.")
    return os.path.join(EXERCISES_DIR, slug + ".json")


def jsonable(o):
    if isinstance(o, dict):
        return {k: jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "studio.html"))


@app.get("/api/meta")
def meta():
    return {"columns": COLUMNS, "options": OPTIONS, "timing": DEFAULT_TIMING,
            "sections": [{"id": i, "label": l, "columns": c} for i, l, c in SECTIONS],
            "arm_presets": {k: {"label": l, "values": v} for k, (l, v) in ARM_PRESETS.items()},
            "arm_left_columns": ARM_COLUMNS_L}


@app.get("/api/muscles")
def muscles_meta():
    """Danh sách cơ (cả hai bên) để Studio tô màu và hiển thị tên."""
    _, exporter = builder.tools()
    out = []
    for name in muscle_ids(exporter):
        vi, latin, group = MUSCLES.get(name[:-2], (name, name, "other"))
        out.append({"id": name, "vi": vi, "latin": latin, "group": group, "side": name[-1],
                    "region": "upper" if name[:-2] in UPPER_SHOWN else "lower"})
    return {"muscles": out, "groups": GROUPS, "bodies": body_names(exporter.model) + VIRTUAL}


def muscle_ids(exporter):
    """Thứ tự cơ dùng chung cho mọi mảng nfl: cơ thân dưới (Rajagopal) rồi cơ thân trên (MoBL-ARMS)."""
    return [m.getName() for m in exporter.all_muscles] + [f"{n}_{s}" for s in "rl" for n in UPPER_SHOWN]


_UP = []


def upper():
    if not _UP:
        _UP.append(UpperExport(*load_model()))
    return _UP[0]


def _upper_frame(solver, vals, opts):
    """Số liệu cơ thân trên + tư thế bả vai/xương đòn; bài giữ hai tay giống nhau → tay trái là đối xứng tay phải."""
    U = upper()
    torso7 = solver.poser.body_xforms(["torso"])[0]
    sides = ["r", "l"] if opts.get("arms") == "separate" else ["r"]
    nfl, _, _, xf, _ = U.frame(vals, torso7, sides)
    if sides == ["r"]:
        for n in UPPER_SHOWN:
            nfl[f"{n}_l"] = nfl[f"{n}_r"]
    return [None if not np.isfinite(nfl[f"{n}_{s}"]) else round(float(nfl[f"{n}_{s}"]), 4) for s in "rl" for n in UPPER_SHOWN], \
        [np.round(np.array(xf[b], float), 5).tolist() for b in VIRTUAL]


@app.get("/api/templates")
def templates():
    out = []
    for f in sorted(os.listdir(TEMPLATES_DIR)) if os.path.isdir(TEMPLATES_DIR) else []:
        if f.endswith(".json"):
            t = json.load(open(os.path.join(TEMPLATES_DIR, f), encoding="utf-8"))
            out.append({"id": f[:-5], **t.pop("template", {}), "exercise": t})
    out.sort(key=lambda t: t.get("order", 99))
    return out


@app.get("/api/exercises")
def list_exercises():
    out = []
    for f in sorted(os.listdir(EXERCISES_DIR)):
        if not f.endswith(".json"):
            continue
        slug = f[:-5]
        try:
            ex = json.load(open(os.path.join(EXERCISES_DIR, f), encoding="utf-8"))
        except Exception:
            continue
        res = os.path.join(OUTPUT_DIR, slug, "result.json")
        built = os.path.exists(res) and os.path.getmtime(res) >= os.path.getmtime(os.path.join(EXERCISES_DIR, f))
        out.append({"slug": slug, "name": ex.get("name", slug), "mode": ex.get("mode"), "built": built,
                    "has_output": os.path.exists(res)})
    return out


@app.get("/api/exercises/{slug}")
def get_exercise(slug: str):
    p = ex_path(slug)
    if not os.path.exists(p):
        raise HTTPException(404, "Không tìm thấy bài tập.")
    ex = json.load(open(p, encoding="utf-8"))
    res = os.path.join(OUTPUT_DIR, slug, "result.json")
    return {"exercise": ex, "result": json.load(open(res, encoding="utf-8")) if os.path.exists(res) else None}


@app.put("/api/exercises/{slug}")
async def save_exercise(slug: str, req: Request):
    ex = await req.json()
    errs = validate(ex)
    if errs:
        return JSONResponse({"ok": False, "errors": errs}, status_code=422)
    with open(ex_path(slug), "w", encoding="utf-8") as f:
        json.dump(ex, f, ensure_ascii=False, indent=2)
    return {"ok": True, "slug": slug}


@app.post("/api/exercises")
async def create_exercise(req: Request):
    body = await req.json()
    ex = body["exercise"]
    slug = base = slugify(ex.get("name", "bai-tap"))
    i = 2
    while os.path.exists(ex_path(slug)):
        slug, i = f"{base}-{i}", i + 1
    with open(ex_path(slug), "w", encoding="utf-8") as f:
        json.dump(ex, f, ensure_ascii=False, indent=2)
    return {"ok": True, "slug": slug}


@app.delete("/api/exercises/{slug}")
def delete_exercise(slug: str):
    p = ex_path(slug)
    if os.path.exists(p):
        os.remove(p)
    shutil.rmtree(os.path.join(OUTPUT_DIR, slug), ignore_errors=True)
    return {"ok": True}


# Hai API xem trước là hàm thường (không async): FastAPI chạy chúng ở luồng riêng, nên phép giải
# nặng không chặn các yêu cầu khác (lưu bài, danh sách bài…).
@app.post("/api/preview")
def preview(body: dict = Body(...)):
    ex, phase = body["exercise"], float(body.get("phase", 0))
    errs = validate(ex)
    if errs:
        return JSONResponse({"ok": False, "errors": errs}, status_code=422)
    with LOCK:
        solver, _ = builder.tools()
        try:
            x0 = body.get("x0")
            vals, _, info = solver.pose(ex, phase, None if x0 is None else np.array(x0, float), _refinfo(solver, ex))
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"ok": False, "errors": [str(e)]}, status_code=422)
        bodies = body_names(solver.model)
        xf = solver.poser.body_xforms(bodies)
        com = solver.poser.com()
        full = solver.poser.values()
        unfl, uxf = _upper_frame(solver, full, ex.get("options", {}))
        _, exporter = builder.tools()
        nfl = _pose_nfl(exporter, full) + unfl
        bodies, xf = bodies + VIRTUAL, list(xf) + uxf
    solved = {k: round(float(vals[k]), 1) for k in
              ["hip_flexion_r", "hip_flexion_l", "knee_angle_r", "knee_angle_l", "ankle_angle_r", "ankle_angle_l",
               "hip_adduction_r", "hip_rotation_r", "pelvis_ty"]}
    solved["trunk_lean"] = round(float(-vals["pelvis_tilt"] - vals["lumbar_extension"]), 1)
    solved.update(_arm_solved(vals))
    return jsonable({"ok": True, "bodies": bodies, "xforms": xf, "info": info, "solved": solved, "com": list(com), "nfl": nfl})


_REF = {}


def _refinfo(solver, ex):
    """Chỗ neo bàn chân (kiểu tự do) chỉ phụ thuộc tư thế phase 0 và tuỳ chọn → lưu tạm."""
    if ex["mode"] != "free":
        return None
    key = json.dumps([ex["keyframes"][0], ex.get("options", {})], sort_keys=True)
    if key not in _REF:
        if len(_REF) > 16:
            _REF.clear()
        _REF[key] = solver.free_reference(curves(ex), ex.get("options", {}))
    return _REF[key]


def _arm_solved(v):
    return {k: round(float(v.get(k, 0.0)), 1) for k in ("arm_flex_r", "elbow_flex_r", "arm_flex_l", "elbow_flex_l")} | \
        {"arm_abd_r": round(float(-v.get("arm_add_r", 0.0)), 1), "arm_abd_l": round(float(-v.get("arm_add_l", 0.0)), 1)}


def _pose_nfl(exporter, vals):
    """l/l_opt của mọi cơ ở tư thế vals (cùng cách tính với bước xuất dữ liệu)."""
    exporter.poser.set(vals)
    equilibrate(exporter.model, exporter.state, exporter.all_muscles)
    return [round(m.getNormalizedFiberLength(exporter.state), 4) for m in exporter.all_muscles]


@app.post("/api/preview_motion")
def preview_motion(body: dict = Body(...)):
    """Lấy mẫu toàn bộ chuyển động (phase 0 → 1) để Studio phát lại và tô màu cơ."""
    ex = body["exercise"]
    errs = validate(ex)
    if errs:
        return JSONResponse({"ok": False, "errors": errs}, status_code=422)
    n = int(body.get("samples", 21))
    phases = sorted({round(float(p), 4) for p in np.linspace(0, 1, n)} | {float(k["phase"]) for k in ex["keyframes"]})
    with LOCK:
        solver, exporter = builder.tools()
        try:
            refinfo = _refinfo(solver, ex)
            x = (refinfo or {}).get("x0")
            xs = []
            bodies = body_names(solver.model)
            opts = ex.get("options", {})
            xforms, nfl, infos, solved = [], [], [], []
            for ph in phases:
                vals, x, info = solver.pose(ex, ph, x, refinfo)
                xs.append(None if x is None else [round(float(v), 5) for v in x])
                full = solver.poser.values()
                unfl, uxf = _upper_frame(solver, full, opts)
                xforms.append(np.round(np.array(solver.poser.body_xforms(bodies)), 5).ravel().tolist() + [c for q in uxf for c in q])
                nfl.append(_pose_nfl(exporter, full) + unfl)
                infos.append({"err_cm": round(float(info.get("err_cm", 0)), 2), "adjust_deg": round(float(info.get("adjust_deg", 0)), 1),
                              "adjust": info.get("adjust", {})})
                solved.append({k: round(float(full[k]), 1) for k in
                               ["hip_flexion_r", "hip_flexion_l", "knee_angle_r", "knee_angle_l", "ankle_angle_r", "ankle_angle_l"]}
                              | {"trunk_lean": round(float(-full["pelvis_tilt"] - full["lumbar_extension"]), 1),
                                 "pelvis_ty": round(float(full["pelvis_ty"]), 3)} | _arm_solved(full))
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"ok": False, "errors": [str(e)]}, status_code=422)
    tl = timeline(ex.get("timing"))
    return jsonable({"ok": True, "bodies": bodies + VIRTUAL, "phases": phases, "xforms": xforms, "nfl": nfl, "info": infos, "solved": solved, "x": xs,
                     "muscles": muscle_ids(exporter),
                     "timeline": {"t": [round(t, 3) for t, _ in tl], "phase": [round(p, 4) for _, p in tl]}})


@app.post("/api/build/{slug}")
def build(slug: str, draft: bool = False):
    p = ex_path(slug)
    if not os.path.exists(p):
        raise HTTPException(404, "Hãy lưu bài tập trước.")
    ex = json.load(open(p, encoding="utf-8"))
    logs = []
    with LOCK:
        try:
            res = builder.build(ex, slug=slug, log=logs.append, run_qa=not draft)
        except ValueError as e:
            return JSONResponse({"ok": False, "errors": str(e).split("\n")}, status_code=422)
    res.pop("folder", None)
    res["draft"] = draft
    return jsonable({"ok": True, "result": res, "log": logs})


@app.get("/api/download/{slug}")
def download(slug: str):
    res = os.path.join(OUTPUT_DIR, slug, "result.json")
    if os.path.exists(res):
        qa = json.load(open(res, encoding="utf-8")).get("qa") or {}
        if qa.get("status") == "fail":
            raise HTTPException(409, "Bản này không đạt kiểm tra chất lượng hình học — sửa bài rồi tạo lại.")
    ex_path(slug)  # kiểm tra tên hợp lệ
    folder = os.path.join(OUTPUT_DIR, slug)
    if not os.path.isdir(folder):
        raise HTTPException(404, "Chưa có dữ liệu — bấm 'Tạo dữ liệu' trước.")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(folder):
            for f in files:
                if f.startswith("_"):
                    continue
                full = os.path.join(root, f)
                z.write(full, os.path.join(slug, os.path.relpath(full, folder)))
        ex = ex_path(slug)
        if os.path.exists(ex):
            z.write(ex, os.path.join(slug, "exercise.json"))
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{slug}.zip"'})


app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")
app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")


def _port_free(port):
    """True nếu cổng chưa có chương trình nào đang nghe (thử chiếm cổng)."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):   # Windows: chặn việc 'chia sẻ' cổng
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:   # Linux/macOS: bỏ qua kết nối cũ đang TIME_WAIT, vẫn từ chối nếu có server đang nghe
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _is_studio(port):
    """True nếu cổng đang là một Anatomy Studio khác (mở từ lần chạy trước)."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/meta", timeout=1.5) as r:
            return {"columns", "options"} <= set(json.loads(r.read().decode("utf-8")))
    except Exception:
        return False


if __name__ == "__main__":
    import argparse
    import uvicorn
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()

    port = None
    for p in range(a.port, a.port + 20):
        if _port_free(p):
            port = p
            break
        if _is_studio(p):   # Studio đã chạy sẵn ở cửa sổ khác → chỉ mở lại trình duyệt
            url = f"http://127.0.0.1:{p}"
            print(f"\n  Anatomy Studio ĐÃ chạy sẵn tại {url} (ở một cửa sổ khác).")
            if not a.no_browser:
                webbrowser.open(url)
                print("  Đã mở lại trình duyệt.")
            print("  Muốn khởi động lại Studio: đóng cửa sổ cmd cũ rồi chạy lại.\n")
            raise SystemExit(0)
        print(f"  Cổng {p} đang bị chương trình khác dùng, thử cổng {p + 1}…")
    if port is None:
        raise SystemExit(f"Không tìm được cổng trống từ {a.port} đến {a.port + 19}. "
                         f"Chạy: python studio.py --port 9000")

    url = f"http://127.0.0.1:{port}"
    print(f"\n  Anatomy Studio đang chạy tại {url}  (Ctrl+C để tắt)\n")
    if not a.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
