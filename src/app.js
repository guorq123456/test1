// 游戏界面：合成台、手牌、图鉴。所有规则都在 rules.js 里，这里只负责显示和点击。

import { CATALOG_ALL as CATALOG, CHAPTERS_ALL as CHAPTERS, GIFTS, META, QUESTS_ALL as QUESTS, START } from './content.js';
import { combine, itemFromDesc, label, recipeText, resolveRef } from './rules.js';
import { toNum, isR } from './math.js';
import { BIN, TYPES, cmpV, fmtV as fmtR, typeOf, typeLabel } from './values.js';
import { fmtU } from './unary.js';
import { groupInfo, previewDeck } from './decks.js';

const SAVE_KEY = 'suanzi-gongfang/v1';
const KIND = { card: '单卡', bin: '二元算子', un: '一元算子', meta: '构造算子', deck: '卡组', hole: '缺口' };
const TAB_OF = { card: 'card', bin: 'op', un: 'op', meta: 'op', deck: 'deck', hole: 'hole' };
const TABS = ['card', 'op', 'deck', 'hole'];
const SLOT_KEYS = ['W', 'L', 'M', 'R'];
const emptySlots = () => ({ W: null, L: null, M: null, R: null });
const CH_NO = ['一', '二', '三', '四', '五', '六', '七', '八'];
// 缺口卡角上的状态
// retyped：结果换了一种东西（ℤ 里做 mod 12 得到时钟），不是这个世界缺的部分，不能填
const HOLE_FLAG = { fillable: '可填', frontier: '前沿', unfillable: '补不上', filled: '已填', retyped: '换了类型' };
// 数太大的缺口也不查找目标（状态 unfillable），但它不是"补不上"，是游戏的边界
const holeFlag = (h, st) => (st === 'unfillable' && h.v.tooLarge ? '边界' : HOLE_FLAG[st]);
// 填的结果：徽章文字
// tighter：候选合规，但比图鉴目标还小或者和它不可比，和「首次发现」一样算发明（res.firstFill）
const GRADE = { auto: '自动填', exact: '恰到好处', over: '多了一块', tighter: '比图鉴更紧', frontier: '首次发现 · 发明者' };

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
    // W 是底板「在……里」，只放卡组
    slots: emptySlots(),
    // 填过的缺口 id（任务用它的长度）；fillWith：缺口 id → 填成的卡组 id；inventor：首次发现的卡组 id
    filled: [],
    fillWith: {},
    inventor: [],
    active: null,
    // 一行临时提示（比如缺口放不进底板），下一次点击就消失，不存档
    tip: null,
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
// 能放在中间当算子用的单卡（多项式）
const isCallable = it => it?.kind === 'card' && !!TYPES.get(typeOf(it.v))?.call;
const holeCount = () => S.order.reduce((n, id) => n + (S.items.get(id).kind === 'hole' ? 1 : 0), 0);

// 缺口现在的状态：只有本局真的填过（记在 S.filled 里）才算"已填"。
// 手里已经有目标世界不算：那张缺口还是"可填"，按「填」也算完成（旧存档迁移上来的玩家靠这个过任务）
function holeState(h) {
  const target = h.v.targetId ? `d:${h.v.targetId}` : null;
  if (S.filled.includes(h.id)) return { status: 'filled', withId: S.fillWith[h.id] ?? target };
  return { status: h.v.status, withId: null };
}

