// 合成规则：合成台上 [左] [算子] [右] 三个格子，放进去的东西决定会得到什么。

import { OVER, isR } from './math.js';
import {
  BIN,
  MSG_OVER,
  binV,
  isV,
  vkey,
  fmtV,
  parseVKey,
  defOf,
  subtypeOf,
  typeLabel,
  familyOf,
  probesFor,
  smallProbesFor,
  sizeV,
  sizeCapFor,
  classify,
} from './values.js';
import { applyU, bindLeft, bindRight, bindU, compose, fmtU, fnU, invertU, parseU, serU, ukey } from './unary.js';
import {
  closurePartition,
  finiteDeck,
  hash,
  imagePartition,
  interDeck,
  isBlank,
  lawClosedOn,
  mkDeck,
  orbitPartition,
  pairwisePartition,
  preimageDeck,
  previewDeck,
  restrictToWorld,
  sampleOf,
  sigOf,
  unionDeck,
  witnessesOf,
} from './decks.js';
import { BIN_INFO, CATALOG_ALL, META, NAMED_UN_ALL } from './content.js';

export const CAT_BY_ID = Object.fromEntries(CATALOG_ALL.map(c => [c.id, c]));
export const META_BY_ID = Object.fromEntries(META.map(m => [m.id, m]));
const NAMED_BY_KEY = new Map(NAMED_UN_ALL.map(u => [ukey(u.f), u]));
const NAMED_BY_ID = Object.fromEntries(NAMED_UN_ALL.map(u => [u.id, u]));

// ───────────────────────── 卡牌（item） ─────────────────────────
// 每张卡：{ kind, v, id, desc }。desc 是存档用的描述，可以用它重新造出这张卡。

export function cardItem(x) {
  return { kind: 'card', v: x, id: `c:${vkey(x)}`, desc: { k: 'card', x: vkey(x) } };
}

export function binItem(b) {
  return { kind: 'bin', v: b, id: `b:${b.id}`, desc: { k: 'bin', id: b.id }, info: BIN_INFO[b.id] };
}

export function metaItem(m) {
  return { kind: 'meta', v: m, id: `m:${m.id}`, desc: { k: 'meta', id: m.id } };
}

export function unItem(f) {
  const named = NAMED_BY_KEY.get(ukey(f));
  return { kind: 'un', v: f, id: `u:${ukey(f)}`, desc: { k: 'un', f: serU(f) }, name: named?.name ?? null };
}

const catCache = new Map();
export function catItem(id) {
  if (!catCache.has(id)) {
    const c = CAT_BY_ID[id];
    const type = c.type ?? 'q';
    // 图鉴的 has 只需要处理本类型的值，别的类型在这里就挡掉
    const D = c.list
      ? finiteDeck(c.list.map(parseVKey), c.short)
      : mkDeck('cat', x => subtypeOf(x) === type && c.has(x), { name: c.short, type });
    D.catId = id;
    catCache.set(id, { kind: 'deck', v: D, id: `d:${id}`, desc: { k: 'deck', cat: id }, cat: c });
  }
  return catCache.get(id);
}

// 卡牌在式子里的写法
export function label(it) {
  switch (it.kind) {
    case 'card':
      return fmtV(it.v);
    case 'deck':
      return it.v.name;
    case 'un':
      return fmtU(it.v);
    case 'hole':
      return holeLabel(it);
    default:
      return it.v.sym;
  }
}

// 已经被一对括号整个包住的文字（向量 "(1, 0)"、矩阵 "[0 1; 1 0]"）不用再加括号
function bracketed(s) {
  const pairs = { '(': ')', '[': ']', '{': '}' };
  const close = pairs[s[0]];
  if (!close || s[s.length - 1] !== close) return false;
  let depth = 0;
  for (let i = 0; i < s.length; i++) {
    if (s[i] === s[0]) depth++;
    else if (s[i] === close) depth--;
    if (depth === 0 && i < s.length - 1) return false;
  }
  return true;
}
const nest = s => (/\s/.test(s) && !bracketed(s) ? `(${s})` : s);
const lab = it => nest(label(it));

// 按引用取卡（测试和图鉴用）：c:1  c:[3]12  b:add  m:extend  u:succ  d:N
export function resolveRef(ref) {
  const [k, v] = [ref.slice(0, 1), ref.slice(2)];
  if (k === 'c') {
    const x = parseVKey(v);
    if (!x) throw new Error(`无法解析的单卡 ${ref}`);
    return cardItem(x);
  }
  if (k === 'b' && BIN[v]) return binItem(BIN[v]);
  if (k === 'm' && META_BY_ID[v]) return metaItem(META_BY_ID[v]);
  if (k === 'u' && NAMED_BY_ID[v]) return unItem(NAMED_BY_ID[v].f);
  if (k === 'd' && CAT_BY_ID[v]) return catItem(v);
  throw new Error(`未知引用 ${ref}`);
}

export function recipeText(recipe) {
  const [L, M, Rt] = recipe.map(r => (r ? resolveRef(r) : null));
  const r = combine(L, M, Rt);
  return r.ok ? r.recipe : '?';
}

// ───────────────────────── 认出图鉴里的卡组 ─────────────────────────

