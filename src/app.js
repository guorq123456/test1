// 游戏界面：合成台、手牌、图鉴。所有规则都在 rules.js 里，这里只负责显示和点击。

import { CATALOG_ALL as CATALOG, CHAPTERS_ALL as CHAPTERS, GIFTS, META, QUESTS_ALL as QUESTS, START } from './content.js';
import { combine, itemFromDesc, recipeText, resolveRef } from './rules.js';
import { toNum, isR } from './math.js';
import { BIN, TYPES, fmtV as fmtR, typeOf, typeLabel } from './values.js';
import { fmtU } from './unary.js';
import { groupInfo, previewDeck } from './decks.js';

const SAVE_KEY = 'suanzi-gongfang/v1';
const KIND = { card: '单卡', bin: '二元算子', un: '一元算子', meta: '构造算子', deck: '卡组' };
const TAB_OF = { card: 'card', bin: 'op', un: 'op', meta: 'op', deck: 'deck' };
const CH_NO = ['一', '二', '三', '四', '五', '六', '七', '八'];

const S = {};
const app = document.getElementById('app');
const sheetRoot = document.getElementById('sheet-root');

// ───────────────────────── 状态 ─────────────────────────

function freshState() {
  Object.assign(S, {
    items: new Map(),
    order: [],
    fresh: new Set(),
    recipes: {},
    hints: {},
    slots: { L: null, M: null, R: null },
    active: null,
    tab: 'card',
    last: null,
    sheet: null,
    busy: false,
    resetArmed: false,
  });
  for (const ref of START) addItem(resolveRef(ref), false);
}

// 收下一张卡。拿到某些卡会解锁新章节并附赠几张卡，赠卡的 id 放在 gifts 里返回。
function addItem(it, markFresh = true, gifts = []) {
  if (S.items.has(it.id)) return false;
  S.items.set(it.id, it);
  S.order.push(it.id);
  if (markFresh) S.fresh.add(it.id);
  for (const ref of GIFTS[it.id] ?? []) {
    const g = resolveRef(ref);
    if (addItem(g, markFresh, gifts)) gifts.push(g.id);
  }
  return true;
}

const has = id => S.items.has(id);
const itemOf = id => (id ? S.items.get(id) ?? null : null);
const chapterOpen = ch => !ch.unlock || has(ch.unlock.when);
const chapterOf = id => CHAPTERS.find(ch => ch.id === id);

function snapshot() {
  return {
    v: 1,
    items: S.order.map(id => S.items.get(id).desc),
    fresh: [...S.fresh],
    recipes: S.recipes,
    hints: S.hints,
    slots: S.slots,
    tab: S.tab,
  };
}

function save() {
  try {
    localStorage.setItem(SAVE_KEY, JSON.stringify(snapshot()));
  } catch {
    // 浏览器不让存也没关系，这一局照样能玩
  }
}

function readLocal() {
  try {
    const s = localStorage.getItem(SAVE_KEY);
    return s ? JSON.parse(s) : null;
  } catch {
    return null;
  }
}

function restore(data) {
  freshState();
  if (!data || data.v !== 1) return false;
  const memo = new Map();
  for (const d of data.items || []) {
    const it = itemFromDesc(d, memo);
    if (it) addItem(it, false);
  }
  for (const id of data.fresh || []) if (has(id)) S.fresh.add(id);
  S.recipes = data.recipes && typeof data.recipes === 'object' ? data.recipes : {};
  S.hints = data.hints && typeof data.hints === 'object' ? data.hints : {};
  for (const k of ['L', 'M', 'R']) {
    const id = data.slots?.[k];
    S.slots[k] = id && has(id) ? id : null;
  }
  if (['card', 'op', 'deck'].includes(data.tab)) S.tab = data.tab;
  return true;
}

// ───────────────────────── 操作 ─────────────────────────