function snapshot() {
  return {
    v: 1,
    items: S.order.map(id => S.items.get(id).desc),
    fresh: [...S.fresh],
    recipes: S.recipes,
    hints: S.hints,
    slots: S.slots,
    filled: S.filled,
    fillWith: S.fillWith,
    inventor: S.inventor,
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
  const saved = new Set();
  for (const d of data.items || []) {
    // 缺口卡的 desc 要重放一次合成；万一重放出错，跳过这一张，别让整个存档读不出来
    let it = null;
    try {
      it = itemFromDesc(d, memo);
    } catch (e) {
      console.warn('读档时有一张卡重建失败', d, e);
    }
    if (!it) continue;
    saved.add(it.id);
    addItem(it, false);
  }
  for (const id of data.fresh || []) if (has(id)) S.fresh.add(id);
  // 旧存档里没有的开局卡（后来才加进开局手牌的构造算子，比如「反推」「填」）标成新卡
  for (const ref of START) {
    const id = resolveRef(ref).id;
    if (!saved.has(id)) S.fresh.add(id);
  }
  const obj = x => (x && typeof x === 'object' && !Array.isArray(x) ? x : {});
  const ids = x => (Array.isArray(x) ? x.filter(s => typeof s === 'string') : []);
  S.recipes = obj(data.recipes);
  S.hints = obj(data.hints);
  // 旧存档没有底板 W、没有填过的记录：补默认值
  for (const k of SLOT_KEYS) {
    const id = data.slots?.[k];
    S.slots[k] = id && has(id) && (k !== 'W' || itemOf(id).kind === 'deck') ? id : null;
  }
  S.filled = ids(data.filled);
  S.fillWith = obj(data.fillWith);
  S.inventor = ids(data.inventor);
  if (TABS.includes(data.tab)) S.tab = data.tab;
  return true;
}

// ───────────────────────── 操作 ─────────────────────────

function place(id) {
  const it = itemOf(id);
  if (!it) return;
  const sl = S.slots;
  let target = S.active;
  // 底板只收卡组。缺口卡最像卡组、最容易放错：不落位，底板保持选中，提示一句
  if (target === 'W' && it.kind === 'hole') {
    S.tip = '缺口不能当底板，请选一个卡组';
    render();
    return;
  }
  // 选中底板时点了单卡或算子，就照平常的规则落位
  if (target === 'W' && it.kind !== 'deck') target = null;
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

// parts：[L, M, R, W] 四张卡；不给就用合成台上的。缺口详情里的「填」直接给 [缺口, 填, 空, 空]，不动合成台。
function doCombine(parts = null) {
  if (S.busy) return;
  S.busy = true;
  render();
  // 让"计算中"先显示出来，再做可能要算一会儿的合成
  setTimeout(() => {
    const [L, M, R, W] = parts ?? ['L', 'M', 'R', 'W'].map(k => itemOf(S.slots[k]));
    let res;
    try {
      res = combine(L, M, R, W);
    } catch (e) {
      console.error(e);
      res = { ok: false, msg: '这一步算的时候出了错，换一种放法试试。' };
    }
    S.busy = false;
    if (!res.ok) {
      S.last = { ok: false, msg: res.msg };
      render();
      return;
    }
    takeResult(res);
    // 合成成功后清空合成台（连同底板），下一步从空台开始；想接着用结果，按「放到左边继续」
    if (!parts) {
      S.slots = emptySlots();
      S.active = null;
    }
    save();
    render();
  }, 30);
}

// 收下合成的结果：得到的卡（可能没有）、缺口卡（零到多张）、填的记录
function takeResult(res) {
  const it = res.item ?? null;
  const gifts = [];
  const isNew = it ? addItem(it, true, gifts) : false;
  let recipeNew = false;
  if (it?.kind === 'deck' && res.recipe) {
    const list = (S.recipes[it.id] ||= []);
    if (!list.includes(res.recipe)) {
      list.push(res.recipe);
      recipeNew = !isNew;
    }
  }
  const holes = (res.holes ?? []).map(h => ({ id: h.id, isNew: addItem(h, true) }));
  if (res.filled) {
    if (!S.filled.includes(res.filled)) S.filled.push(res.filled);
    if (it) S.fillWith[res.filled] = it.id;
  }
  // 发明者只给自造的世界：图鉴里本来就有的世界不算"以前没人填过"
  if (res.firstFill && it && !it.cat && !S.inventor.includes(it.id)) S.inventor.push(it.id);
  // 一张卡可能同时解锁好几章（ℚ 解锁第六、七章），每一章都要报出来
  const got = new Set([it?.id, ...gifts].filter(Boolean));
  const unlocked = isNew ? CHAPTERS.filter(ch => ch.unlock && got.has(ch.unlock.when)).map(ch => ch.id) : [];
  S.last = { ok: true, text: res.text, id: it?.id ?? null, isNew, recipeNew, gifts, unlocked, holes, grade: res.grade ?? null };
  if (isNew) S.tab = TAB_OF[it.kind];
  else if (holes.some(h => h.isNew)) S.tab = 'hole';
}

// 缺口详情里的「填」：等于在合成台上放 [缺口] [填] [空]
function autoFill(holeId) {
  const H = itemOf(holeId);
  const F = itemOf('m:fill');
  if (!H || !F) return;
  S.sheet = null;
  S.fresh.delete(holeId);
  doCombine([H, F, null, null]);
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
// 数学文字：变量 x 用斜体，换行（矩阵）变成 <br>。
// 只认单独的 x（前后不是拉丁字母），缺口名字、说明里夹着的英文词不会被拆开；
// 先转义再替换，转义出来的实体里没有 x。结果是 HTML，不要再套一次 math。
const math = s => esc(s).replace(/(?<![A-Za-z])x(?![A-Za-z])/g, '<i>x</i>').replace(/\n/g, '<br>');
// 卡面上的矩阵 [a b; c d] 只在分号处换行（一行一行断开），不从一行中间断开
const keepRows = s => s.replace(/\[[^[\]]*;[^[\]]*\]/g, m => m.replace(/(?<!;) /g, '\u00a0'));
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
      // 没起名字的卡组（拿缺口当候选手填出来的）用它的内容当名字，别让页面渲染时崩掉
      return it.v.name ?? previewDeck(it.v);
    case 'hole':
      return holeName(it);
    default:
      return it.v.sym;
  }
}

// 缺口卡的名字：缺的那部分被认成图鉴卡组时用它的名字，否则列出前几张
const holeName = h => h.v.name ?? previewDeck(h.v.where, 3);
const catShort = id => {
  const c = CATALOG.find(x => x.id === id);
  return c ? (c.short !== c.name ? `${c.short}（${c.name}）` : c.name) : id;
};
const catSym = id => CATALOG.find(x => x.id === id)?.short ?? id;
const nameOfId = id => {
  const it = itemOf(id);
  if (it?.cat) return catShort(it.cat.id);
  if (it) return label(it);
  return id?.startsWith('d:') ? catShort(id.slice(2)) : '';
};

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
      if (S.inventor.includes(it.id)) return '自造 · 发明者';
      return it.v.approx ? '自造 · 近似' : '自造卡组';
    case 'hole':
      return it.v.kindText ?? '';
  }
  return '';
}

