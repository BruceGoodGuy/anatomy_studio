"""Tạo toàn bộ dữ liệu cho một bài tập: chuyển động → dữ liệu cơ → trang viewer.

Dùng từ dòng lệnh:
    python -m pipeline.build exercises/squat-khong-ta.json      (thêm --no-qa để bỏ bước kiểm tra)
Trả mã lỗi 1 nếu một bài KHÔNG ĐẠT kiểm tra chất lượng.
Kết quả nằm trong output/<tên-bài>/:
    viewer.html        trang xem 3D, MỘT file, mở trực tiếp hoặc nhúng vào blog
    motion.mot         chuyển động (mở được bằng OpenSim GUI)
    angles.csv         góc khớp theo thời gian
    muscles.csv        bảng xếp hạng độ giãn của từng cơ
    qa.json            kết quả kiểm tra chất lượng hình học (lật, rách, gập, xuyên giữa cơ)
    data/              dữ liệu rời (motion.json, xương, mesh Z-Anatomy) nếu muốn tự dựng trang
"""
import csv
import json
import os
import shutil
import sys
import time

from .common import ASSETS, OUTPUT_DIR, WEB_DIR, slugify
from .export import Exporter
from .motion import MotionSolver, write_mot, load_exercise
from .stretch import rank_key

CDN = ("https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
       "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/")
LOCAL = ("/web/vendor/three/three.module.js", "/web/vendor/three/addons/")

_solver = _exporter = None


def tools():
    global _solver, _exporter
    if _solver is None:
        _solver, _exporter = MotionSolver(), Exporter()
    return _solver, _exporter


def core_js():
    """web/anatomy-core.js, chèn thẳng vào trang (trang blog phải là MỘT file)."""
    import re
    src = open(os.path.join(WEB_DIR, "anatomy-core.js"), encoding="utf-8").read()
    src = re.sub(r'^import \* as THREE from "three";\n', "", src, flags=re.M)
    return re.sub(r"^export ", "", src, flags=re.M)