function sameList(a, b) {
  return a.length === b.length && a.every((x, i) => vkey(x) === vkey(b[i]));
}

export function matchCatalog(D) {
  if (D.catId) return CAT_BY_ID[D.catId];
  const type = D.type;
  const emptyFinite = D.list && D.list.length === 0;
  for (const c of CATALOG_ALL) {
    const ctype = c.type ?? 'q';
    if (ctype !== type && !emptyFinite) continue;
    const C = catItem(c.id).v;
    if (D.list) {
      if (C.list && sameList(D.list, C.list)) return c;
      continue;
    }
    if (D.kind === 'approx') {
      // 因为太大没收进来的结果，如果明显不在 C 里，就不是 C
      if (D.lost && !D.lost.every(x => C.has(x) !== false)) continue;
      // 算出来的每张卡都得在 C 里，C 在小探针范围内的卡也都得算出来
      if (C.list) {
        // 有成员大到表示不了的卡组，肯定比算出来的多，不会等于一个有限的图鉴卡组
        if (D.incomplete) continue;
        const elems = [...D.elems].sort((x, y) => (vkey(x) < vkey(y) ? -1 : 1));
        const cl = [...C.list].sort((x, y) => (vkey(x) < vkey(y) ? -1 : 1));
        if (sameList(elems, cl)) return c;
        continue;
      }
      // 有理数视野只到 20，两两运算凑不出 11 这样的素数分子，所以只要求覆盖大小一半以内的探针
      const small = smallProbesFor(type);
      const cover = type === 'q' ? small.filter(x => 2 * sizeV(x) <= sizeCapFor(type)) : small;
      if (D.elems.every(x => C.has(x)) && cover.every(x => !C.has(x) || D.has(x))) return c;
      continue;
    }
    // 小探针必须都判断得出来；大数探针如果超出范围（null）就跳过
    const small = smallProbesFor(type);
    const smallKeys = new Set(small.map(vkey));
    const probes = D.approx ? small : probesFor(type);
    const same = x => {
      const d = D.has(x);
      return d === null ? !smallKeys.has(vkey(x)) : d === C.has(x);
    };
    if (!probes.every(same)) continue;
    // 再在这个卡组自己的"边界值"上比对，防止探针之外的差别被漏掉
    const sameW = x => {
      const d = D.has(x);
      return d === null || d === C.has(x);
    };
    if (witnessesOf(D).every(sameW)) return c;
  }
  return null;
}

function fingerprint(D) {
  if (D.list) return `f${hash(D.list.map(vkey).join(','))}`;
  if (D.kind === 'approx') return `a${hash(D.elems.map(vkey).sort().join(','))}`;
  // 混合类型的卡组按成员的各个类型分别取探针
  const types = D.type === 'set' ? [...new Set(sampleOf(D).map(subtypeOf))].sort() : [D.type];
  const probes = types.flatMap(t => (D.approx ? smallProbesFor(t) : probesFor(t)));
  const wit = witnessesOf(D)
    .map(x => `${vkey(x)}=${D.has(x)}`)
    .sort()
    .join(',');
  return `e${hash(types.join('|') + ':' + sigOf(D, probes) + ':' + wit)}`;
}

// ───────────────────────── 合成 ─────────────────────────
// 结果的形状见 docs/v03-step1.md：永远是 { ok: true, item, holes, text }，
// 只有"用法提示"才是 { ok: false, msg }。

const fail = msg => ({ ok: false, msg });
const ok = (item, text, extra = {}) => ({ ok: true, item, holes: [], text, ...extra });

const HOLE_KIND = { undefined: '没有定义', unrepresentable: '表示不了', outside: '越出世界' };

function errText(r) {
  if (r === OVER) return MSG_OVER;
  if (r && typeof r === 'object' && r.err) return r.err;
  return '这一步算不出结果。';
}

const fpDeck = D => (D.catId ? `cat:${D.catId}` : fingerprint(D));
// 法：{ t:'un', f } 一元 | { t:'bin', b } 二元 | { t:'meta', id } 并/交 | { t:'pre', f, target } 反推
const lawKeyOf = law =>
  law.t === 'un' ? ukey(law.f) : law.t === 'bin' ? `bin:${law.b.id}` : law.t === 'pre' ? `pre:${ukey(law.f)}:${fpDeck(law.target)}` : `meta:${law.id}`;
const catTitle = c => (c.short === c.name || /[一-鿿]/.test(c.short) ? `「${c.name}」` : `「${c.name} ${c.short}」`);

// ───────────────────────── 缺口卡 ─────────────────────────

// 跑出去的部分是不是"另一种东西"：类型不同（数 → 余数），或者族全都不同（长度 → 面积）
function retyped(base, where) {
  if (where.type !== base.type) return true;
  const fam = D => new Set(sampleOf(D).slice(0, 12).map(familyOf));
  const a = fam(base);
  const b = fam(where);
  return b.size > 0 && [...b].every(f => !a.has(f));
}