function cardHTML(it, { act = 'place', slot = '', still = false } = {}) {
  const main = mainText(it);
  const lines = main.split('\n');
  // 按视觉宽度选字号：一个汉字约等于两个数字的宽度
  const width = l => [...l].reduce((n, ch) => n + (/[　-鿿＀-￯]/.test(ch) ? 2.2 : 1), 0);
  const len = Math.max(...lines.map(width)) + (lines.length > 1 ? 3 : 0);
  const size = len <= 3 ? 'l' : len <= 6 ? 'm' : len <= 11 ? 's' : 'xs';
  // card-main 是 flex 容器：公式包在一层 span 里，<i>x</i> 和旁边的文字才会连成一行，空格也不会丢
  // "新"标记放进小字那一行，不盖住小字
  const fresh = !still && !slot && S.fresh.has(it.id) ? '<span class="card-new">新</span>' : '';
  // 缺口卡角上标出状态：可填 / 前沿 / 补不上 / 已填 / 换了类型；数太大的写「边界」
  const st = it.kind === 'hole' ? holeState(it).status : null;
  const flagText = st ? holeFlag(it, st) : '';
  const flag = st ? `<span class="card-flag">${flagText}</span>` : '';
  const cls = `card k-${it.kind}${st ? ` st-${st}` : ''}`;
  const inner = `
    <span class="card-type">${KIND[it.kind]}</span>${flag}
    <span class="card-main sz-${size}"><span>${math(keepRows(main))}</span></span>
    <span class="card-sub">${fresh}${math(subText(it))}</span>`;
  if (still) return `<div class="${cls}">${inner}</div>`;
  const what = st ? `${KIND[it.kind]}（${flagText}）` : KIND[it.kind];
  const aria = slot ? `移除${what} ${main}` : `${what} ${main}`;
  return `<button type="button" class="${cls}" data-act="${act}" data-id="${esc(it.id)}"${
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
  // 缺口相关的任务要看手里有几张缺口卡、填过几个缺口
  const ctx = { holes: holeCount(), filled: S.filled.length };
  const idx = open.findIndex(q => !q.done(has, ctx));
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
  // 任务编号按章计：入门是一组，每一章各是一组
  const group = open.filter(x => x.ch === q.ch);
  return `<section class="quest" aria-label="当前任务"><span class="quest-step">${where} · 任务 ${group.indexOf(q) + 1}/${group.length} · ${esc(
    q.title,
  )}</span><p>${math(q.text)}</p></section>`;
}

function slotHTML(k) {
  const label = { L: '左', M: '算子', R: '右' }[k];
  const it = itemOf(S.slots[k]);
  const active = S.active === k;
  // 点卡时多项式会放到左右两边；要放到中间，得先点中间的空格
  const polyTip =
    k === 'M' && [...S.items.values()].some(isCallable)
      ? '<span class="slot-tip">多项式：先点这里，再点那张卡</span>'
      : '';
  const empty = active ? '下一张放这里' : k === 'M' ? `放一个算子${polyTip}` : '空位';
  return `<div class="slot${active ? ' is-active' : ''}"><span class="slot-label">${label}</span>${
    it
      ? cardHTML(it, { act: 'slot', slot: k })
      : `<button type="button" class="slot-empty" data-act="slot" data-slot="${k}">${empty}</button>`
  }</div>`;
}

// 底板「在……里」：可选，只放卡组。合成会限制在这个世界里，跑出去的部分成为缺口。
function floorHTML() {
  const it = itemOf(S.slots.W);
  const active = S.active === 'W';
  const inner = it
    ? `<span class="floor-name">${math(mainText(it))}</span><span class="floor-sub">${math(subText(it))}</span><span class="floor-x" aria-hidden="true">×</span>`
    : `<span class="floor-blank">${active ? '下一张卡组放这里' : '点这里，再点一个卡组'}</span>`;
  const aria = it ? `移除底板上的卡组 ${mainText(it)}` : active ? '底板已选中，下一张卡组放这里' : '选中底板：在某个卡组里做运算';
  return `<div class="floor${active ? ' is-active' : ''}${it ? ' is-set' : ''}">
    <span class="floor-word">在</span>
    <button type="button" class="floor-slot" data-act="slot" data-slot="W" aria-pressed="${active}" aria-label="${esc(aria)}">${inner}</button>
    <span class="floor-word">里<small>（可选）</small></span>
  </div>`;
}

function benchHTML() {
  return `<section class="bench" aria-label="合成台">
    <div class="bench-title"><h2>合成台</h2><span>点卡放上来，点格子里的卡移除</span></div>
    ${floorHTML()}
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
    return `<p class="result-idle">左右两格放单卡或卡组，中间放算子。左右格空着时，那个位置就代表变量 <i>x</i>。上面的「在……里」可以放一个卡组：合成就在这个世界里做，跑出去的部分成为缺口。</p>`;
  }
  if (!L.ok) {
    return `<div class="result is-fail" role="status"><strong>合不成</strong><p>${math(L.msg)}</p></div>`;
  }
  const it = L.id ? itemOf(L.id) : null;
  const holes = (L.holes ?? []).map(h => itemOf(h.id)).filter(Boolean);
  const newHoles = (L.holes ?? []).filter(h => h.isNew).length;
  const tags = [];
  if (it) {
    const tag = L.isNew ? (it.kind === 'deck' ? '新卡组' : `新${KIND[it.kind]}`) : L.recipeNew ? '新做法' : '已经有了';
    tags.push(`<span class="tag${L.isNew || L.recipeNew ? ' tag-new' : ''}">${tag}</span>`);
  }
  if (newHoles) tags.push(`<span class="tag tag-hole">新缺口${newHoles > 1 ? ` ${newHoles} 张` : ''}</span>`);
  else if (holes.length) tags.push('<span class="tag">缺口已经有了</span>');
  if (L.grade && GRADE[L.grade]) tags.push(`<span class="grade g-${L.grade}">${GRADE[L.grade]}</span>`);
  // 两栏：得到（可能为空）｜缺口卡（零到多张）
  const gotCol = `<div class="res-col res-got"><span class="res-h">得到</span>${
    it ? cardHTML(it, { act: 'info' }) : '<div class="res-empty">成立的部分一张都没有</div>'
  }</div>`;
  const holeCol = holes.length
    ? `<div class="res-col res-holes"><span class="res-h">缺口 <span class="tab-n">${holes.length}</span></span><div class="res-hole-cards">${holes
        .map(h => cardHTML(h, { act: 'info' }))
        .join('')}</div></div>`
    : '';
  const actions = [
    it ? '<button type="button" class="btn" data-act="reuse">放到左边继续</button>' : '',
    it ? `<button type="button" class="btn" data-act="info" data-id="${esc(it.id)}">详情</button>` : '',
    holes.length ? `<button type="button" class="btn" data-act="info" data-id="${esc(holes[0].id)}">缺口详情</button>` : '',
  ].join('');
  // 每解锁一章写一段，只列这一章自己的赠卡
  const unlock = [].concat(L.unlocked ?? [])
    .map(chapterOf)
    .filter(Boolean)
    .map(ch => {
      const own = new Set(ch.unlock.gives.map(r => resolveRef(r).id));
      const names = (L.gifts ?? []).filter(id => own.has(id)).map(itemOf).filter(Boolean).map(label);
      return `<p class="unlock"><strong>解锁第${CH_NO[ch.id - 1]}章「${esc(ch.title)}」</strong>${
        names.length ? `，获得新卡：${math(names.join('、'))}` : ''
      }。${esc(ch.unlock.note ?? '')}</p>`;
    })
    .join('');
  const pop = L.isNew || newHoles ? ' is-new' : '';
  return `<div class="result${holes.length ? ' has-holes' : ''}${pop}" role="status">
    ${gotCol}${holeCol}
    <div class="result-body">
      <div class="tags">${tags.join('')}</div>
      <p>${math(L.text)}</p>${unlock}
      <div class="result-actions">${actions}</div>
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
    // 按类型自己的比较函数排序（量：先按量纲分组再按大小），没有就按 key
    xs.sort((a, b) => cmpV(a.v, b.v));
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
    holes: all.filter(i => i.kind === 'hole'),
  };
}

function handHTML() {
  const g = handGroups();
  const counts = {
    card: g.cards.length,
    op: g.bins.length + g.uns.length + g.metas.length,
    deck: g.decks.length,
    hole: g.holes.length,
  };
  const freshIn = tab => [...S.fresh].some(id => TAB_OF[itemOf(id)?.kind] === tab);
  const tabs = [
    ['card', '单卡'],
    ['op', '算子'],
    ['deck', '卡组'],
    ['hole', '缺口'],
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
  } else if (S.tab === 'hole') {
    body = g.holes.length
      ? `<p class="muted small">缺口是走不通的地方：没有定义、表示不了，或者跑出了「在……里」的世界。点开看它能不能填；缺口卡也能当卡组用，等于缺的那一部分。</p>${gridHTML(
          g.holes,
        )}`
      : '<p class="muted small">还没有缺口。把一个卡组放进合成台上方的「在……里」，再在里面做运算：跑出去的部分就是缺口。除以 0 这种没有定义的运算也会留下缺口。</p>';
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
  // 临时提示放在手牌里、刚点的卡上方：点卡时合成台常常已经滚出屏幕
  const tip = S.tip ? `<p class="hand-tip" role="status">${esc(S.tip)}</p>` : '';
  return `<section class="hand" aria-label="手牌"><div class="hand-tabs" role="tablist">${tabs}</div>${tip}${body}</section>`;
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
  if (S.inventor.includes(it.id)) {
    html += `<p><span class="badge badge-inventor">发明者</span>这个世界填上了一个以前没有人填过的缺口，是你首先发现的。</p>`;
  }
  html += `<h3 class="sub-title">你找到的做法</h3>${
    found.length
      ? `<ul class="recipes">${found.map(r => `<li>${math(r)}</li>`).join('')}</ul>`
      : '<p class="muted small">还没有记录。</p>'
  }`;
  if (c) html += refListHTML(c);
  return html;
}

// 值级的缺口：左右两格是单卡（或空着）、中间是算子，出发的只有一两张卡。
// 返回"这一步"的算式（√2、1/0、2 − 3）；卡组级的缺口返回 null。
// 引擎给了 expr 就用它（没有定义 / 表示不了）；越出世界的值级缺口没有 expr，从 desc 里的原卡拼出来
function holeStep(h) {
  if (h.v.expr) return h.v.expr;
  const [l, m, r] = h.desc?.from ?? [];
  if (!m || m.k === 'meta' || ![l, r].every(d => !d || d.k === 'card')) return null;
  const card = d => (d ? itemOf(`c:${d.x}`) : null);
  const a = card(l);
  const b = card(r);
  if (m.k === 'bin' && a && b && BIN[m.id]) return `${fmtR(a.v)} ${BIN[m.id].sym} ${fmtR(b.v)}`;
  const x = a ?? b;
  if (m.k !== 'bin' && x && h.v.law?.t === 'un') return fmtU(h.v.law.f, fmtR(x.v));
  return h.v.inputName ?? h.v.sourceName ?? '';
}

// 缺口详情：类别、法、出发世界（值级叫「这一步」）、缺了什么 / 卡在哪些输入上、状态与说明
function holeDetailHTML(h) {
  const v = h.v;
  const { status, withId } = holeState(h);
  const row = (k, val) => `<div><dt>${k}</dt><dd>${val}</dd></div>`;
  const step = holeStep(h);
  // 越出世界：where 是跑出去的结果，就是缺的东西（换了类型的除外：那不是这个世界缺的）。
  // 没有定义 / 表示不了：where 是走不通的输入。
  // 值级缺口的名字就是那个式子（√2），已经写在「这一步」里，这一行只列输入
  const outside = v.kind === 'outside';
  const whereLabel = !outside ? '卡在这些输入上' : status === 'retyped' ? '跑出去的结果' : '缺了什么';
  const where = math(previewDeck(v.where));
  const miss =
    v.name && (outside || step === null)
      ? `<span class="fact-name">${math(v.name)}</span> <span class="muted">${where}</span>`
      : where;
  const facts = [
    row('类别', esc(v.kindText ?? '')),
    row('法', `<span class="fact-math">${math(v.lawText ?? '')}</span>`),
    // 越出世界的缺口：sourceName 是底板世界，真正的输入在 inputName 里
    step === null
      ? row('出发世界', `<span class="fact-math">${math(v.inputName ?? v.sourceName ?? '')}</span>`)
      : row('这一步', `<span class="fact-math">${math(step)}</span>`),
    v.world ? row('在……里', `<span class="fact-math">${math(v.world.name ?? previewDeck(v.world))}</span>`) : '',
    row(whereLabel, miss),
  ].join('');
  let note;
  switch (status) {
    case 'filled':
      note = `已填成 ${math(nameOfId(withId) || '一个新世界')}`;
      break;
    case 'fillable':
      note = `可以填成 ${math(catShort(v.targetId))}`;
      break;
    case 'frontier':
      // 越出世界的前沿真能手填；表示不了的前沿，出发世界里的输入本身就算不出有理数，现有的卡都填不上
      note =
        v.kind === 'unrepresentable'
          ? '前沿：现在的数还写不出这些结果（比如 √2）。这类缺口要等新的数出现，现在的卡填不上'
          : '前沿：图鉴里还没有装得下它的世界。用现有的卡凑一个来手填，奖励更高';
      break;
    case 'retyped':
      // 并、交不会"把结果变成别的东西"：另一种东西是另一边放进来的
      note =
        v.law?.t === 'meta'
          ? `${v.name ? math(v.name) : '这部分'}是另一边放进来的另一种东西，不是这个世界缺的部分；拿掉底板再做一次，两边就都留下`
          : `结果换了一种东西，不是这个世界缺的部分；拿掉底板再做一次，就能直接得到${
              v.targetId ? ` ${math(catShort(v.targetId))}` : '它'
            }`;
      break;
    default:
      note = v.tooLarge ? '游戏的边界：数太大' : '补不上：这条法在这里没有定义';
  }
  return `<dl class="facts">${facts}</dl><p class="hole-note st-${status}">${note}</p>`;
}

function itemSheetHTML(it, back) {
  let rows = '';
  switch (it.kind) {
    case 'card': {
      const what = !isR(it.v) ? `${typeLabel(it.v)}。` : it.v.d === 1 ? '一个整数。' : `一个分数，约等于 ${decimal(it.v)}。`;
      const asFn = isCallable(it)
        ? '它也可以放在中间当算子用：旁边放单卡就代入，放卡组就对每张卡都代入。直接点这张卡会放到左右两边；要放到中间，先点合成台中间的空格，再点这张卡，或者按下面的「放到中间」。'
        : '';
      rows = `<p>${esc(what)}</p>
        <p class="muted">单卡放在合成台左右两边，和中间的算子一起算出新卡。${asFn}</p>`;
      break;
    }
    case 'bin':
      rows = `<p>${esc(it.info?.desc ?? '')}</p>
        <p class="muted">两边放单卡，算出新单卡；只放一边，得到一元算子；卡组配单卡，卡组里每张卡都做这个运算；两个卡组，两两运算收集结果。</p>`;
      break;
    case 'meta':
      rows = `<p>${math(it.v.desc)}</p><p class="muted">用法：${math(it.v.usage)}</p>`;
      break;
    case 'hole':
      rows = holeDetailHTML(it);
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
  const eyebrow = it.kind === 'hole' ? `缺口 · ${it.v.kindText ?? ''}` : KIND[it.kind];
  const id = esc(it.id);
  let actions;
  if (it.kind === 'hole') {
    // 可填的缺口：「填」等于合成台上的 [缺口] [填] [空]；「放上合成台」放到左格，用来手填或当卡组用。
    // 按钮看缺口自己的状态和本局的填过记录，不看手里有没有目标世界：已经有了，填一下也算完成
    const canFill = it.v.status === 'fillable' && !S.filled.includes(it.id) && has('m:fill');
    const owned = canFill && it.v.targetId && has(`d:${it.v.targetId}`);
    actions = `${canFill ? `<button type="button" class="btn btn-primary" data-act="fill" data-id="${id}">填</button>` : ''}<button type="button" class="btn${
      canFill ? '' : ' btn-primary'
    }" data-act="place-close" data-id="${id}" data-slot="L">放上合成台</button>${
      owned ? `<p class="act-note">你已经有 ${math(catSym(it.v.targetId))} 了，填一下也算完成</p>` : ''
    }`;
  } else {
    actions = `<button type="button" class="btn btn-primary" data-act="place-close" data-id="${id}">放上合成台</button>${
      isCallable(it) ? `<button type="button" class="btn" data-act="place-close" data-id="${id}" data-slot="M">放到中间</button>` : ''
    }${it.kind === 'deck' ? `<button type="button" class="btn" data-act="place-close" data-id="${id}" data-slot="W">放进「在……里」</button>` : ''}`;
  }
  return sheetFrame(
    `<div class="detail"><div>${cardHTML(it, { still: true })}</div><div><p class="eyebrow">${esc(
      eyebrow,
    )}</p><h2 id="sheet-title">${math(title)}</h2></div></div>
    ${rows}
    <div class="sheet-actions">${actions}</div>`,
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
      <span class="tile-name">${esc(c.name)}${inventorBadge(id)}</span>
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

const inventorBadge = id => (S.inventor.includes(id) ? ' <span class="badge badge-inventor">发明者</span>' : '');

// 图鉴末尾的「自造」区：图鉴以外、玩家自己造出来的卡组
function selfMadeHTML() {
  const mine = S.order.map(itemOf).filter(it => it.kind === 'deck' && !it.cat);
  if (!mine.length) return '';
  const tiles = mine
    .map(it => {
      const n = (S.recipes[it.id] || []).length;
      return `<button type="button" class="tile is-got is-self" data-act="info" data-id="${esc(it.id)}" data-back="codex">
      <span class="tile-sym">${math(it.v.name)}</span>
      <span class="tile-name">${it.v.approx ? '自造 · 近似' : '自造卡组'}${inventorBadge(it.id)}</span>
      <span class="tile-prev">${math(previewDeck(it.v))}</span>
      <span class="tile-meta">找到 ${n} 种做法</span>
    </button>`;
    })
    .join('');
  return `<section class="chapter"><h3><span class="ch-no">自造</span>图鉴以外的卡组 <span class="ch-count">${mine.length}</span></h3>
    <p class="muted small">你自己造出来、图鉴里没有的卡组。填上一个没人填过的缺口，就是它的发明者。</p>
    <div class="codex-grid">${tiles}</div>
  </section>`;
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
    ${selfMadeHTML()}
    <div class="reset">${reset}</div>`);
}