def page(template, motion_txt, bones_txt, zanat_txt, three, full_document=True, title=None, zanat_upper_txt=""):
    html = template.replace("__THREE_MODULE__", three[0]).replace("__THREE_ADDONS__", three[1])
    html = html.replace("// @@ANATOMY_CORE@@", core_js(), 1)
    if title:
        import html as _h
        html = html.replace("<title>Muscle Stretch Viewer</title>", f"<title>{_h.escape(title)}</title>", 1)
    if full_document:   # trang HTML hoàn chỉnh để mở trực tiếp / nhúng iframe
        head, body = html.split('<div class="wrap">', 1)
        html = ('<!doctype html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                + head + '</head>\n<body>\n<div class="wrap">' + body + '\n</body>\n</html>\n')
    blocks = (f'<script type="application/json" id="data-motion">{motion_txt}</script>\n'
              f'<script type="application/json" id="data-bones">{bones_txt}</script>\n')
    if zanat_txt:
        blocks += f'<script type="application/json" id="data-zanat">{zanat_txt}</script>\n'
    if zanat_upper_txt:
        blocks += f'<script type="application/json" id="data-zanat-upper">{zanat_upper_txt}</script>\n'
    return html.replace('<script type="importmap">', blocks + '<script type="importmap">', 1)


_qa_binding = None


def qa_binding():
    global _qa_binding
    if _qa_binding is None:
        from .qa import bindings
        _qa_binding = bindings()
    return _qa_binding


def build(ex, slug=None, log=print, run_qa=True):
    t0 = time.time()
    slug = slug or slugify(ex.get("name", "bai-tap"))
    out = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    solver, exporter = tools()

    log("1/4 Giải chuyển động…")
    times, rows, summary, warnings = solver.build(ex)
    write_mot(os.path.join(out, "motion.mot"), times, rows)
    with open(os.path.join(out, "angles.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)

    log("2/4 Tính đường cơ và chiều dài sợi cơ…")
    data = exporter.run(times, rows, ex)
    data["phase"] = [r["phase"] for r in summary]
    warnings = warnings + data.pop("upper_warnings", [])
    data["warnings"] = warnings
    vpath = os.path.join(os.path.dirname(WEB_DIR), "docs", "kiem-chung.json")
    if os.path.exists(vpath):
        data["validation"] = json.load(open(vpath, encoding="utf-8")).get("sentence")
    motion_txt = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(out, "data", "motion.json"), "w", encoding="utf-8") as f:
        f.write(motion_txt)
    names = {m["id"]: m for m in data["muscles"]}
    ranked = sorted(data["summary"], key=lambda r: rank_key({"beyond": r["beyond_opt"], "change": r["fiber_change_pct"]}), reverse=True)
    with open(os.path.join(out, "muscles.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["co", "latin", "nhom", "bi_keo_gian", "luc_bat_dau_l/lopt", "dai_nhat_l/lopt", "vuot_toi_uu", "thoi_diem_s",
                    "soi_co_dai_them_%", "co_va_gan_dai_them_%"])
        for r in ranked:
            m = names[r["id"]]
            w.writerow([m["vi"], m["latin"], data["groups"][m["group"]]["vi"], "co" if r["stretched"] else "khong",
                        r["nfl_start"], r["nfl_max"], r["beyond_opt"], r["t_max"], r["fiber_change_pct"], r["mtu_change_pct"]])

    log("3/4 Đóng gói trang viewer…")
    bones_path = os.path.join(ASSETS, "osim.bones.json")
    zanat_path = os.path.join(ASSETS, "zanat_binding.json")
    shutil.copy(bones_path, os.path.join(out, "data", "osim.bones.json"))
    zanat_txt = zupper_txt = ""
    if os.path.exists(zanat_path):
        shutil.copy(zanat_path, os.path.join(out, "data", "zanat_binding.json"))
        zanat_txt = open(zanat_path, encoding="utf-8").read()
    zupper_path = os.path.join(ASSETS, "zanat_upper.json")
    if os.path.exists(zupper_path):
        shutil.copy(zupper_path, os.path.join(out, "data", "zanat_upper.json"))
        zupper_txt = open(zupper_path, encoding="utf-8").read()
    bones_txt = open(bones_path, encoding="utf-8").read()
    template = open(os.path.join(WEB_DIR, "viewer.html"), encoding="utf-8").read()
    with open(os.path.join(out, "viewer.html"), "w", encoding="utf-8") as f:
        f.write(page(template, motion_txt, bones_txt, zanat_txt, CDN, title=ex.get("name"), zanat_upper_txt=zupper_txt))
    with open(os.path.join(out, "_preview.html"), "w", encoding="utf-8") as f:   # dùng three.js trong máy (Studio)
        f.write(page(template, motion_txt, bones_txt, zanat_txt, LOCAL, title=ex.get("name"), zanat_upper_txt=zupper_txt))
    top = [{"vi": names[r["id"]]["vi"], "nfl_max": r["nfl_max"], "nfl_start": r["nfl_start"], "stretched": r["stretched"],
            "fiber_change_pct": r["fiber_change_pct"], "t_max": r["t_max"]}
           for r in ranked if names[r["id"]]["group"] != "other" and r["nfl_max"] is not None][:10]

    qa_rep = None
    if zanat_txt and run_qa:
        log("4/4 Kiểm tra chất lượng hình học của cơ (khoảng 1 phút)…")
        from . import qa as qa_mod
        qa_rep = qa_mod.run_all(data, qa_binding(), stride=2, log=log)
        with open(os.path.join(out, "qa.json"), "w", encoding="utf-8") as f:
            json.dump(qa_rep, f, ensure_ascii=False, indent=1)
        log({"pass": "Kiểm tra: ĐẠT", "warn": "Kiểm tra: ĐẠT (có ghi chú)", "fail": "Kiểm tra: KHÔNG ĐẠT"}[qa_rep["status"]])
    result = {"slug": slug, "folder": out, "seconds": round(time.time() - t0, 1), "warnings": warnings, "top": top,
              "frames": len(times), "symmetric": data["mirror"],
              "size_mb": round(os.path.getsize(os.path.join(out, "viewer.html")) / 1e6, 1),
              "qa": None if qa_rep is None else {"status": qa_rep["status"], "summary": qa_rep["summary"],
                                                 "issues": qa_rep["issues"]}}
    with open(os.path.join(out, "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    log(f"Xong sau {result['seconds']} s → {out}")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    failed = 0
    for path in args:
        ex = load_exercise(path)
        r = build(ex, slug=os.path.splitext(os.path.basename(path))[0], run_qa="--no-qa" not in sys.argv,
                  log=lambda m: None if m.startswith("  kiểm tra") else print(m))
        for w in r["warnings"]:
            print("  ! " + w)
        if r["qa"]:
            for i in r["qa"]["issues"]:
                if i["level"] == "fail":
                    print(f"  LỖI {i['muscle']}: {i['text']}")
            failed += r["qa"]["status"] == "fail"
        for t in r["top"][:5]:
            print(f"  {t['vi']:<28} {t['nfl_max']:.2f}  (+{t['fiber_change_pct']}%)")
    sys.exit(1 if failed else 0)
