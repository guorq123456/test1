#!/usr/bin/env python3
"""Build mv/dist/: one self-contained index.html (inline CSS + JS, fonts as base64 data URIs)
plus the PNG assets and timeline.json it fetches with relative URLs.

The main build (mv/index.html, mv/css, mv/js) is the source of truth and is NOT modified;
dist-only changes are applied here as checked string substitutions."""
import base64, json, re, shutil, sys
from pathlib import Path
from fontTools import subset as ftsubset
from fontTools.ttLib import TTFont

MV = Path('/home/user/test1/mv')
SCR = MV / 'fonts'
SUBSET_FONTS = SCR / 'subset'
OUT = MV / 'dist'


def sub(src, old, new, count=1):
    n = src.count(old)
    if n != count:
        sys.exit(f'substitution failed ({n}x, expected {count}): {old[:80]!r}')
    return src.replace(old, new)


# ------------------------------------------------------------------ JS bundle
def strip_exports(src):
    names = []
    for m in re.finditer(r'^export\s+(?:async\s+)?function\s+(\w+)', src, re.M):
        names.append(m.group(1))
    for m in re.finditer(r'^export\s+(?:const|let|var)\s+([^=;]+?)=', src, re.M):
        names.append(m.group(1).strip())
    # `export const W = 1920, H = 1080;`
    for m in re.finditer(r'^export\s+(?:const|let|var)\s+\w+\s*=\s*[\d.]+\s*,\s*(\w+)\s*=\s*[\d.]+\s*;', src, re.M):
        names.append(m.group(1))
    src = re.sub(r'^export\s+', '', src, flags=re.M)
    return src, list(dict.fromkeys(names))


fx_src, fx_names = strip_exports((MV / 'js/fx.js').read_text(encoding='utf-8'))
for n in fx_names:
    if not re.search(r'^(?:async\s+)?(?:function\s+' + n + r'\b|(?:const|let|var)\s+(?:\w+\s*=\s*[\d.]+\s*,\s*)?' + n + r'\s*=)', fx_src, re.M):
        sys.exit('export name not declared at top level: ' + n)
# env.js: named imports from fx → destructure inside its IIFE
env_src = (MV / 'js/env.js').read_text(encoding='utf-8')
m = re.search(r"^import \{([^}]*)\} from './fx\.js';\n", env_src, re.M)
if not m:
    sys.exit('env.js import not found')
env_src = env_src.replace(m.group(0), 'const {' + m.group(1) + '} = fx;\n')
env_src, env_names = strip_exports(env_src)
cf_src = (MV / 'js/charfx.js').read_text(encoding='utf-8')
cf_src = sub(cf_src, "import * as fx from './fx.js';\n", '')
cf_src, cf_names = strip_exports(cf_src)
sc_src = (MV / 'js/scenes.js').read_text(encoding='utf-8')
sc_src = sub(sc_src, "import * as fx from './fx.js';\n", '')
sc_src = sub(sc_src, "import * as env from './env.js';\n", '')
sc_src = sub(sc_src, "import * as cf from './charfx.js';\n", '')
sc_src, sc_names = strip_exports(sc_src)
en_src = (MV / 'js/engine.js').read_text(encoding='utf-8')
en_src = sub(en_src, "import * as fx from './fx.js';\n", '')
en_src = sub(en_src, "import { SCENES, TRANSITIONS, prepareScenes, finishFrame, energyAt, frameState } from './scenes.js';\n", '')
en_src, _ = strip_exports(en_src)

# --- dist-only engine patches (player robustness inside a sandboxed iframe / on phones)
# SVG icons instead of ▶ ❚❚ glyphs (not in the embedded fonts, tofu on some phones)
en_src = sub(en_src, "    play.textContent = isPlaying() ? '❚❚' : '▶';",
             "    play.innerHTML = isPlaying() ? ICON_PAUSE : ICON_PLAY;")
en_src = sub(en_src, "function startPlayer() {\n", """const ICON_PLAY = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M4 2.5v11l9-5.5z" fill="currentColor"/></svg>';
const ICON_PAUSE = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z" fill="currentColor"/></svg>';
function startPlayer() {
""")
# fullscreen may be refused (sandbox / permissions policy): never throw, hide the button when unavailable
en_src = sub(en_src, """  const fullscreen = () => {
    const el = document.documentElement;
    if (!document.fullscreenElement) (el.requestFullscreen ? el.requestFullscreen() : Promise.resolve()).catch(() => {});
    else document.exitFullscreen();
  };""", """  const fullscreen = () => {
    try {
      const el = document.documentElement;
      const p = !document.fullscreenElement
        ? (el.requestFullscreen && el.requestFullscreen())
        : (document.exitFullscreen && document.exitFullscreen());
      if (p && typeof p.catch === 'function') p.catch(() => {});
    } catch (e) { /* fullscreen not allowed here */ }
  };
  if (!document.fullscreenEnabled) $('fs').hidden = true;""")