function place(id) {
  const it = itemOf(id);
  if (!it) return;
  const sl = S.slots;
  let target = S.active;
  if (!target) {
    const mid = itemOf(sl.M);
    const isOp = it.kind === 'bin' || it.kind === 'un' || it.kind === 'meta';
    if (it.kind === 'meta') {
      // 构造算子占中间，原来的算子挪到旁边当输入
      if (mid && mid.kind !== 'meta') {
        if (!sl.L) sl.L = sl.M;
        else if (!sl.R) sl.R = sl.M;
      }
      target = 'M';
    } else if (isOp && (!mid || mid.kind !== 'meta')) {
      target = 'M';
    } else {
      target = !sl.L ? 'L' : 'R';
    }
  }
  sl[target] = id;
  S.active = null;
  S.fresh.delete(id);
  save();
  render();
}

function tapSlot(k) {
  if (S.slots[k]) {
    S.slots[k] = null;
    S.active = k;
  } else {
    S.active = S.active === k ? null : k;
  }
  save();
  render();
}

function doCombine() {
  if (S.busy) return;
  S.busy = true;
  render();
  // 让"计算中"先显示出来，再做可能要算一会儿的合成
  setTimeout(() => {
    const res = combine(itemOf(S.slots.L), itemOf(S.slots.M), itemOf(S.slots.R));
    S.busy = false;
    if (!res.ok) {
      S.last = { ok: false, msg: res.msg };
      render();
      return;
    }
    const gifts = [];
    const isNew = addItem(res.item, true, gifts);
    let recipeNew = false;
    if (res.item.kind === 'deck' && res.recipe) {
      const list = (S.recipes[res.item.id] ||= []);
      if (!list.includes(res.recipe)) {
        list.push(res.recipe);
        recipeNew = !isNew;
      }
    }
    const unlocked = isNew ? CHAPTERS.find(ch => ch.unlock?.when === res.item.id) : null;
    S.last = { ok: true, text: res.text, id: res.item.id, isNew, recipeNew, gifts, unlocked: unlocked?.id ?? null };
    if (isNew) S.tab = TAB_OF[res.item.kind];
    save();
    render();
  }, 30);
}

function switchTab(tab) {
  // 离开一个标签时，把里面的"新"标记清掉
  for (const id of [...S.fresh]) if (TAB_OF[itemOf(id)?.kind] === S.tab) S.fresh.delete(id);
  S.tab = tab;
  save();
  render();
}

function openSheet(sheet) {
  S.sheet = sheet;
  S.resetArmed = false;
  if (sheet.type === 'item') S.fresh.delete(sheet.id);
  render();
  sheetRoot.querySelector('.sheet-panel')?.focus();
}

function closeSheet() {
  S.sheet = null;
  S.resetArmed = false;
  save();
  render();
}

// ───────────────────────── 显示 ─────────────────────────

const esc = s =>
  String(s).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]);
// 数学文字：变量 x 用斜体，换行（矩阵）变成 <br>
const math = s => esc(s).replace(/x/g, '<i>x</i>').replace(/\n/g, '<br>');
const decimal = x => String(+toNum(x).toFixed(3)).replace('-', '−');
const structText = c => (c.struct === '群' ? `群（${c.groupOp}）` : '集合');
const OP_SYM = { add: '+', mul: '×' };

// 自造的有限卡组：自动判断它对 + 和 × 是不是群
function groupText(D) {
  const g = groupInfo(D);
  if (!g) return '';
  const parts = [];
  for (const [op, r] of Object.entries(g)) {
    const sym = OP_SYM[op];
    if (r.group) parts.push(`对 ${sym} 是群`);
    else if (!r.closed) parts.push(`对 ${sym} 不封闭`);
    else if (!r.identity) parts.push(`对 ${sym} 封闭，但没有单位元`);
    else parts.push(`对 ${sym} 封闭，有单位元 ${fmtR(r.identity)}，但不是每张卡都有逆元`);
  }
  return parts.join('；') + '。';
}

function mainText(it) {
  switch (it.kind) {
    case 'card':
      return fmtR(it.v);
    case 'un':
      return fmtU(it.v);
    case 'deck':
      return it.v.name;
    default:
      return it.v.sym;
  }
}

function subText(it) {
  switch (it.kind) {
    case 'card':
      if (!isR(it.v)) return typeLabel(it.v);
      return it.v.d === 1 ? '' : `≈ ${decimal(it.v)}`;
    case 'bin':
    case 'meta':
      return it.v.name;
    case 'un':
      return it.name ?? '';
    case 'deck':
      if (it.cat) return it.cat.short !== it.cat.name ? it.cat.name : structText(it.cat);
      return it.v.approx ? '自造 · 近似' : '自造卡组';
  }
  return '';
}

