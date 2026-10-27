// Kiểm thử giao diện bằng Playwright (Chromium headless, swiftshader). Cần Studio đang chạy ở cổng 8765:
//   python studio.py --no-browser --port 8765
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [list, view] = process.argv.slice(2);
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const p = await b.newPage({ viewport: { width: 1500, height: 920 } });
  p.on('pageerror', e => console.log('pageerror: ' + e.message));
  for (const slug of list.split(',')) {
    await p.goto(`http://127.0.0.1:8765/?ex=${slug}`, { waitUntil: 'load' });
    const ok = await p.waitForFunction(() => window.studio && window.studio.S.samples, null, { timeout: 120000 }).then(() => true).catch(() => false);
    if (!ok) { console.log(slug, 'no samples'); continue; }
    const out = await p.evaluate(async (view) => {
      const s = window.studio; s.setTab('photo'); s.PH.long = 700; s.PH.aspect = '1:1'; s.PH.title = true; s.PH.bg = 'solid'; s.PH.c1 = '#ffffff'; s.PH.bone = 0.5;
      s.setView(view); document.getElementById('ph-fit').click();
      const res = [];
      for (const ph of [0, 1]) res.push(s.snap({ phase: ph }).toDataURL('image/png'));
      return [res, JSON.stringify(s.S.samples.info.map(i => i.err_cm).reduce((a, b) => Math.max(a, b), 0))];
    }, view);
    out[0].forEach((d, i) => fs.writeFileSync(`tp_${slug}_${i}.png`, Buffer.from(d.split(',')[1], 'base64')));
    console.log(slug, 'maxerr', out[1]);
  }
  await b.close();
})();