# audio: object URL first; if the media element rejects it, fall back to a FileReader data URL
en_src = sub(en_src, "  $('file').addEventListener('change', (e) => {", """  let curFile = null, dataTried = false;
  audio.addEventListener('error', () => {
    if (!curFile || dataTried) return;
    dataTried = true;
    const fr = new FileReader();
    fr.onload = () => { audio.src = fr.result; };
    fr.readAsDataURL(curFile);
  });
  $('file').addEventListener('change', (e) => {""")
en_src = sub(en_src, "    audio.src = URL.createObjectURL(f);", """    curFile = f; dataTried = false;
    try { audio.src = URL.createObjectURL(f); } catch (err) { dataTried = true; const fr = new FileReader(); fr.onload = () => { audio.src = fr.result; }; fr.readAsDataURL(f); }""")
# touch devices never send mousemove: wake the auto-hidden control bar on any pointer/touch
en_src = sub(en_src, "  window.addEventListener('mousemove', () => { lastMove = performance.now(); ui.classList.remove('idle'); });",
             """  const wake = () => { lastMove = performance.now(); ui.classList.remove('idle'); };
  window.addEventListener('mousemove', wake);
  window.addEventListener('pointerdown', wake, { passive: true });
  window.addEventListener('touchstart', wake, { passive: true });""")

bundle = (
    "// 機械の声 × Claude — fan MV player (single-file build of js/fx.js, env.js, charfx.js, scenes.js, engine.js)\n"
    "const fx = (() => {\n" + fx_src + "\nreturn { " + ', '.join(fx_names) + " };\n})();\n\n"
    "const env = (() => {\n" + env_src + "\nreturn { " + ', '.join(env_names) + " };\n})();\n\n"
    "const cf = (() => {\n" + cf_src + "\nreturn { " + ', '.join(cf_names) + " };\n})();\n\n"
    "const { " + ', '.join(sc_names) + " } = (() => {\n" + sc_src + "\nreturn { " + ', '.join(sc_names) + " };\n})();\n\n"
    + en_src
)
# encoding-proof inline JS: escape every non-ASCII char (string/template/regex literals and comments)
if any(ord(ch) > 0xFFFF for ch in bundle):
    sys.exit('astral character in bundle')
bundle = ''.join(ch if ord(ch) < 128 else '\\u%04x' % ord(ch) for ch in bundle)
for bad in ('\nimport ', '\nexport ', '</script', '<!--'):
    if bad in bundle:
        sys.exit(f'bundle still contains {bad!r}')

# ------------------------------------------------------------------ fonts
ui_strings = ('选择音频文件 无音频 · 静音时钟 播放 / 暂停 全屏 中 ON OFF 偏移 方向键 '
              '选择本地《機械の声》音频文件后播放；Z 切换中文字幕，[ / ] 微调偏移 Claude LOADING VOICEBANK…')
ui_font = SCR / 'subset' / 'MVUI-NotoSansSC.ttf'
ui_font.parent.mkdir(exist_ok=True)
opts = ftsubset.Options(); opts.layout_features = ['*']; opts.name_IDs = ['*']
f = TTFont(MV / 'fonts/NotoSansSC-Regular-SC.ttf')
cmap = f.getBestCmap()
ui_chars = sorted({c for c in ui_strings if ord(c) > 127 and ord(c) in cmap} | set(chr(i) for i in range(32, 127)))
s = ftsubset.Subsetter(opts); s.populate(text=''.join(ui_chars)); s.subset(f); f.save(ui_font)

def data_uri(p):
    return 'data:font/ttf;base64,' + base64.b64encode(Path(p).read_bytes()).decode('ascii')

css = (MV / 'css/style.css').read_text(encoding='utf-8')
used = re.findall(r'url\("\.\./fonts/([^"]+)"\)', css)
for name in used:
    src = SUBSET_FONTS / name
    if not src.exists():
        sys.exit('missing subset font ' + name)
    css = sub(css, f'url("../fonts/{name}")', f'url("{data_uri(src)}")')