function cardHTML(it, { act = 'place', slot = '', still = false } = {}) {
  const main = mainText(it);
  const lines = main.split('\n');
  const len = Math.max(...lines.map(l => [...l].length)) + (lines.length > 1 ? 3 : 0);
  const size = len <= 3 ? 'l' : len <= 6 ? 'm' : len <= 11 ? 's' : 'xs';
  const inner = `
    <span class="card-type">${KIND[it.kind]}</span>
    <span class="card-main sz-${size}">${math(main)}</span>
    <span class="card-sub">${math(subText(it))}</span>
    ${!still && !slot && S.fresh.has(it.id) ? '<span class="card-new">新</span>' : ''}`;
  if (still) return `<div class="card k-${it.kind}">${inner}</div>`;
  const aria = slot ? `移除${KIND[it.kind]} ${main}` : `${KIND[it.kind]} ${main}`;
  return `<button type="button" class="card k-${it.kind}" data-act="${act}" data-id="${esc(it.id)}"${
    slot ? ` data-slot="${slot}"` : ''
  } aria-label="${esc(aria)}">${inner}</button>`;
}

function gridHTML(items) {
  return `<div class="grid">${items
    .map(
      it => `<div class="cell">${cardHTML(it)}<button type="button" class="info" data-act="info" data-id="${esc(
        it.id,
      )}" aria-label="查看 ${esc(mainText(it))} 的详情"><span>i</span></button></div>`,
    )
    .join('')}</div>`;
}

function questHTML() {
  // 只显示已解锁章节的任务
  const open = QUESTS.filter(q => !q.ch || chapterOpen(chapterOf(q.ch)));
  const idx = open.findIndex(q => !q.done(has));
  if (idx < 0) {
    const locked = CHAPTERS.filter(ch => !chapterOpen(ch));
    const next = locked.length
      ? `还有 ${locked.length} 章没有解锁：${locked.map(ch => `「${ch.title}」要先拿到 ${label(resolveRef(ch.unlock.when))}`).join('，')}。`
      : '所有章节都通关了。试着给每个卡组多找几种做法，或者造一些图鉴里没有的卡组。';
    return `<section class="quest"><span class="quest-step">当前任务全部完成</span><p>${math(next)}</p></section>`;
  }
  const q = open[idx];
  const ch = q.ch ? chapterOf(q.ch) : null;
  const where = ch ? `第${CH_NO[ch.id - 1]}章` : '入门';
  return `<section class="quest" aria-label="当前任务"><span class="quest-step">${where} · 任务 ${idx + 1}/${open.length} · ${esc(
    q.title,
  )}</span><p>${math(q.text)}</p></section>`;
}

function slotHTML(k) {
  const label = { L: '左', M: '算子', R: '右' }[k];
  const it = itemOf(S.slots[k]);
  const active = S.active === k;
  const empty = active ? '下一张放这里' : k === 'M' ? '放一个算子' : '空位';
  return `<div class="slot${active ? ' is-active' : ''}"><span class="slot-label">${label}</span>${
    it
      ? cardHTML(it, { act: 'slot', slot: k })
      : `<button type="button" class="slot-empty" data-act="slot" data-slot="${k}">${empty}</button>`
  }</div>`;
}

function benchHTML() {
  return `<section class="bench" aria-label="合成台">
    <div class="bench-title"><h2>合成台</h2><span>点卡放上来，点格子里的卡移除</span></div>
    <div class="slots">${slotHTML('L')}${slotHTML('M')}${slotHTML('R')}</div>
    <div class="bench-actions">
      <button type="button" class="btn btn-primary" data-act="combine"${S.busy ? ' disabled' : ''}>${
        S.busy ? '计算中…' : '合成'
      }</button>
      <button type="button" class="btn" data-act="swap">左右互换</button>
      <button type="button" class="btn" data-act="clear">清空</button>
    </div>
  </section>`;
}

function resultHTML() {
  const L = S.last;
  if (!L) {
    return `<p class="result-idle">左右两格放单卡或卡组，中间放算子。左右格空着时，那个位置就代表变量 <i>x</i>。</p>`;
  }
  if (!L.ok) {
    return `<div class="result is-fail" role="status"><strong>合不成</strong><p>${math(L.msg)}</p></div>`;
  }
  const it = itemOf(L.id);
  const tag = L.isNew ? (it.kind === 'deck' ? '新卡组' : `新${KIND[it.kind]}`) : L.recipeNew ? '新做法' : '已经有了';
  let unlock = '';
  if (L.unlocked) {
    const ch = chapterOf(L.unlocked);
    const names = (L.gifts ?? []).map(id => itemOf(id)).filter(Boolean).map(label);
    unlock = `<p class="unlock"><strong>解锁第${CH_NO[ch.id - 1]}章「${esc(ch.title)}」</strong>${
      names.length ? `，获得新卡：${math(names.join('、'))}` : ''
    }。${esc(ch.unlock.note ?? '')}</p>`;
  }
  return `<div class="result${L.isNew ? ' is-new' : ''}" role="status">
    <div class="result-card">${cardHTML(it, { act: 'info' })}</div>
    <div class="result-body">
      <span class="tag${L.isNew || L.recipeNew ? ' tag-new' : ''}">${tag}</span>
      <p>${math(L.text)}</p>${unlock}
      <div class="result-actions">
        <button type="button" class="btn" data-act="reuse">放到左边继续</button>
        <button type="button" class="btn" data-act="info" data-id="${esc(it.id)}">详情</button>
      </div>
    </div>
  </div>`;
}

// 单卡按类型分组：数在最前，其他类型按注册顺序
function cardGroups(cards) {
  const byType = new Map();
  for (const it of cards) {
    const t = typeOf(it.v);
    if (!byType.has(t)) byType.set(t, []);
    byType.get(t).push(it);
  }
  const out = [];
  for (const [t, def] of TYPES) {
    const xs = byType.get(t);
    if (!xs) continue;
    if (t === 'q') xs.sort((a, b) => toNum(a.v) - toNum(b.v));
    else xs.sort((a, b) => (a.id < b.id ? -1 : 1));
    out.push([def.name, xs]);
  }
  return out;
}

function handGroups() {
  const all = S.order.map(itemOf);
  return {
    cards: all.filter(i => i.kind === 'card'),
    bins: Object.keys(BIN).map(k => itemOf(`b:${k}`)).filter(Boolean),
    uns: all.filter(i => i.kind === 'un'),
    metas: META.map(m => itemOf(`m:${m.id}`)).filter(Boolean),
    decks: [...CATALOG.map(c => itemOf(`d:${c.id}`)).filter(Boolean), ...all.filter(i => i.kind === 'deck' && !i.cat)],
  };
}

function handHTML() {
  const g = handGroups();
  const counts = { card: g.cards.length, op: g.bins.length + g.uns.length + g.metas.length, deck: g.decks.length };
  const freshIn = tab => [...S.fresh].some(id => TAB_OF[itemOf(id)?.kind] === tab);
  const tabs = [
    ['card', '单卡'],
    ['op', '算子'],
    ['deck', '卡组'],
  ]
    .map(
      ([k, t]) =>
        `<button type="button" role="tab" class="tab" aria-selected="${S.tab === k}" data-act="tab" data-tab="${k}">${t} <span class="tab-n">${
          counts[k]
        }</span>${freshIn(k) && S.tab !== k ? '<span class="dot"></span>' : ''}</button>`,
    )
    .join('');
  let body;
  if (S.tab === 'card') {
    const groups = cardGroups(g.cards);
    body =
      groups.length <= 1
        ? gridHTML(g.cards)
        : groups.map(([title, xs]) => `<div class="group"><h3 class="group-title">${esc(title)}</h3>${gridHTML(xs)}</div>`).join('');
  } else if (S.tab === 'deck') {
    body = g.decks.length
      ? gridHTML(g.decks)
      : '<p class="muted small">还没有卡组。跟着上面的任务，从 0 出发造出第一个卡组。</p>';
  } else {
    body = [
      ['二元算子', g.bins, '两个输入的运算。只在一边放数，就变成一元算子。'],
      ['一元算子', g.uns, '一个输入的变换：作用在单卡上得到单卡，作用在卡组上得到卡组。'],
      ['构造算子', g.metas, '改造算子、生成卡组的高阶算子。'],
    ]
      .map(
        ([title, xs, desc]) =>
          `<div class="group"><h3 class="group-title">${title}</h3><p class="muted small">${desc}</p>${
            xs.length ? gridHTML(xs) : ''
          }</div>`,
      )
      .join('');
  }
  return `<section class="hand" aria-label="手牌"><div class="hand-tabs" role="tablist">${tabs}</div>${body}</section>`;
}

const refCache = new Map();
function refTexts(c) {
  if (!refCache.has(c.id)) refCache.set(c.id, c.recipes.map(recipeText));
  return refCache.get(c.id);
}

function sheetFrame(inner, back = null) {
  return `<div class="sheet" data-act="close-bg"><div class="sheet-panel" role="dialog" aria-modal="true" aria-labelledby="sheet-title" tabindex="-1">
    <div class="sheet-bar">${
      back ? `<button type="button" class="btn" data-act="codex">← 图鉴</button>` : '<span></span>'
    }<button type="button" class="btn" data-act="close">关闭</button></div>
    ${inner}
  </div></div>`;
}

function refListHTML(c) {
  const n = S.hints[c.id] || 0;
  const refs = refTexts(c);
  const found = S.recipes[`d:${c.id}`] || [];
  const shown = refs.slice(0, n);
  const list = shown.length
    ? `<h3 class="sub-title">参考做法</h3><ul class="recipes">${shown
        .map(r => `<li>${math(r)}${found.includes(r) ? ' <span class="badge">已用过</span>' : ''}</li>`)
        .join('')}</ul>`
    : '';
  const more =
    n < refs.length
      ? `<div><button type="button" class="btn" data-act="more-hint" data-cat="${c.id}">${
          n ? '再看一种做法' : '看一种参考做法'
        }</button></div>`
      : '';
  return list + more;
}

function deckDetailHTML(it) {
  const c = it.cat;
  const found = S.recipes[it.id] || [];
  let html = `<p class="preview">${math(c ? c.preview : previewDeck(it.v))}</p>`;
  if (c) {
    html += `<p>${esc(c.desc)}</p><p><span class="badge${c.struct === '群' ? ' badge-group' : ''}">${structText(
      c,
    )}</span>${esc(c.note)}</p>`;
  } else {
    html += `<p class="muted">图鉴里没有这个卡组，是你自己造出来的。${
      it.v.approx ? '它的内容是在一个小范围里算出来的，是近似结果。' : ''
    }</p>`;
    const gt = groupText(it.v);
    if (gt) html += `<p>${math(gt)}</p>`;
  }
  html += `<h3 class="sub-title">你找到的做法</h3>${
    found.length
      ? `<ul class="recipes">${found.map(r => `<li>${math(r)}</li>`).join('')}</ul>`
      : '<p class="muted small">还没有记录。</p>'
  }`;
  if (c) html += refListHTML(c);
  return html;
}

function itemSheetHTML(it, back) {
  let rows = '';
  switch (it.kind) {
    case 'card': {
      const what = !isR(it.v) ? `${typeLabel(it.v)}。` : it.v.d === 1 ? '一个整数。' : `一个分数，约等于 ${decimal(it.v)}。`;
      const asFn = TYPES.get(typeOf(it.v))?.call ? '它也可以放在中间当算子用：旁边放单卡就代入，放卡组就对每张卡都代入。' : '';
      rows = `<p>${esc(what)}</p>
        <p class="muted">单卡放在合成台左右两边，和中间的算子一起算出新卡。${asFn}</p>`;
      break;
    }
    case 'bin':
      rows = `<p>${esc(it.info?.desc ?? '')}</p>
        <p class="muted">两边放单卡，算出新单卡；只放一边，得到一元算子；卡组配单卡，卡组里每张卡都做这个运算；两个卡组，两两运算收集结果。</p>`;
      break;
    case 'meta':
      rows = `<p>${esc(it.v.desc)}</p><p class="muted">用法：${math(it.v.usage)}</p>`;
      break;
    case 'un':
      rows = `<p class="formula">${math(`f(x) = ${fmtU(it.v)}`)}</p>
        <p class="muted">放在中间：旁边放单卡就代入计算，放卡组就对里面每一张卡都做一遍。配合「延展」可以从一张单卡长出一个卡组。</p>`;
      break;
    case 'deck':
      rows = deckDetailHTML(it);
      break;
  }
  const title = it.kind === 'deck' && it.cat ? it.cat.name : it.kind === 'un' && it.name ? it.name : mainText(it);
  return sheetFrame(
    `<div class="detail"><div>${cardHTML(it, { still: true })}</div><div><p class="eyebrow">${
      KIND[it.kind]
    }</p><h2 id="sheet-title">${math(title)}</h2></div></div>
    ${rows}
    <div class="sheet-actions"><button type="button" class="btn btn-primary" data-act="place-close" data-id="${esc(
      it.id,
    )}">放上合成台</button></div>`,
    back,
  );
}

