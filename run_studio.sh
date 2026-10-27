#!/usr/bin/env bash
# Anatomy Studio (Linux; macOS xem README — OpenSim cho Mac cài bằng conda).
# OpenSim 4.6 chỉ có bản cài cho Python 3.11–3.13.
set -e
cd "$(dirname "$0")"
CHECK="import opensim, numpy, scipy, trimesh, fastapi, uvicorn"
if [ -x .venv/bin/python ] && .venv/bin/python -c "$CHECK" 2>/dev/null; then
  exec .venv/bin/python studio.py
fi
rm -rf .venv
PY=""
for c in python3.12 python3.13 python3.11 python3; do
  if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)'; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "Không tìm thấy Python 3.11–3.13 (OpenSim 4.6 chưa hỗ trợ bản khác). Hãy cài Python 3.12 rồi chạy lại."; exit 1
fi
echo "Dùng $($PY --version)"
"$PY" -m venv .venv
if ! .venv/bin/pip install --upgrade pip || ! .venv/bin/pip install -r requirements.txt || ! .venv/bin/python -c "$CHECK"; then
  rm -rf .venv; echo "Cài thư viện thất bại (xem lỗi phía trên). Đã xoá .venv để lần sau cài lại."; exit 1
fi
exec .venv/bin/python studio.py