// 这个缺口能填成图鉴里的哪个世界：{ status: 'fillable' | 'frontier' | 'unfillable' | 'retyped', id }
function findTarget(spec) {
  if (spec.kind === 'undefined' || spec.tooLarge) return { status: 'unfillable', id: null };
  const base = spec.world ?? spec.source;
  const type = base.type;
  // 结果换了一种东西：这不是这个世界的缺口，拿掉底板就能直接得到它
  if (spec.kind === 'outside' && retyped(base, spec.where)) return { status: 'retyped', id: spec.where.catId ?? null };
  if (type === 'set') return { status: 'frontier', id: null };
  const escaped = spec.kind === 'outside' ? sampleOf(spec.where).slice(0, 40) : [];
  const need = [...sampleOf(base).slice(0, 40), ...escaped];
  const probes = probesFor(type);
  const cands = [];
  for (const c of CATALOG_ALL) {
    if ((c.type ?? 'q') !== type) continue;
    if (base.catId === c.id) continue;
    const C = catItem(c.id).v;
    if (!need.every(x => C.has(x) === true)) continue;
    // 封闭：结果都在候选里或者没有定义；写不出来的结果也算没关住（缺口里的值必查）
    const r = lawClosedOn(C, spec.law, 40, escaped);
    if (r.escaped.length || r.unrep) continue;
    cands.push(c);
  }
  if (!cands.length) return { status: 'frontier', id: null };
  // 最小：不真包含别的候选；再按探针里的成员数取最少的
  const has = (c, x) => catItem(c.id).v.has(x) === true;
  const contains = (a, b) => probes.every(x => !has(b, x) || has(a, x));
  const minimal = cands.filter(a => !cands.some(b => b !== a && contains(a, b) && !contains(b, a)));
  minimal.sort((a, b) => probes.filter(x => has(a, x)).length - probes.filter(x => has(b, x)).length);
  return { status: 'fillable', id: minimal[0].id };
}

// spec: { kind, law, lawText, source, sourceName, where, world, tooLarge?, name?, expr? }
function holeItem(spec, from, W, idx) {
  // 越出世界的缺口，出发世界就是底板上的那个世界；真正的输入另记在 inputName 里
  if (spec.kind === 'outside' && spec.world) spec = { ...spec, inputName: spec.sourceName, source: spec.world, sourceName: spec.world.name };
  const c = spec.where.catId ? CAT_BY_ID[spec.where.catId] : matchCatalog(spec.where);
  const where = c ? catItem(c.id).v : spec.where;
  const target = findTarget({ ...spec, where });
  const v = {
    ...spec,
    where,
    name: c ? c.name : (spec.name ?? null),
    lawKey: lawKeyOf(spec.law),
    kindText: HOLE_KIND[spec.kind],
    status: target.status,
    targetId: target.id,
  };
  const id = `h:${hash([spec.kind, v.lawKey, fpDeck(spec.source), fpDeck(where)].join('|'))}`;
  return {
    kind: 'hole',
    v,
    id,
    desc: { k: 'hole', from: from.map(x => (x ? x.desc : null)), w: W ? W.desc : null, kind: spec.kind, idx },
  };
}

// 把 *Partition 的 holes 做成缺口卡
function holesFrom(specs, from, W) {
  const count = {};
  return specs.map(s => {
    const idx = count[s.kind] ?? 0;
    count[s.kind] = idx + 1;
    return holeItem(s, from, W, idx);
  });
}

const holeSummary = holes =>
  holes.map(h => `缺口（${h.v.kindText}）：${h.v.name ?? previewDeck(h.v.where)}`).join('；');

// 缺口卡在式子里的写法
export function holeLabel(h) {
  return `缺口(${h.v.name ?? previewDeck(h.v.where, 3)})`;
}

// ───────────────────────── 结果 ─────────────────────────

function selfItem(D, from, W) {
  if (D.list && D.list.length <= 6) D.name = previewDeck(D);
  return {
    kind: 'deck',
    v: D,
    id: `d:~${fingerprint(D)}`,
    desc: { k: 'deck', from: from.map(x => (x ? x.desc : null)), w: W ? W.desc : null },
  };
}

// 卡组结果：认图鉴、起名字、带上缺口
function deckResult(D, from, text, recipe, opts = {}) {
  const W = opts.W ?? null;
  const holes = holesFrom(opts.holes ?? [], from, W);
  const tail = holes.length ? `${holeSummary(holes)}。` : '';
  const rec = W ? `${recipe}（在 ${W.v.name} 里）` : recipe;
  if (isBlank(D) && holes.length && !opts.keepEmpty) {
    return ok(null, `${text}。成立的部分一张都没有。${tail}`, { holes, recipe: rec });
  }
  const c = matchCatalog(D);
  // 有缺口时，认出来的只是成立的那部分，别说成"全部结果就是"
  const lead = holes.length ? (W ? `留在 ${W.v.name} 里的结果就是` : '算得出来的结果就是') : '这就是';
  if (c) return ok(catItem(c.id), `${text}。${lead}${catTitle(c)}！${tail}`, { recipe: rec, catId: c.id, holes });
  const item = selfItem(D, from, W);
  const note = D.dropped
    ? '（结果都超出了视野的大小，这个卡组暂时看不到具体内容。）'
    : D.approx
      ? '（这个卡组只在一个小范围里算过，内容是近似的。）'
      : '';
  return ok(item, `${text}。${note}${tail}`, { recipe: rec, holes });
}