let codexScroll = 0;

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
  // 从图鉴点开提示或卡组详情，再按「← 图鉴」回来时，回到原来的滚动位置
  if (oldPanel?.dataset.key === 'codex:') codexScroll = oldPanel.scrollTop;
  if (!S.sheet) codexScroll = 0;
  const key = sheetKey();
  const keepScroll =
    !oldPanel || !S.sheet ? 0 : oldPanel.dataset.key === key ? oldPanel.scrollTop : key === 'codex:' ? codexScroll : 0;
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
    panel.dataset.key = key;
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
  // 临时提示只管一次点击
  S.tip = null;
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
      S.slots = emptySlots();
      S.active = null;
      save();
      render();
      break;
    case 'fill':
      autoFill(el.dataset.id);
      break;
    case 'reuse':
      if (S.last?.id && has(S.last.id)) {
        S.slots = { ...emptySlots(), L: S.last.id };
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
      if (el.dataset.slot) S.active = el.dataset.slot;
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
      S.slots = { ...emptySlots(), L: 'c:1', M: 'b:add', R: 'c:1' };
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
    S.slots = { ...emptySlots(), L: 'c:1', M: 'b:add', R: 'c:1' };
  }
  render();
}

window.claude?.hot?.snapshot?.(() => ({ save: snapshot() }));
if (window.claude?.hot?.ready) window.claude.hot.ready(start);
else start(window.claude?.hot?.data ?? {});
