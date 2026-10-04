// Render dist/standalone.html to an MP4, frame by frame (deterministic: every frame is a pure function of time).
// Usage: node render.cjs [out.mp4] [fps] [workers]
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, execFileSync } = require('child_process');
const { chromium } = require('playwright');

const OUT = path.resolve(process.argv[2] || path.join(__dirname, 'dist', 'answer-birth.mp4'));
const FPS = Number(process.argv[3] || 30);
const WORKERS = Number(process.argv[4] || Math.max(1, Math.min(4, os.cpus().length)));
const PAGE = 'file://' + path.join(__dirname, 'dist', 'standalone.html') + '?export=1';
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'answer-video-'));

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', e => { throw e; });
  await page.goto(PAGE);
  await page.waitForFunction(() => window.__video);
  await page.evaluate(() => window.__video.ready);
  return page;
}

async function renderSegment(k, f0, f1, onFrame) {
  const browser = await chromium.launch();
  const page = await openPage(browser);
  const seg = path.join(TMP, `seg${k}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', String(FPS), seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exit ' + c)))));
  for (let f = f0; f < f1; f++) {
    const url = await page.evaluate(t => window.__video.frame(t), f / FPS);
    const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    onFrame();
  }
  ff.stdin.end();
  await done;
  await browser.close();
  return seg;
}

(async () => {
  const probe = await chromium.launch();
  const page = await openPage(probe);
  const total = await page.evaluate(() => window.__video.total);
  const cues = await page.evaluate(() => window.__video.cues());
  await probe.close();

  const frames = Math.ceil(total * FPS);
  console.log(`Video ${total.toFixed(1)} s · ${frames} frames @ ${FPS} fps · ${WORKERS} workers`);
  const per = Math.ceil(frames / WORKERS);
  let doneFrames = 0, lastPct = -1;
  const tick = () => {
    doneFrames++;
    const pct = Math.floor(doneFrames / frames * 100);
    if (pct % 10 === 0 && pct !== lastPct) { lastPct = pct; console.log(`  ${pct}%`); }
  };
  const t0 = Date.now();
  const segs = await Promise.all(Array.from({ length: WORKERS }, (_, k) =>
    renderSegment(k, k * per, Math.min(frames, (k + 1) * per), tick)));

  const list = path.join(TMP, 'list.txt');
  fs.writeFileSync(list, segs.map(s => `file '${s}'`).join('\n'));
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', OUT]);

  // Soft subtitles too, for players that let viewers restyle them.
  const ts = s => { const ms = Math.round(s * 1000); const h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, sec = Math.floor(ms / 1000) % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')},${String(ms % 1000).padStart(3, '0')}`; };
  const srt = cues.map((q, i) => `${i + 1}\n${ts(q.start)} --> ${ts(q.end)}\n${q.text}\n`).join('\n');
  fs.writeFileSync(OUT.replace(/\.mp4$/, '.srt'), srt);

  fs.rmSync(TMP, { recursive: true, force: true });
  const mb = (fs.statSync(OUT).size / 1048576).toFixed(1);
  console.log(`Wrote ${OUT} (${mb} MB) in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
})().catch(e => { console.error(e); process.exit(1); });