// 值结果：可能没有定义、表示不了，或者不在底板世界里
function cardResult(r, from, W, law, lawText, input, text, src = {}) {
  const inputs = src.inputs ?? [input];
  // 出发世界写成只含这几张卡的卡组（{1, 0}），算式（1 ÷ 0）另记在 expr 里
  const source = finiteDeck(inputs, '');
  const sourceName = previewDeck(source);
  source.name = sourceName;
  const k = classify(r);
  if (k === 'ok') {
    if (W && W.v.has(r) === false) {
      const spec = { kind: 'outside', law, lawText, source, sourceName, where: finiteDeck([r], fmtV(r)), world: W.v };
      const holes = holesFrom([spec], from, W);
      return ok(null, `${text}，但 ${fmtV(r)} 不在 ${W.v.name} 里。${holeSummary(holes)}。`, { holes });
    }
    return ok(cardItem(r), text);
  }
  if (k === 'type') return fail(errText(r));
  // 值级的缺口用"写不出来的那个式子"当名字：√2、1/0、2^(1/2)
  const expr = law.t === 'un' ? fmtU(law.f, fmtV(input)) : (src.name ?? sourceName);
  const spec = {
    kind: k,
    law,
    lawText,
    source,
    sourceName,
    where: finiteDeck([input], fmtV(input)),
    world: null,
    tooLarge: r === OVER,
    name: expr,
    expr,
  };
  const holes = holesFrom([spec], from, W);
  return ok(null, `${errText(r)}${holeSummary(holes)}。`, { holes });
}

const asDeck = it => (it.kind === 'deck' ? it.v : it.kind === 'hole' ? it.v.where : finiteDeck([it.v], fmtV(it.v)));
const isSetLike = it => it && (it.kind === 'card' || it.kind === 'deck' || it.kind === 'hole');
const isDeckLike = it => it && (it.kind === 'deck' || it.kind === 'hole');

// 在左右两格里找一对 [A, B]，A 的种类在 kindsA 里，B 的种类是 kindB，顺序不限
function pairOf(L, Rt, kindsA, kindB) {
  if (L && Rt) {
    if (kindsA.includes(L.kind) && Rt.kind === kindB) return [L, Rt];
    if (kindsA.includes(Rt.kind) && L.kind === kindB) return [Rt, L];
  }
  return null;
}

const single = (L, Rt) => (L && !Rt ? L : Rt && !L ? Rt : null);

const isFnCard = it => it?.kind === 'card' && !!defOf(it.v).call;
// 算子公式里含多项式时，输入写成 □ 而不是 x（免得和多项式的 x 混淆）
const varName = f => (fmtU(f).includes('□') ? ' □' : ' x');

// L、M、Rt 是三个格子；W 是底板上的世界（卡组卡），可以为空
export function combine(L, M, Rt, W = null) {
  if (W && W.kind !== 'deck') return fail('底板上只能放卡组：合成会限制在这个世界里进行。');
  if (!M) {
    const hint = isFnCard(L) || isFnCard(Rt) ? '多项式也能当算子：先点中间的空格，再点这张多项式。' : '';
    return fail(`中间的「算子」格还空着。放一个算子进去：橙色、黄色或紫色的卡。${hint}`);
  }
  if (M.kind === 'card') {
    // 多项式这种可以当函数用的单卡，放在中间就是一元算子（desc 保留原卡，存档才能重建）
    if (defOf(M.v).call) return withUn(L, { kind: 'un', v: fnU(M.v), desc: M.desc }, Rt, W, '代入');
    return fail('中间的格子只能放算子。单卡和卡组请放在左右两边。多项式可以放中间当算子用。');
  }
  if (M.kind === 'deck' || M.kind === 'hole') return fail('中间的格子只能放算子。单卡、卡组和缺口请放在左右两边。');
  if (M.kind === 'bin') return withBin(L, M, Rt, W);
  if (M.kind === 'un') return withUn(L, M, Rt, W);
  return withMeta(L, M, Rt, W);
}

