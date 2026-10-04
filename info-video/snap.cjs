// Render still frames for review: node snap.cjs <outDir> [t1 t2 ...]
// With no times, saves one frame near the end of every scene.
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const out = process.argv[2] || 'frames';
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('file://' + path.join(__dirname, 'dist', 'standalone.html') + '?export=1');
  await page.waitForFunction(() => window.__video);
  await page.evaluate(() => window.__video.ready);
  let times = process.argv.slice(3).map(Number);
  if (!times.length) {
    const cues = await page.evaluate(() => window.__video.cues());
    const total = await page.evaluate(() => window.__video.total);
    console.log('total', total.toFixed(1), 's');
    times = cues.map(q => q.end - 0.3);
  }
  for (const t of times) {
    const url = await page.evaluate(t => window.__video.frame(t), t);
    fs.writeFileSync(path.join(out, `t${t.toFixed(1).padStart(6, '0')}.jpg`), Buffer.from(url.split(',')[1], 'base64'));
  }
  if (errors.length) console.log('ERRORS:\n' + errors.join('\n'));
  await browser.close();
  console.log('saved', times.length, 'frames to', out);
})();
