// Build: src/video.html -> dist/index.html (artifact body) + dist/standalone.html (opens locally).
// Fonts are subset to exactly the characters the video draws and inlined as data URIs,
// so the page and the rendered MP4 use the same type with no network at play time.
//
// Usage: node build.cjs
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const ROOT = __dirname;
const SRC = path.join(ROOT, 'src', 'video.html');
const DIST = path.join(ROOT, 'dist');
const CACHE = path.join(ROOT, '.font-cache');
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

const skeleton = body =>
  `<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n` +
  `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n` +
  `</head>\n<body>\n${body}\n</body>\n</html>\n`;

async function collectChars(srcBody) {
  const tmp = path.join(CACHE, 'collect.html');
  fs.writeFileSync(tmp, skeleton(srcBody));
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + tmp + '?export=1');
  await page.waitForFunction(() => window.__video);
  const used = await page.evaluate(() => window.__video.collect());
  await browser.close();
  return used;
}

function curl(url, out) {
  const args = ['-sS', '--fail', '-A', UA, url];
  if (out) args.push('-o', out);
  return execFileSync('curl', args, { maxBuffer: 64 * 1024 * 1024 });
}

function fontFaces(family, weights, chars) {
  const list = [...new Set(Array.from(chars))].filter(ch => ch.trim() || ch === ' ').sort();
  const chunks = [];
  for (let i = 0; i < list.length; i += 180) chunks.push(list.slice(i, i + 180));
  const css = [];
  let bytes = 0;
  chunks.forEach(chunk => {
    const fam = family.replace(/ /g, '+') + (weights ? `:wght@${weights.join(';')}` : '');
    const url = `https://fonts.googleapis.com/css2?family=${fam}&text=${encodeURIComponent(chunk.join(''))}`;
    const sheet = curl(url).toString();
    const range = chunk.map(ch => 'U+' + ch.codePointAt(0).toString(16).toUpperCase()).join(',');
    for (const m of sheet.matchAll(/@font-face\s*{([^}]*)}/g)) {
      const block = m[1];
      const weight = (block.match(/font-weight:\s*(\d+)/) || [])[1] || '400';
      const src = (block.match(/url\((https:[^)]+)\)/) || [])[1];
      if (!src) continue;
      const file = path.join(CACHE, Buffer.from(src).toString('base64url').slice(-60) + '.font');
      if (!fs.existsSync(file)) curl(src, file);
      const data = fs.readFileSync(file);
      bytes += data.length;
      css.push(`@font-face{font-family:"${family}";font-style:normal;font-weight:${weight};font-display:swap;` +
        `src:url(data:font/woff2;base64,${data.toString('base64')}) format("woff2");unicode-range:${range};}`);
    }
  });
  console.log(`  ${family.padEnd(16)} ${String(list.length).padStart(4)} chars  ${(bytes / 1024).toFixed(0)} KB`);
  return css.join('\n');
}

(async () => {
  fs.mkdirSync(DIST, { recursive: true });
  fs.mkdirSync(CACHE, { recursive: true });
  const src = fs.readFileSync(SRC, 'utf8');

  console.log('Collecting the characters each font draws…');
  const used = await collectChars(src);
  const ascii = Array.from({ length: 95 }, (_, i) => String.fromCharCode(32 + i)).join('');
  const allText = ascii + Array.from(src).filter(ch => ch.codePointAt(0) > 127).join('');
  const domDisplay = [...src.matchAll(/<h[12][^>]*>([^<]*)<\/h[12]>/g)].map(m => m[1]).join('');

  console.log('Fetching font subsets…');
  const css = [
    fontFaces('Noto Sans SC', [400, 700], allText + used.body),
    fontFaces('Noto Serif SC', [700], used.display + domDisplay),
    fontFaces('Long Cang', null, used.hand),
    fontFaces('JetBrains Mono', [400, 600], ascii + used.mono.replace(/[^\x20-\x7e×−…→₂Σ·≈]/g, '')),
  ].join('\n');

  const out = src.replace('/*FONTS*/', css);
  fs.writeFileSync(path.join(DIST, 'index.html'), out);
  fs.writeFileSync(path.join(DIST, 'standalone.html'), skeleton(out));
  const kb = f => (fs.statSync(path.join(DIST, f)).size / 1024).toFixed(0) + ' KB';
  console.log(`Wrote dist/index.html (${kb('index.html')}) and dist/standalone.html (${kb('standalone.html')})`);
})().catch(e => { console.error(e); process.exit(1); });