function withBin(L, M, Rt, W) {
  const b = M.v;
  const kindOf = it => (!it ? '空' : it.kind === 'hole' ? 'deck' : it.kind);
  const k = `${kindOf(L)}|${kindOf(Rt)}`;
  const from = [L, M, Rt];
  switch (k) {
    case 'card|card': {
      const r = binV(b.id, L.v, Rt.v);
      const eqn = `${fmtV(L.v)} ${b.sym} ${fmtV(Rt.v)}`;
      // 多项式 x + 1 算出来还是写成 x + 1，不用再写一遍等号
      const text = isV(r) ? (fmtV(r) === eqn ? `${eqn}：得到新卡 ${fmtV(r)}` : `${eqn} = ${fmtV(r)}`) : eqn;
      const bound = bindLeft(L.v, b);
      const law = bound.f ? { t: 'un', f: bound.f } : { t: 'bin', b };
      return cardResult(r, from, W, law, bound.f ? fmtU(bound.f) : b.sym, Rt.v, text, { inputs: [L.v, Rt.v], name: eqn });
    }
    case '空|card': {
      const r = bindRight(b, Rt.v);
      if (r.err) return fail(r.err);
      return ok(unItem(r.f), `左边空着，就是变量${varName(r.f)}。得到一元算子 ${fmtU(r.f)}`);
    }
    case 'card|空': {
      const r = bindLeft(L.v, b);
      if (r.err) return fail(r.err);
      return ok(unItem(r.f), `右边空着，就是变量${varName(r.f)}。得到一元算子 ${fmtU(r.f)}`);
    }
    case 'deck|card': {
      let r = bindRight(b, Rt.v);
      // x ÷ 0、x ^ (1/13) 这种绑不成简式的，逐值算：结果分成得到和缺口，不当用法错误
      if (r.err && isR(Rt.v) && (b.id === 'div' || b.id === 'pow')) r = { f: bindU(b.id, 'r', Rt.v) };
      if (r.err) return fail(r.err);
      return imageResult(L, r.f, from, W, `${lab(L)} ${b.sym} ${fmtV(Rt.v)}`);
    }
    case 'card|deck': {
      const r = bindLeft(L.v, b);
      if (r.err) return fail(r.err);
      return imageResult(Rt, r.f, from, W, `${fmtV(L.v)} ${b.sym} ${lab(Rt)}`);
    }
    case 'deck|deck': {
      const name = `${lab(L)} ${b.sym} ${lab(Rt)}`;
      const A = asDeck(L);
      const B = asDeck(Rt);
      const { got, holes } = pairwisePartition(A, b, B, name, W?.v ?? null);
      if (isBlank(got) && !holes.length && !got.dropped && !isBlank(A) && !isBlank(B)) {
        return fail(got.err ?? `${lab(L)} 和 ${lab(Rt)} 里的卡两两做 ${b.sym} 都算不出结果。`);
      }
      const specs = holes.map(h => ({
        ...h,
        law: { t: 'bin', b },
        lawText: b.sym,
        source: h.side === 'l' ? A : h.side === 'r' ? B : A,
        sourceName: h.side === 'l' ? lab(L) : h.side === 'r' ? lab(Rt) : name,
        world: W?.v ?? null,
      }));
      return deckResult(got, from, `从 ${lab(L)} 和 ${lab(Rt)} 里各取一张做「${b.name}」（${b.sym}），收集结果`, name, {
        W,
        holes: specs,
      });
    }
    case '空|空':
      return fail(`「${b.name}」需要输入：两边都放单卡，算出一张新单卡；只放一边，得到一元算子。`);
    case 'deck|空':
    case '空|deck':
      return fail('卡组和二元算子之间还差一个输入：另一边放一张单卡或一个卡组。');
  }
  return fail(`「${b.name}」两边要放单卡或卡组。想改造算子本身，请用紫色的构造算子。`);
}

// 卡组 X 里的每张卡做 f
function imageResult(X, f, from, W, recipe, verb = null) {
  const D = asDeck(X);
  const { got, holes } = imagePartition(D, f, `{ ${fmtU(f)} | x ∈ ${lab(X)} }`, W?.v ?? null);
  if (isBlank(got) && !holes.length && !isBlank(D)) return fail(got.err ?? `${lab(X)} 里没有一张卡能做 ${fmtU(f)}。`);
  const specs = holes.map(h => ({ ...h, law: { t: 'un', f }, lawText: fmtU(f), source: D, sourceName: lab(X), world: W?.v ?? null }));
  const text = verb === '代入' ? `${lab(X)} 里的每张卡都代入 ${fmtU(f)}` : `${lab(X)} 里的每张卡都做 ${fmtU(f)}`;
  return deckResult(got, from, text, recipe, { W, holes: specs });
}

function withUn(L, M, Rt, W, verb = '经') {
  const f = M.v;
  const ins = [L, Rt].filter(Boolean);
  if (ins.length === 0) return fail(`一元算子 ${fmtU(f)} 需要一个输入：在左边或右边放一张单卡或一个卡组。`);
  if (ins.length === 2) return fail('一元算子只吃一个输入，请把另一边清空。想把两个一元算子接起来，用构造算子「复合」。');
  const X = ins[0];
  const from = [L, M, Rt];
  if (X.kind === 'card') {
    const y = applyU(f, X.v);
    const text = isV(y) ? `把${varName(f)} = ${fmtV(X.v)} 代入 ${fmtU(f)}，得到 ${fmtV(y)}` : `把${varName(f)} = ${fmtV(X.v)} 代入 ${fmtU(f)}`;
    if (!isV(y) && classify(y) === 'type') {
      const why = isR(X.v) ? '（没有定义，或者不是有理数）' : '（这个算子对这种卡没有定义）';
      return fail(y && y.err ? y.err : `${text} 算不出结果${why}。`);
    }
    return cardResult(y, from, W, { t: 'un', f }, fmtU(f), X.v, text);
  }
  if (isDeckLike(X)) return imageResult(X, f, from, W, `${lab(X)} ${verb} ${fmtU(f)}`, verb);
  return fail('一元算子的输入要是单卡或卡组。想改造算子，请用紫色的构造算子，比如「复合」「逆」。');
}

