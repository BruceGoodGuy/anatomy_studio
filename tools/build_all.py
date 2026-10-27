"""Dựng hàng loạt + kiểm tra chất lượng: bài trong exercises/ và/hoặc các mẫu trong templates/.

  python tools/build_all.py all | ex | tpl-upper | tpl-lower
Mẫu được dựng vào output/_tpl-<tên>/ (giữ lại để tools/validate_muscles.py đối chiếu; xoá trước khi
đóng gói). In mỗi bài một dòng: trạng thái QA, chỉ số tệ nhất, cảnh báo, 5 cơ giãn nhất.
"""
import json, os, sys, glob, time, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from pipeline import build
which = sys.argv[1] if len(sys.argv) > 1 else "all"
jobs = []
if which in ("all", "tpl-upper"):
    jobs += [(f, "_tpl-" + os.path.basename(f)[3:-5]) for f in sorted(glob.glob("templates/*.json")) if int(os.path.basename(f)[:2]) >= 12]
if which in ("all", "ex"):
    jobs += [(f, os.path.basename(f)[:-5]) for f in sorted(glob.glob("exercises/*.json"))]
if which in ("all", "tpl-lower"):
    jobs += [(f, "_tpl-" + os.path.basename(f)[3:-5]) for f in sorted(glob.glob("templates/*.json")) if int(os.path.basename(f)[:2]) < 12]
for path, slug in jobs:
    ex = json.load(open(path, encoding="utf-8")); ex.pop("template", None)
    t = time.time()
    try:
        r = build.build(ex, slug=slug, log=lambda m: None)
    except Exception as e:
        print(f"{slug:<28} ERROR {e}", flush=True); continue
    q = r["qa"]
    fails = [i for i in q["issues"] if i["level"] == "fail"]
    print(f"{slug:<28} {q['status']:<5} {time.time()-t:5.0f}s flips<={q['summary']['flips_max']} edge<=x{q['summary']['edge_max']:.1f} fold<={q['summary']['jac_neg_pct_max']:.1f}% pen<={q['summary']['penetration_max_mm']:.1f}mm warn={len(r['warnings'])}", flush=True)
    for i in fails: print("    FAIL", i["muscle"], i["text"], flush=True)
    for w in r["warnings"]: print("    !", w, flush=True)
    print("    top:", ", ".join(f"{t['vi']} {t['nfl_max']:.2f}" for t in r["top"][:5]), flush=True)
