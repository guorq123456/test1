// 合成规则：合成台上 [左] [算子] [右] 三个格子，放进去的东西决定会得到什么。

import { OVER } from './math.js';
import {
  BIN,
  MSG_OVER,
  binV,
  isV,
  vkey,
  fmtV,
  parseVKey,
  defOf,
  typeLabel,
  probesFor,
  smallProbesFor,
} from './values.js';
import { applyU, bindLeft, bindRight, compose, fmtU, fnU, invertU, parseU, serU, ukey } from './unary.js';
import {
  closureDeck,
  finiteDeck,
  hash,
  imageDeck,
  interDeck,
  mkDeck,
  orbitDeck,
  pairwiseDeck,
  previewDeck,
  sigOf,
  unionDeck,
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
    const D = c.list
      ? finiteDeck(c.list.map(parseVKey), c.short)
      : mkDeck('cat', c.has, { name: c.short, type: c.type ?? 'q' });
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
    default:
      return it.v.sym;
  }
}

const nest = s => (/\s/.test(s) ? `(${s})` : s);
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
      // 算出来的每张卡都得在 C 里，C 在小探针范围内的卡也都得算出来
      if (C.list) {
        const elems = [...D.elems].sort((x, y) => (vkey(x) < vkey(y) ? -1 : 1));
        const cl = [...C.list].sort((x, y) => (vkey(x) < vkey(y) ? -1 : 1));
        if (sameList(elems, cl)) return c;
        continue;
      }
      if (D.elems.every(x => C.has(x)) && smallProbesFor(type).every(x => !C.has(x) || D.has(x))) return c;
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
    if (probes.every(same)) return c;
  }
  return null;
}

function fingerprint(D) {
  if (D.list) return `f${hash(D.list.map(vkey).join(','))}`;
  if (D.kind === 'approx') return `a${hash(D.elems.map(vkey).sort().join(','))}`;
  return `e${hash(D.type + ':' + sigOf(D, D.approx ? smallProbesFor(D.type) : probesFor(D.type)))}`;
}

// ───────────────────────── 合成 ─────────────────────────

const fail = msg => ({ ok: false, msg });
const ok = (item, text, extra = {}) => ({ ok: true, item, text, ...extra });

function errText(r) {
  if (r === OVER) return MSG_OVER;
  if (r && typeof r === 'object' && r.err) return r.err;
  return '这一步算不出结果。';
}

function deckResult(D, from, text, recipe) {
  const c = matchCatalog(D);
  if (c) {
    const title = c.short === c.name ? `「${c.name}」` : `「${c.name} ${c.short}」`;
    return ok(catItem(c.id), `${text}。这就是${title}！`, { recipe, catId: c.id });
  }
  if (D.list && D.list.length <= 6) D.name = previewDeck(D);
  const item = {
    kind: 'deck',
    v: D,
    id: `d:~${fingerprint(D)}`,
    desc: { k: 'deck', from: from.map(x => (x ? x.desc : null)) },
  };
  const note = D.approx ? '（这个卡组只在一个小范围里算过，内容是近似的。）' : '';
  return ok(item, `${text}。${note}`, { recipe });
}

const asDeck = it => (it.kind === 'deck' ? it.v : finiteDeck([it.v], fmtV(it.v)));
const isSetLike = it => it && (it.kind === 'card' || it.kind === 'deck');

// 在左右两格里找一对 [A, B]，A 的种类在 kindsA 里，B 的种类是 kindB，顺序不限
function pairOf(L, Rt, kindsA, kindB) {
  if (L && Rt) {
    if (kindsA.includes(L.kind) && Rt.kind === kindB) return [L, Rt];
    if (kindsA.includes(Rt.kind) && L.kind === kindB) return [Rt, L];
  }
  return null;
}

const single = (L, Rt) => (L && !Rt ? L : Rt && !L ? Rt : null);

export function combine(L, M, Rt) {
  if (!M) return fail('中间的「算子」格还空着。放一个算子进去：橙色、黄色或紫色的卡。');
  if (M.kind === 'card') {
    // 多项式这种可以当函数用的单卡，放在中间就是一元算子
    if (defOf(M.v).call) return withUn(L, { kind: 'un', v: fnU(M.v) }, Rt);
    return fail('中间的格子只能放算子。单卡和卡组请放在左右两边。');
  }
  if (M.kind === 'deck') return fail('中间的格子只能放算子。单卡和卡组请放在左右两边。');
  if (M.kind === 'bin') return withBin(L, M, Rt);
  if (M.kind === 'un') return withUn(L, M, Rt);
  return withMeta(L, M, Rt);
}