const EXTEND = {
  add: { to: 'mul', text: '反复做加法就是乘法：3 × 4 = 4 + 4 + 4' },
  mul: { to: 'pow', text: '反复做乘法就是乘方：2⁴ = 2 × 2 × 2 × 2' },
  sub: { to: 'mod', text: '反复减去（负数就反复加上）同一个数，直到落在 0 到它减 1 之间，剩下的就是余数：17 mod 5 = 2，−17 mod 5 = 3' },
};
const INVERSE = {
  add: { to: 'sub', text: '加法倒过来做就是减法：a + b = c，那么 c − b = a' },
  sub: { to: 'add', text: '减法倒过来做就是加法' },
  mul: { to: 'div', text: '乘法倒过来做就是除法：a × b = c，那么 c ÷ b = a' },
  div: { to: 'mul', text: '除法倒过来做就是乘法' },
};

function withMeta(L, M, Rt, W) {
  const m = M.v;
  const from = [L, M, Rt];
  const Wd = W?.v ?? null;
  switch (m.id) {
    case 'extend': {
      const p = pairOf(L, Rt, ['card'], 'un');
      if (p) {
        const [c, u] = p;
        const name = `${fmtV(c.v)} ⟳ ${nest(fmtU(u.v))}`;
        const { got, holes } = orbitPartition(c.v, u.v, name, Wd);
        const specs = holes.map(h => ({
          ...h,
          law: { t: 'un', f: u.v },
          lawText: fmtU(u.v),
          source: got,
          sourceName: name,
          world: Wd,
        }));
        const steps = isBlank(got) ? '一步都走不了' : previewDeck(got);
        return deckResult(got, from, `从 ${fmtV(c.v)} 出发，一直做 ${fmtU(u.v)}：${steps}`, `${fmtV(c.v)} 延展 ${fmtU(u.v)}`, {
          W,
          holes: specs,
        });
      }
      const one = single(L, Rt);
      if (one?.kind === 'bin') {
        const e = EXTEND[one.v.id];
        if (!e) {
          if (one.v.id === 'pow') return fail('反复做乘方叫「迭代幂」，已经超出这个游戏的范围啦。');
          return fail('「延展」只能升级加法（得到乘法）、乘法（得到乘方）和减法（得到取余）。');
        }
        return ok(binItem(BIN[e.to]), e.text);
      }
      if (one?.kind === 'un') return fail('「延展」还需要一个起点：另一边放一张单卡，从它出发反复做这个一元算子。');
      if (one?.kind === 'card') return fail('「延展」还需要一个一元算子，告诉它每一步怎么走，比如 x + 1。');
      return fail('「延展」的用法：单卡 ＋ 一元算子 → 卡组；或者只放一个二元算子，把它升级。');
    }
    case 'closure': {
      const p = pairOf(L, Rt, ['card', 'deck', 'hole'], 'bin');
      if (!p) return fail('「封闭」的用法：一边放单卡或卡组作为起点，另一边放二元算子作为组合方式。');
      const [X, b] = p;
      const D = asDeck(X);
      const { got, holes } = closurePartition(D, b.v, `⟨${label(X)} | ${b.v.sym}⟩`, Wd);
      const specs = holes.map(h => ({ ...h, law: { t: 'bin', b: b.v }, lawText: b.v.sym, source: D, sourceName: lab(X), world: Wd }));
      const how = got.truncated ? '反复组合（更大的结果超出了能显示的范围，没有算进来）' : '反复组合，直到得不到新卡';
      return deckResult(got, from, `从 ${lab(X)} 出发，用 ${b.v.sym} ${how}`, `${lab(X)} 在 ${b.v.sym} 下封闭`, { W, holes: specs, keepEmpty: true });
    }
    case 'inverse': {
      const one = single(L, Rt);
      if (!one) return fail('「逆」只需要一个算子：在左边或右边放一个二元算子或一元算子。');
      if (one.kind === 'bin') {
        const e = INVERSE[one.v.id];
        if (!e) {
          if (one.v.id === 'pow') {
            return fail(
              '乘方倒过来有两种：已知指数求底数是开方，已知底数求指数是对数。先给乘方绑定一个数（比如 x² 或 2ˣ），再对它用「逆」。',
            );
          }
          return fail(`「${one.v.name}」会丢掉信息，没法倒过来做。`);
        }
        return ok(binItem(BIN[e.to]), e.text);
      }
      if (one.kind === 'un') {
        const g = invertU(one.v);
        if (!g) {
          return fail(`${fmtU(one.v)} 没有逆：不同的输入会得到同一个结果，没法倒推回去。想知道哪些输入能得到某个结果，用「反推」。`);
        }
        const note = one.v.t === 'pow' && one.v.n.d === 1 && one.v.n.n % 2 === 0 ? '（只取正的那个根）' : '';
        return ok(unItem(g), `${fmtU(one.v)} 的逆是 ${fmtU(g)}${note}：先做一个再做另一个，就回到原来的数`);
      }
      return fail('「逆」作用在算子上。想要一张卡的相反数？试试一元算子「取反」，也就是 0 − x。');
    }
    case 'compose': {
      if (L?.kind === 'un' && Rt?.kind === 'un') {
        const h = compose(L.v, Rt.v);
        return ok(unItem(h), `先做 ${fmtU(L.v)}，再做 ${fmtU(Rt.v)}，合起来是 ${fmtU(h)}`);
      }
      return fail('「复合」的用法：左右各放一个一元算子，先做左边的，再做右边的。');
    }
    case 'union':
    case 'inter': {
      if (!isSetLike(L) || !isSetLike(Rt)) {
        return fail(`「${m.name}」的两边都要放卡组。单卡会被当成只有一张卡的卡组，缺口卡当成缺的那部分。`);
      }
      const A = asDeck(L);
      const B = asDeck(Rt);
      const name = `${lab(L)} ${m.sym} ${lab(Rt)}`;
      const D = m.id === 'union' ? unionDeck(A, B, name) : interDeck(A, B, name);
      const { got, outside } = restrictToWorld(D, Wd, name);
      const specs = outside ? [{ kind: 'outside', where: outside, law: { t: 'meta', id: m.id }, lawText: m.sym, source: A, sourceName: lab(L), world: Wd }] : [];
      const text = m.id === 'union' ? `把 ${lab(L)} 和 ${lab(Rt)} 合在一起` : `只留下 ${lab(L)} 和 ${lab(Rt)} 都有的卡`;
      return deckResult(got, from, text, name, { W, holes: specs, keepEmpty: m.id === 'inter' });
    }
    case 'reverse': {
      const p = pairOf(L, Rt, ['card', 'deck', 'hole'], 'un');
      if (!p) return fail('「反推」的用法：一边放一元算子，另一边放一张单卡或卡组，得到所有能算到它的输入。');
      const [X, u] = p;
      const T = asDeck(X);
      const isCard = X.kind === 'card';
      // 和像的写法 { f(x) | x ∈ X } 对称：{ x | f(x) ∈ X }
      const D = preimageDeck(u.v, T, isCard ? `{ x | ${fmtU(u.v)} = ${lab(X)} }` : `{ x | ${fmtU(u.v)} ∈ ${lab(X)} }`);
      const { got, outside } = restrictToWorld(D, Wd, D.name);
      // 反推的缺口是"解跑出了底板"，不是底板做不了 f：法记成 pre，填的时候只要装得下
      const specs = outside
        ? [{ kind: 'outside', where: outside, law: { t: 'pre', f: u.v, target: T }, lawText: `反推 ${fmtU(u.v)}`, source: T, sourceName: lab(X), world: Wd }]
        : [];
      const text = isCard ? `所有代入 ${fmtU(u.v)} 会得到 ${lab(X)} 的输入` : `代入 ${fmtU(u.v)} 以后落进 ${lab(X)} 的所有输入`;
      return deckResult(got, from, text, `${lab(X)} 反推 ${fmtU(u.v)}`, { W, holes: specs, keepEmpty: true });
    }
    case 'fill':
      return withFill(L, M, Rt, W);
  }
  return fail('这个构造算子还不会用。');
}

