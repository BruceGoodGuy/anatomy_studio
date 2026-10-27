// Kiểm thử giao diện bằng Playwright (Chromium headless, swiftshader). Cần Studio đang chạy ở cổng 8765:
//   python studio.py --no-browser --port 8765
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [url, prefix, js] = process.argv.slice(2);
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const p = await b.newPage({ viewport: { width: 1500, height: 920 } });
  p.on('pageerror', e => console.log('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !m.text().includes('Failed to load resource')) console.log('console: ' + m.text()); });
  await p.goto(url, { waitUntil: 'load' });
  await p.waitForFunction(() => window.studio && window.studio.S.samples, null, { timeout: 60000 }).catch(() => console.log('no samples'));
  await p.waitForTimeout(500);
  const r = await p.evaluate(js);
  await p.waitForTimeout(1200);
  await p.screenshot({ path: `${prefix}_ui.png` });
  const shots = await p.evaluate(async () => { const s = window.studio; const c = s.snap(); return [c.toDataURL('image/png'), c.width, c.height]; });
  fs.writeFileSync(`${prefix}_shot.png`, Buffer.from(shots[0].split(',')[1], 'base64'));
  console.log('shot', shots[1], shots[2], r || '');
  await b.close();
})();