function withBin(L, M, Rt) {
  const b = M.v;
  const k = `${L?.kind ?? '空'}|${Rt?.kind ?? '空'}`;
  switch (k) {
    case 'card|card': {
      const r = binV(b.id, L.v, Rt.v);
      if (!isV(r)) return fail(errText(r));
      return ok(cardItem(r), `${fmtV(L.v)} ${b.sym} ${fmtV(Rt.v)} = ${fmtV(r)}`);
    }
    case '空|card': {
      const r = bindRight(b, Rt.v);
      if (r.err) return fail(r.err);
      return ok(unItem(r.f), `左边空着，就是变量 x。x ${b.sym} ${fmtV(Rt.v)} 成了一元算子 ${fmtU(r.f)}`);
    }
    case 'card|空': {
      const r = bindLeft(L.v, b);
      if (r.err) return fail(r.err);
      return ok(unItem(r.f), `右边空着，就是变量 x。${fmtV(L.v)} ${b.sym} x 成了一元算子 ${fmtU(r.f)}`);
    }
    case 'deck|card': {
      const r = bindRight(b, Rt.v);
      if (r.err) return fail(r.err);
      const D = imageDeck(L.v, r.f, `{ ${fmtU(r.f)} | x ∈ ${lab(L)} }`);
      return deckResult(D, [L, M, Rt], `${lab(L)} 里的每张卡都做 ${fmtU(r.f)}`, `${lab(L)} ${b.sym} ${fmtV(Rt.v)}`);
    }
    case 'card|deck': {
      const r = bindLeft(L.v, b);
      if (r.err) return fail(r.err);
      const D = imageDeck(Rt.v, r.f, `{ ${fmtU(r.f)} | x ∈ ${lab(Rt)} }`);
      return deckResult(D, [L, M, Rt], `${lab(Rt)} 里的每张卡 x 都变成 ${fmtU(r.f)}`, `${fmtV(L.v)} ${b.sym} ${lab(Rt)}`);
    }
    case 'deck|deck': {
      const name = `${lab(L)} ${b.sym} ${lab(Rt)}`;
      const D = pairwiseDeck(L.v, b, Rt.v, name);
      if (D.list && D.list.length === 0 && !(L.v.list && L.v.list.length === 0) && !(Rt.v.list && Rt.v.list.length === 0)) {
        return fail(`${lab(L)} 和 ${lab(Rt)} 里的卡两两做 ${b.sym} 都算不出结果。`);
      }
      return deckResult(D, [L, M, Rt], `从 ${lab(L)} 和 ${lab(Rt)} 里各取一张做 ${b.sym}，收集所有结果`, name);
    }
    case '空|空':
      return fail(`「${b.name}」需要输入：两边都放单卡，算出一张新单卡；只放一边，得到一元算子。`);
    case 'deck|空':
    case '空|deck':
      return fail('卡组和二元算子之间还差一个输入：另一边放一张单卡或一个卡组。');
  }
  return fail(`「${b.name}」两边要放单卡或卡组。想改造算子本身，请用紫色的构造算子。`);
}

function withUn(L, M, Rt) {
  const f = M.v;
  const ins = [L, Rt].filter(Boolean);
  if (ins.length === 0) return fail(`一元算子 ${fmtU(f)} 需要一个输入：在左边或右边放一张单卡或一个卡组。`);
  if (ins.length === 2) return fail('一元算子只吃一个输入，请把另一边清空。想把两个一元算子接起来，用构造算子「复合」。');
  const X = ins[0];
  if (X.kind === 'card') {
    const y = applyU(f, X.v);
    if (!isV(y)) {
      if (y === OVER || (y && y.err)) return fail(errText(y));
      return fail(`把 x = ${fmtV(X.v)} 代入 ${fmtU(f)} 算不出结果（没有定义，或者不是有理数）。`);
    }
    return ok(cardItem(y), `把 x = ${fmtV(X.v)} 代入 ${fmtU(f)}，得到 ${fmtV(y)}`);
  }
  if (X.kind === 'deck') {
    const D = imageDeck(X.v, f, `{ ${fmtU(f)} | x ∈ ${lab(X)} }`);
    if (D.list && D.list.length === 0 && !(X.v.list && X.v.list.length === 0)) {
      return fail(`${lab(X)} 里没有一张卡能做 ${fmtU(f)}。`);
    }
    return deckResult(D, [L, M, Rt], `${lab(X)} 里的每张卡都做 ${fmtU(f)}`, `${lab(X)} 经 ${fmtU(f)}`);
  }
  return fail('一元算子的输入要是单卡或卡组。想改造算子，请用紫色的构造算子，比如「复合」「逆」。');
}