// ───────────────────────── 填与手填 ─────────────────────────

// 补不上的缺口：自动填和手填共用同一句解释
function unfillableMsg(h) {
  if (h.tooLarge) return `这个缺口是游戏的边界：${h.name ?? previewDeck(h.where)} 太大，现在的数写不下。`;
  if (h.expr) return `这个缺口补不上：${h.expr} 没有定义，换到任何世界都一样。`;
  return `这个缺口补不上：${h.lawText} 在 ${previewDeck(h.where)} 上没有定义，换到任何世界都一样。`;
}

// 填的目标要满足的条件，写成人话："包含 ℕ 和 负整数、又能做 − 的最小世界"
function fillCond(h) {
  const need = h.kind === 'outside' ? `${h.sourceName} 和 ${h.name ?? previewDeck(h.where, 3)}` : h.sourceName;
  if (h.law.t === 'pre') return `包含 ${need}、又装得下 ${h.lawText} 的全部解的最小世界`;
  if (h.law.t === 'meta') return `包含 ${need} 的最小世界`;
  return `包含 ${need}、又能做 ${h.lawText} 的最小世界`;
}

function withFill(L, M, Rt, W) {
  const H = [L, Rt].find(x => x?.kind === 'hole');
  // 两边都是缺口时，左边那张被填，右边那张当候选（等于它缺的那部分）
  const other = [L, Rt].find(x => x && x !== H);
  if (!H) return fail('「填」的用法：一边放一张缺口卡。另一边空着就自动填；放一个卡组，就用它来填（手填）。');
  const h = H.v;
  const from = [L, M, Rt];
  const whereText = h.name ?? previewDeck(h.where);
  if (h.status === 'retyped') {
    return fail(`这不是这个世界的缺口：${h.lawText} 把 ${h.sourceName} 变成了别的东西${h.name ? `（${h.name}）` : ''}。拿掉底板再做一次，就能直接得到它。`);
  }
  if (h.status === 'unfillable') return fail(unfillableMsg(h));
  if (!other) {
    if (h.status === 'fillable') {
      const c = CAT_BY_ID[h.targetId];
      return ok(catItem(c.id), `这个缺口填成了${catTitle(c)}：图鉴里${fillCond(h)}`, { grade: 'auto', filled: H.id, catId: c.id });
    }
    if (h.expr) return fail(`这个缺口还没有人填过：${h.expr} 现在还写不出来。可以用现有的卡凑一个世界，放在另一边来填。`);
    return fail(`这个缺口还没有人填过：${h.lawText} 在 ${h.sourceName} 上卡在 ${whereText}。可以用现有的卡凑一个世界，放在另一边来填。`);
  }
  if (!isDeckLike(other)) return fail('用来填的要是一个卡组（或另一张缺口）。');
  const K = asDeck(other);
  // (a) 包含出发世界（和越出的部分）
  const base = h.world ?? h.source;
  const escaped = h.kind === 'outside' ? sampleOf(h.where).slice(0, 40) : [];
  const need = [...sampleOf(base).slice(0, 40), ...escaped];
  const missing = need.filter(x => K.has(x) !== true);
  if (missing.length) {
    return fail(`${lab(other)} 没有包住 ${h.sourceName}${h.kind === 'outside' ? ' 和缺的那部分' : ''}：比如 ${missing.slice(0, 3).map(fmtV).join('、')} 不在里面。`);
  }
  // (b) 这条法在候选上封闭：缺口里的值必查，写不出来的结果也算没关住
  const r = lawClosedOn(K, h.law, 40, escaped);
  if (r.escaped.length) {
    const spec = { kind: 'outside', law: h.law, lawText: h.lawText, source: base, sourceName: h.sourceName, where: finiteDeck(r.escaped, ''), world: K };
    const holes = holesFrom([spec], from, W);
    return ok(null, `${lab(other)} 还是关不住 ${h.lawText}：${holeSummary(holes)}。`, { holes });
  }
  if (r.unrep) return fail(`${lab(other)} 里做 ${h.lawText} 还是有写不出来的结果。`);
  // 分档
  const c = matchCatalog(K);
  const item = c ? catItem(c.id) : selfItem(K, from, W);
  if (h.status === 'fillable') {
    const t = CAT_BY_ID[h.targetId];
    if (c && c.id === t.id) {
      return ok(item, `恰到好处：${lab(other)} 正好是图鉴里${fillCond(h)}，${catTitle(t)}`, { grade: 'exact', filled: H.id, catId: c.id });
    }
    // 包住了图鉴目标才叫"多了一块"；更小或者不可比的候选，是比图鉴更紧的答案
    const T = catItem(t.id).v;
    const covers = probesFor(T.type ?? 'q').every(x => T.has(x) !== true || K.has(x) === true);
    if (covers) {
      return ok(item, `填上了，但多了一块：${lab(other)} 关住了 ${h.lawText}，不过图鉴里最小的世界是${catTitle(t)}`, { grade: 'over', filled: H.id, catId: c?.id });
    }
    return ok(item, `比图鉴更紧：${lab(other)} 关住了 ${h.lawText}，而且比图鉴里的${catTitle(t)}还小（或者和它不一样）`, {
      grade: 'tighter',
      filled: H.id,
      catId: c?.id,
      firstFill: true,
    });
  }
  if (h.status === 'frontier') {
    return ok(item, `首次发现：${lab(other)} 关住了 ${h.lawText}，这个缺口以前没有人填过`, { grade: 'frontier', filled: H.id, catId: c?.id, firstFill: true });
  }
  return fail('这个缺口现在不能手填。');
}