function hintSheetHTML(c) {
  return sheetFrame(
    `<p class="eyebrow">未发现的卡组 · 第${CH_NO[c.ch - 1]}章</p>
    <h2 id="sheet-title">${esc(c.name)}</h2>
    <p>${esc(c.hint)}</p>
    ${refListHTML(c)}
    <p class="muted small">做法里用到的卡，要先自己造出来。</p>`,
    'codex',
  );
}

function tileHTML(c) {
  const id = `d:${c.id}`;
  if (has(id)) {
    const n = (S.recipes[id] || []).length;
    return `<button type="button" class="tile is-got" data-act="info" data-id="${id}" data-back="codex">
      <span class="tile-sym">${math(c.short)}</span>
      <span class="tile-name">${esc(c.name)}</span>
      <span class="tile-prev">${math(c.preview)}</span>
      <span class="tile-meta">${structText(c)} · 找到 ${n} 种做法</span>
    </button>`;
  }
  return `<button type="button" class="tile" data-act="hint" data-cat="${c.id}">
    <span class="tile-sym">?</span>
    <span class="tile-name">${esc(c.name)}</span>
    <span class="tile-prev">${esc(c.hint)}</span>
    <span class="tile-meta">未发现</span>
  </button>`;
}

function chapterHTML(ch) {
  const decks = CATALOG.filter(c => c.ch === ch.id);
  const head = `<h3><span class="ch-no">第${CH_NO[ch.id - 1]}章</span>${esc(ch.title)}</h3>`;
  if (!chapterOpen(ch)) {
    const key = resolveRef(ch.unlock.when);
    return `<section class="chapter is-locked">${head}
      <p class="muted small">${esc(ch.desc)}</p>
      <p class="locked-note">🔒 拿到 ${math(label(key))} 后解锁，共 ${decks.length} 个卡组。</p>
    </section>`;
  }
  const got = decks.filter(c => has(`d:${c.id}`)).length;
  return `<section class="chapter">${head}
    <p class="muted small">${esc(ch.desc)} <span class="ch-count">${got}/${decks.length}</span></p>
    ${ch.intro ? `<p class="intro">${esc(ch.intro)}</p>` : ''}
    <div class="codex-grid">${decks.map(tileHTML).join('')}</div>
  </section>`;
}