const EXTEND = {
  add: { to: 'mul', text: '反复做加法就是乘法：3 × 4 = 4 + 4 + 4' },
  mul: { to: 'pow', text: '反复做乘法就是乘方：2⁴ = 2 × 2 × 2 × 2' },
  sub: { to: 'mod', text: '反复减去同一个数，直到减不动为止，剩下的就是余数：17 mod 5 = 2' },
};
const INVERSE = {
  add: { to: 'sub', text: '加法倒过来做就是减法：a + b = c，那么 c − b = a' },
  sub: { to: 'add', text: '减法倒过来做就是加法' },
  mul: { to: 'div', text: '乘法倒过来做就是除法：a × b = c，那么 c ÷ b = a' },
  div: { to: 'mul', text: '除法倒过来做就是乘法' },
};

function withMeta(L, M, Rt) {
  const m = M.v;
  switch (m.id) {
    case 'extend': {
      const p = pairOf(L, Rt, ['card'], 'un');
      if (p) {
        const [c, u] = p;
        const name = `${fmtV(c.v)} ⟳ ${nest(fmtU(u.v))}`;
        const D = orbitDeck(c.v, u.v, name);
        const steps = previewDeck(D);
        return deckResult(D, [L, M, Rt], `从 ${fmtV(c.v)} 出发，一直做 ${fmtU(u.v)}：${steps}`, `${fmtV(c.v)} 延展 ${fmtU(u.v)}`);
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
      const p = pairOf(L, Rt, ['card', 'deck'], 'bin');
      if (!p) return fail('「封闭」的用法：一边放单卡或卡组作为起点，另一边放二元算子作为组合方式。');
      const [X, b] = p;
      const D = closureDeck(asDeck(X), b.v, `⟨${label(X)} | ${b.v.sym}⟩`);
      return deckResult(
        D,
        [L, M, Rt],
        `从 ${lab(X)} 出发，用 ${b.v.sym} 反复组合，直到得不到新卡`,
        `${lab(X)} 在 ${b.v.sym} 下封闭`,
      );
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
          return fail(`${fmtU(one.v)} 没有逆：不同的输入会得到同一个结果，没法倒推回去。`);
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
        return fail(`「${m.name}」的两边都要放卡组。单卡会被当成只有一张卡的卡组。`);
      }
      const A = asDeck(L);
      const B = asDeck(Rt);
      const name = `${lab(L)} ${m.sym} ${lab(Rt)}`;
      const D = m.id === 'union' ? unionDeck(A, B, name) : interDeck(A, B, name);
      const text = m.id === 'union' ? `把 ${lab(L)} 和 ${lab(Rt)} 合在一起` : `只留下 ${lab(L)} 和 ${lab(Rt)} 都有的卡`;
      return deckResult(D, [L, M, Rt], text, name);
    }
  }
  return fail('这个构造算子还不会用。');
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
    case 'deck': {
      if (d.cat) {
        it = CAT_BY_ID[d.cat] ? catItem(d.cat) : null;
        break;
      }
      if (!Array.isArray(d.from) || d.from.length !== 3) break;
      const parts = d.from.map(x => (x ? itemFromDesc(x, memo) : null));
      if (d.from.some((x, i) => x && !parts[i])) break;
      const r = combine(parts[0], parts[1], parts[2]);
      it = r.ok && r.item.kind === 'deck' ? r.item : null;
      break;
    }
  }
  memo.set(key, it);
  return it;
}

export const startItems = START_REFS => START_REFS.map(resolveRef);

export { typeLabel };