// ───────────────────────── 存档 ─────────────────────────

export function itemFromDesc(d, memo = new Map()) {
  if (!d) return null;
  const key = JSON.stringify(d);
  if (memo.has(key)) return memo.get(key);
  let it = null;
  switch (d.k) {
    case 'card': {
      const x = parseVKey(d.x);
      it = x ? cardItem(x) : null;
      break;
    }
    case 'bin':
      it = BIN[d.id] ? binItem(BIN[d.id]) : null;
      break;
    case 'meta':
      it = META_BY_ID[d.id] ? metaItem(META_BY_ID[d.id]) : null;
      break;
    case 'un': {
      const f = parseU(d.f);
      it = f ? unItem(f) : null;
      break;
    }
    case 'deck':
    case 'hole': {
      if (d.cat) {
        it = CAT_BY_ID[d.cat] ? catItem(d.cat) : null;
        break;
      }
      if (!Array.isArray(d.from) || d.from.length !== 3) break;
      const parts = d.from.map(x => (x ? itemFromDesc(x, memo) : null));
      if (d.from.some((x, i) => x && !parts[i])) break;
      const W = d.w ? itemFromDesc(d.w, memo) : null;
      if (d.w && !W) break;
      const r = combine(parts[0], parts[1], parts[2], W);
      if (!r.ok) break;
      if (d.k === 'deck') it = r.item && r.item.kind === 'deck' ? r.item : null;
      else it = r.holes.filter(h => h.v.kind === d.kind)[d.idx] ?? null;
      break;
    }
  }
  memo.set(key, it);
  return it;
}

export const startItems = START_REFS => START_REFS.map(resolveRef);

export { typeLabel, HOLE_KIND };
