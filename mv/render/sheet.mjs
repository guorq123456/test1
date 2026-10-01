#!/usr/bin/env node
// QA contact sheet: render MV frames at given times to PNGs (lossless, straight from the canvas)
// and assemble a labelled contact sheet JPEG with ImageMagick `montage`.
import fsp from 'node:fs/promises';
import path from 'node:path';
import {
  MV_ROOT, RENDER_DIR, DEFAULT_URL, fail, timecode,
  launchBrowser, openMV, grabFrame, resolveUrl, run, parseCli,
} from './lib.mjs';

const SPEC = {
  url: { default: DEFAULT_URL },
  serve: { type: 'boolean', default: false },
  root: { default: MV_ROOT },
  port: { type: 'number', default: 0 },
  times: { default: undefined },
  every: { type: 'number', default: 0 },
  start: { type: 'number', default: 0 },
  end: { type: 'number', default: undefined },
  outDir: { default: path.join(RENDER_DIR, 'sheet') },
  name: { default: 'contact.jpg' },
  cols: { type: 'number', default: 5 },
  thumb: { type: 'number', default: 384 },
  quality: { type: 'number', default: 88 },
  chrome: { default: undefined },
  gpu: { type: 'boolean', default: false },
  timeout: { type: 'number', default: 180 },
  allowConsoleErrors: { type: 'boolean', default: false },
  help: { type: 'boolean', default: false },
};

const HELP = `Usage: node sheet.mjs (--times 0,10,20.5 | --every 10) [options]

  --times <list>       comma-separated times in seconds
  --every <s>          one frame every N seconds over [--start, --end)
  --start / --end <s>  range for --every (default 0 .. MV.duration)
  --out-dir <dir>      where PNGs + sheet go (default ${path.join(RENDER_DIR, 'sheet')})
  --name <file>        contact sheet file name (default contact.jpg)
  --cols <n>           sheet columns (default 5)     --thumb <px>   tile width (default 384)
  --quality <q>        sheet JPEG quality (default 88)
  --url / --serve / --root / --port / --chrome / --gpu / --timeout / --allow-console-errors  as in render.mjs
`;

const opt = parseCli(process.argv.slice(2), SPEC);
if (opt.help) { process.stdout.write(HELP); process.exit(0); }
if (!opt.times && !(opt.every > 0)) fail('give --times a,b,c or --every N (see --help)');

let browser, server, code = 0;
try {
  const r = await resolveUrl(opt);
  server = r.server;
  browser = await launchBrowser({ chrome: opt.chrome, gpu: opt.gpu });
  const mv = await openMV(browser, r.url, { timeout: opt.timeout * 1000, allowConsoleErrors: opt.allowConsoleErrors });
  const { info } = mv;

  let times;
  if (opt.times) {
    times = String(opt.times).split(',').map((s) => s.trim()).filter(Boolean).map(Number);
    if (times.some((t) => !Number.isFinite(t))) throw new Error(`bad --times "${opt.times}"`);
  } else {
    const end = opt.end ?? info.duration;
    times = [];
    for (let k = 0; ; k++) { const t = +(opt.start + k * opt.every).toFixed(6); if (t >= end) break; times.push(t); }
  }
  const outDir = path.resolve(opt.outDir);
  await fsp.mkdir(outDir, { recursive: true });

  const sectionAt = (t) => info.sections.find((s) => t >= s.start && t < s.end)?.id;
  const montageArgs = [];
  console.log(`[sheet] ${times.length} frames from ${r.url} -> ${outDir}`);
  for (const t of times) {
    const t0 = performance.now();
    const png = await grabFrame(mv, t, 'png');
    const file = path.join(outDir, `t${t.toFixed(3).padStart(8, '0')}.png`);
    await fsp.writeFile(file, png);
    const sec = sectionAt(t);
    const label = `t=${t}s  ${timecode(t)}${sec ? '  ' + sec : ''}`;
    montageArgs.push('-label', label, file);
    console.log(`  ${path.basename(file)}  ${label}  (${(performance.now() - t0).toFixed(0)} ms)`);
  }

  const sheet = path.join(outDir, opt.name);
  const cols = Math.max(1, Math.min(opt.cols, times.length));
  const th = Math.round(opt.thumb * info.height / info.width);
  await run('montage', [
    '-font', 'DejaVu-Sans', '-pointsize', String(Math.max(11, Math.round(opt.thumb / 26))),
    '-fill', '#e8e8e8', '-background', '#151515',
    ...montageArgs,
    '-tile', `${cols}x`, '-geometry', `${opt.thumb}x${th}+6+6`,
    '-title', `MV contact sheet  (${times.length} frames)`,
    '-quality', String(opt.quality), sheet,
  ]);
  console.log(`[sheet] contact sheet: ${sheet}`);
} catch (e) {
  console.error(`[sheet] FAILED: ${e.message}`);
  code = 1;
}
await Promise.allSettled([browser?.close(), server?.close()]);
process.exit(code);