function codexHTML() {
  const got = CATALOG.filter(c => has(`d:${c.id}`)).length;
  const chapters = CHAPTERS.map(chapterHTML).join('');
  const reset = S.resetArmed
    ? `<span>清空所有卡牌和记录，从头开始？</span><button type="button" class="btn btn-danger" data-act="reset-confirm">确认重置</button><button type="button" class="btn" data-act="reset-cancel">取消</button>`
    : `<button type="button" class="btn btn-quiet" data-act="reset">重置进度</button>`;
  return sheetFrame(`<p class="eyebrow">从数数到丈量世界</p>
    <h2 id="sheet-title">图鉴 <span class="muted">${got}/${CATALOG.length}</span></h2>
    <p class="muted small">每个卡组都至少有两种做法，而且都能用别的卡组组合出来。点开没发现的卡组看提示。拿到关键的卡会解锁新章节。</p>
    ${chapters}
    <div class="reset">${reset}</div>`);
}

function render() {
  const got = CATALOG.filter(c => has(`d:${c.id}`)).length;
  app.innerHTML = `
    <header class="top">
      <div class="brand"><h1>算子工坊</h1><span class="edition">从数数到丈量世界 · DEMO</span></div>
      <button type="button" class="codex-btn" data-act="codex">图鉴 <span class="count">${got}/${CATALOG.length}</span></button>
    </header>
    ${questHTML()}
    ${benchHTML()}
    <section aria-live="polite">${resultHTML()}</section>
    ${handHTML()}`;

  const oldPanel = sheetRoot.querySelector('.sheet-panel');
  const keepScroll = oldPanel && S.sheet && oldPanel.dataset.key === sheetKey() ? oldPanel.scrollTop : 0;
  if (!S.sheet) sheetRoot.innerHTML = '';
  else {
    const s = S.sheet;
    sheetRoot.innerHTML =
      s.type === 'codex'
        ? codexHTML()
        : s.type === 'hint'
          ? hintSheetHTML(CATALOG.find(c => c.id === s.cat))
          : itemSheetHTML(itemOf(s.id), s.back);
    const panel = sheetRoot.querySelector('.sheet-panel');
    panel.dataset.key = sheetKey();
    panel.scrollTop = keepScroll;
  }
  document.body.classList.toggle('has-sheet', !!S.sheet);
}