css += '\n@font-face { font-family: "MV UI"; src: url("' + data_uri(ui_font) + '") format("truetype"); font-weight: 400; font-style: normal; font-display: swap; }\n'
css += """
/* ---------- dist overrides: dark page, responsive player, phone-friendly bar ---------- */
:root { color-scheme: dark; }
html, body { margin: 0; padding: 0; background: #0E1115; color: var(--paper); overflow: hidden; overscroll-behavior: none; }
body, .btn, #tc, #dur, #off, #hint { font-family: "Share Tech Mono", "MV UI", "Zen Kaku Gothic New", sans-serif; }
.file, #help { font-family: "MV UI", "Zen Kaku Gothic New", sans-serif; }
*, *::before, *::after { box-sizing: border-box; }
#stage { background: #0E1115; }
canvas#mv { width: min(100vw, calc(100vh * 16 / 9)); width: min(100vw, calc(100dvh * 16 / 9)); max-width: 100%; height: auto; }
#ui { padding: 14px max(16px, env(safe-area-inset-right)) max(12px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left)); }
#bar { flex-wrap: wrap; gap: 8px 12px; }
#seek { min-width: 0; }
.btn svg { display: block; }
#hint { line-height: 1.6; }
#help { color: var(--paper); opacity: .9; letter-spacing: .04em; }
#src { color: var(--gold); }
[hidden] { display: none !important; }
@media (max-width: 760px) {
  #ui { padding-top: 10px; }
  #bar { gap: 8px; justify-content: flex-start; }
  #seek { order: -1; flex: 1 1 100%; height: 3px; margin: 6px 0 4px; }
  #dur, .keys { display: none; }
  .btn { height: 34px; min-width: 38px; padding: 0 10px; }
  #tc { min-width: 0; font-size: 13px; }
  #off { min-width: 44px; }
  #hint { font-size: 11px; letter-spacing: .04em; }
}
"""
if 'url("../' in css or "url('../" in css:
    sys.exit('relative url left in css')

# ------------------------------------------------------------------ markup
index = (MV / 'index.html').read_text(encoding='utf-8')
stub = re.search(r'<script>\s*(// Contract stub.*?)</script>', index, re.S).group(1)

markup = """<div id="stage"><canvas id="mv" width="1920" height="1080"></canvas></div>
<div id="loading">LOADING VOICEBANK… <span>CLAUDE</span></div>
<div id="ui" hidden>
  <div id="bar">
    <label class="btn file" title="选择音频文件">选择音频文件<input type="file" id="file" accept="audio/*"></label>
    <button class="btn" id="play" title="播放 / 暂停 (Space)" aria-label="播放 / 暂停"></button>
    <span id="tc">00:00.00</span>
    <input type="range" id="seek" min="0" max="400" step="0.01" value="0" aria-label="seek">
    <span id="dur">06:40.00</span>
    <button class="btn" id="zh" title="中文字幕 (Z)">中</button>
    <span class="off"><button class="btn sm" id="offm" title="偏移 −0.1 s ([)" aria-label="偏移 −0.1 s">[</button><span id="off">+0.0s</span><button class="btn sm" id="offp" title="偏移 +0.1 s (])" aria-label="偏移 +0.1 s">]</button></span>
    <button class="btn" id="fs" title="全屏 (F)" aria-label="全屏"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M1.5 5.5v-4h4M10.5 1.5h4v4M14.5 10.5v4h-4M5.5 14.5h-4v-4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
  </div>
  <div id="hint"><span id="help">选择本地《機械の声》音频文件后播放；Z 切换中文字幕，[ / ] 微调偏移</span> · <span id="src">无音频 · 静音时钟</span><span class="keys"> · SPACE 播放/暂停 · F 全屏 · 方向键 ±5 s</span></div>
</div>
<audio id="audio" preload="auto"></audio>
"""

font_note = ('/* Embedded fonts (subsets), all SIL Open Font License 1.1: Zen Old Mincho, Shippori Mincho B1, Zen Kaku Gothic New,\n'
             '   DotGothic16, Share Tech Mono, Orbitron, Cormorant Garamond, Noto Sans SC. Licence texts: licenses/ */\n')
page = ("<title>機械の声 × Claude</title>\n"
        '<meta charset="utf-8">\n<link rel="icon" href="data:,">\n'
        "<style>\n" + font_note + css + "\n</style>\n"
        "<script>\n" + stub.strip() + "\n</script>\n"
        + markup +
        '<script type="module">\n' + bundle + "\n</script>\n")

# ------------------------------------------------------------------ write
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / 'assets').mkdir(parents=True)
(OUT / 'data').mkdir()
(OUT / 'index.html').write_text(page, encoding='utf-8')
names = re.search(r"const names = \[([^\]]+)\]", en_src).group(1)
for n in re.findall(r"'(\w+)'", names):
    shutil.copy2(MV / 'assets' / f'{n}.png', OUT / 'assets' / f'{n}.png')
shutil.copy2(MV / 'data/timeline.json', OUT / 'data/timeline.json')
(OUT / 'licenses').mkdir()
for lic in ('OFL-ZenOldMincho.txt', 'OFL-NotoSansSC.txt'):
    shutil.copy2(MV / 'fonts' / lic, OUT / 'licenses' / lic)
print('fx exports:', len(fx_names), '| scenes exports:', sc_names)
print('ui font glyphs:', len(ui_chars))
for p in sorted(OUT.rglob('*')):
    if p.is_file():
        print(f'{p.stat().st_size:>10}  {p.relative_to(OUT)}')