const sheetKey = () => (S.sheet ? `${S.sheet.type}:${S.sheet.id ?? S.sheet.cat ?? ''}` : '');

// ───────────────────────── 点击 ─────────────────────────

document.addEventListener('click', e => {
  const el = e.target.closest('[data-act]');
  if (!el) return;
  const act = el.dataset.act;
  if (act === 'close-bg' && e.target !== el) return;
  switch (act) {
    case 'place':
      place(el.dataset.id);
      break;
    case 'slot':
      tapSlot(el.dataset.slot);
      break;
    case 'combine':
      doCombine();
      break;
    case 'swap':
      [S.slots.L, S.slots.R] = [S.slots.R, S.slots.L];
      save();
      render();
      break;
    case 'clear':
      S.slots = { L: null, M: null, R: null };
      S.active = null;
      save();
      render();
      break;
    case 'reuse':
      if (S.last?.id) {
        S.slots = { L: S.last.id, M: null, R: null };
        S.active = null;
        save();
        render();
      }
      break;
    case 'tab':
      switchTab(el.dataset.tab);
      break;
    case 'info':
      if (itemOf(el.dataset.id)) openSheet({ type: 'item', id: el.dataset.id, back: el.dataset.back ?? null });
      break;
    case 'codex':
      openSheet({ type: 'codex' });
      break;
    case 'hint':
      openSheet({ type: 'hint', cat: el.dataset.cat });
      break;
    case 'more-hint': {
      const id = el.dataset.cat;
      S.hints[id] = (S.hints[id] || 0) + 1;
      save();
      render();
      break;
    }
    case 'place-close': {
      const id = el.dataset.id;
      S.sheet = null;
      place(id);
      break;
    }
    case 'close':
    case 'close-bg':
      closeSheet();
      break;
    case 'reset':
      S.resetArmed = true;
      render();
      break;
    case 'reset-cancel':
      S.resetArmed = false;
      render();
      break;
    case 'reset-confirm':
      try {
        localStorage.removeItem(SAVE_KEY);
      } catch {
        // 忽略
      }
      freshState();
      S.slots = { L: 'c:1', M: 'b:add', R: 'c:1' };
      save();
      render();
      break;
  }
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && S.sheet) closeSheet();
});

// ───────────────────────── 启动 ─────────────────────────

function start(data) {
  const saved = data?.save ?? readLocal();
  if (!restore(saved)) {
    // 第一次玩：合成台上先摆好 1 + 1
    S.slots = { L: 'c:1', M: 'b:add', R: 'c:1' };
  }
  render();
}

window.claude?.hot?.snapshot?.(() => ({ save: snapshot() }));
if (window.claude?.hot?.ready) window.claude.hot.ready(start);
else start(window.claude?.hot?.data ?? {});
