// 卡组：用"成员判断" has(x) 表示的集合。
//
// 每个卡组有：
//   type    成员的类型：'q'、'mod:12'、'poly'、'vec'、'mat'、'qty'……混合时是 'set'
//   list    有限卡组的成员列表（有的话）
//   elems   在视野里算出来的成员（近似卡组，approx = true）
//   has(x)  true / false / null（超出范围判断不了）
//
// 像"封闭"这种没法精确推算的操作，会在类型的视野（window）里真的算一遍。

import { R, isR, rkey, cmp, height, eq, eqR, isInt, toNum, sub, div, ipow, ONE, OVER, uniqR } from './math.js';
import {
  isV,
  vkey,
  fmtV,
  uniqV,
  cmpV,
  sizeV,
  subtypeOf,
  windowFor,
  binV,
  WINDOW,
  WIN_H,
  sizeCapFor,
  eqV,
} from './values.js';
import { applyU, preU, invertU, isQStructural } from './unary.js';

// 三值逻辑的"或"和"且"：null 表示不知道
const or3 = (a, b) => (a === true || b === true ? true : a === null || b === null ? null : false);
const and3 = (a, b) => (a === false || b === false ? false : a === null || b === null ? null : true);

// 展示有理数卡组内容时从这里挑"最简单"的几个数
const DISPLAY_POOL = (() => {
  const xs = [...WINDOW];
  for (let n = -400; n <= 400; n++) xs.push(R(n));
  for (let k = 0; k <= 16; k++) xs.push(R(2 ** k), R(1, 2 ** k));
  return uniqR(xs).sort((x, y) => height(x) - height(y) || cmp(x, y));
})();

// has(x) 返回 true / false，或者 null（表示"超出游戏的数字范围，判断不了"）
export function mkDeck(kind, has, extra = {}) {
  const cache = new Map();
  return {
    kind,
    approx: false,
    type: 'set',
    ...extra,
    has(x) {
      if (!isV(x)) return false;
      const k = vkey(x);
      if (cache.has(k)) return cache.get(k);
      const r = has(x);
      const v = r === null ? null : !!r;
      cache.set(k, v);
      return v;
    },
  };
}

function sameType(xs) {
  const t = subtypeOf(xs[0]);
  return xs.every(x => subtypeOf(x) === t) ? t : 'set';
}

export function finiteDeck(xs, name) {
  const list = uniqV(xs).sort(cmpV);
  const keys = new Set(list.map(vkey));
  const type = list.length ? sameType(list) : 'q';
  return mkDeck('finite', x => keys.has(vkey(x)), { list, name, type });
}

function approxDeck(elems, name, type) {
  const m = new Map();
  for (const x of elems) if (isV(x)) m.set(vkey(x), x);
  const list = [...m.values()];
  return mkDeck('approx', x => m.has(vkey(x)), {
    name,
    approx: true,
    elems: list,
    type: type ?? (list.length ? sameType(list) : 'set'),
  });
}

// 卡组的代表性成员：有限卡组是全部，其他的是视野里的成员
export function sampleOf(D) {
  if (D.list) return D.list;
  if (D.elems) return D.elems;
  if (D.sample) return D.sample();
  return windowFor(D.type).filter(x => D.has(x) === true);
}

// 对卡组里的每张卡做一元算子 f
export function imageDeck(D, f, name) {
  if (D.list) return finiteDeck(D.list.map(x => applyU(f, x)).filter(isV), name);
  if (D.type === 'q' && isQStructural(f)) {
    return mkDeck(
      'image',
      y => {
        if (!isR(y)) return false;
        const p = preU(f, y);
        if (p.pred) return WINDOW.some(x => p.pred(x) && D.has(x) === true);
        const hits = p.list.map(x => D.has(x));
        if (hits.includes(true)) return true;
        return p.unknown || hits.includes(null) ? null : false;
      },
      { name, type: 'q', approx: D.approx },
    );
  }
  const sample = sampleOf(D);
  const outs = uniqV(sample.map(x => applyU(f, x)));
  if (!outs.length) return finiteDeck([], name);
  const type = sameType(outs);
  // f 可逆时可以精确判断：y 在像里 ⇔ f⁻¹(y) 在 D 里
  const g = invertU(f);
  const roundTrips =
    g &&
    !D.approx &&
    sample.slice(0, 16).every(x => {
      const y = applyU(f, x);
      return !isV(y) || eqV(applyU(g, y), x);
    });
  if (roundTrips) {
    return mkDeck(
      'image',
      y => {
        const x = applyU(g, y);
        return isV(x) && eqV(applyU(f, x), y) ? D.has(x) : false;
      },
      { name, type },
    );
  }
  return approxDeck(outs, name, type);
}

export function unionDeck(A, B, name) {
  if (A.list && B.list) return finiteDeck([...A.list, ...B.list], name);
  const type = A.type === B.type ? A.type : 'set';
  return mkDeck('union', x => or3(A.has(x), B.has(x)), {
    name,
    type,
    approx: A.approx || B.approx,
    sample: () => uniqV([...sampleOf(A), ...sampleOf(B)]),
  });
}

export function interDeck(A, B, name) {
  if (A.list) return finiteDeck(A.list.filter(x => B.has(x) === true), name);
  if (B.list) return finiteDeck(B.list.filter(x => A.has(x) === true), name);
  const type = A.type === B.type ? A.type : 'set';
  return mkDeck('inter', x => and3(A.has(x), B.has(x)), {
    name,
    type,
    approx: A.approx || B.approx,
    sample: () => sampleOf(A).filter(x => B.has(x) === true),
  });
}

// a·x + b 的轨道 {c, f(c), f(f(c)), …} 的精确成员判断（有理数）
function affOrbitHas(c, f, y) {
  if (!isR(y)) return false;
  const { a, b } = f;
  if (eq(a, ONE)) {
    const t = sub(y, c);
    if (!isR(t)) return false;
    const k = div(t, b);
    return isR(k) && isInt(k) && k.n >= 0;
  }
  // 不动点 p = b / (1 − a)，于是 y − p = aᵏ · (c − p)
  const oneMinusA = sub(ONE, a);
  if (!isR(oneMinusA)) return false;
  const p = div(b, oneMinusA);
  if (!isR(p)) return false;
  const u = sub(y, p);
  const w = sub(c, p);
  if (!isR(u) || !isR(w) || w.n === 0) return false;
  const r = div(u, w);
  if (!isR(r)) return false;
  if (eq(r, ONE)) return true;
  const la = Math.log(Math.abs(toNum(a)));
  if (la === 0 || r.n === 0) return false;
  const k = Math.round(Math.log(Math.abs(toNum(r))) / la);
  if (!(k >= 0) || k > 200) return false;
  return eqR(ipow(a, k), r);
}

const ORBIT_STEPS = 400;

// 延展：从 c 出发反复做 f
export function orbitDeck(c, f, name) {
  const seq = [c];
  const seen = new Set([vkey(c)]);
  let x = c;
  let open = true;
  let overflow = false;
  for (let i = 0; i < ORBIT_STEPS; i++) {
    const y = applyU(f, x);
    if (!isV(y)) {
      open = false;
      overflow = y === OVER;
      break;
    }
    const k = vkey(y);
    if (seen.has(k)) {
      open = false;
      break;
    }
    seen.add(k);
    seq.push(y);
    x = y;
  }
  // 走进了循环，或者走到没有定义的地方停下：有限卡组
  if (!open && !overflow) return finiteDeck(seq, name);
  const type = sameType(seq);
  const extra = { name, seq: seq.slice(0, 6), type };
  if (isR(c) && f.t === 'aff' && type === 'q') return mkDeck('orbit', y => affOrbitHas(c, f, y), extra);
  // 其他算子：记下走过的每一步。走满步数还没停就标成近似。
  return mkDeck('orbit', y => seen.has(vkey(y)), { ...extra, approx: open, elems: seq });
}

const OP_BUDGET = 1_500_000;

// 封闭：从 D 出发，用 b 反复组合（在视野里算）
export function closureDeck(D, b, name) {
  const fin = !!D.list;
  const seeds = sampleOf(D);
  const cap = sizeCapFor(D.type);
  const hmax = fin ? Math.min(2000, Math.max(cap, 2 * Math.max(1, ...seeds.map(sizeV)))) : cap;
  const all = new Map(seeds.map(x => [vkey(x), x]));
  let frontier = [...all.values()];
  let dropped = false;
  let ops = 0;
  let rounds = 0;
  let stop = false;
  while (frontier.length && rounds < 12 && !stop) {
    rounds++;
    const cur = [...all.values()];
    const fresh = [];
    const tryAdd = z => {
      if (!isV(z)) {
        if (z === OVER) dropped = true;
        return;
      }
      if (sizeV(z) > hmax) {
        dropped = true;
        return;
      }
      const k = vkey(z);
      if (!all.has(k)) {
        all.set(k, z);
        fresh.push(z);
      }
    };
    for (const x of frontier) {
      for (const y of cur) {
        tryAdd(binV(b.id, x, y));
        if (!b.comm) tryAdd(binV(b.id, y, x));
      }
      ops += cur.length * 2;
      if (ops > OP_BUDGET || all.size > 4000) {
        dropped = true;
        stop = true;
        break;
      }
    }
    frontier = fresh;
  }
  if (frontier.length) dropped = true;
  if (fin && !dropped) return finiteDeck([...all.values()], name);
  return approxDeck([...all.values()], name);
}

// 两个卡组两两运算：{a ∘ b | a ∈ A, b ∈ B}
export function pairwiseDeck(A, b, B, name) {
  const fin = !!(A.list && B.list);
  const sa = sampleOf(A);
  const sb = sampleOf(B);
  const out = new Map();
  let cap = null;
  for (const x of sa) {
    for (const y of sb) {
      const z = binV(b.id, x, y);
      if (!isV(z)) continue;
      if (!fin) {
        if (cap === null) cap = sizeCapFor(subtypeOf(z));
        if (sizeV(z) > cap) continue;
      }
      out.set(vkey(z), z);
    }
  }
  if (fin) return finiteDeck([...out.values()], name);
  return approxDeck([...out.values()], name);
}

export function sigOf(D, probes) {
  return probes.map(x => ({ true: '1', false: '0', null: '?' })[D.has(x)]).join('');
}

// 卡组内容预览，比如 "{0, 2, 4, 6, 8, …}"
export function previewDeck(D, max = 6) {
  if (D.list) {
    const xs = D.list;
    if (!xs.length) return '{ }';
    if (xs.length <= max + 1) return `{${xs.map(fmtV).join(', ')}}`;
    return `{${xs.slice(0, max).map(fmtV).join(', ')}, …}`;
  }
  if (D.seq && D.seq.length >= 2) return `{${D.seq.slice(0, 5).map(fmtV).join(', ')}, …}`;
  if (D.type !== 'q') {
    const pool = D.elems ?? [...windowFor(D.type)].sort((x, y) => sizeV(x) - sizeV(y) || cmpV(x, y));
    const members = [];
    let more = false;
    for (const x of pool) {
      if (D.has(x) !== true) continue;
      if (members.length >= max) {
        more = true;
        break;
      }
      members.push(x);
    }
    if (!members.length) return D.approx ? '{ …（视野外） }' : '{ }';
    return `{${members.map(fmtV).join(', ')}${more ? ', …' : ''}}`;
  }
  const members = [];
  for (const x of DISPLAY_POOL) {
    if (D.has(x)) {
      members.push(x);
      if (members.length >= max) break;
    }
  }
  if (!members.length) return D.approx ? '{ …（范围外） }' : '{ }';
  members.sort(cmp);
  const lo = members[0];
  const hi = members[members.length - 1];
  const moreLo = DISPLAY_POOL.some(x => cmp(x, lo) < 0 && D.has(x));
  const moreHi = DISPLAY_POOL.some(x => cmp(x, hi) > 0 && D.has(x));
  return `{${moreLo ? '…, ' : ''}${members.map(fmtV).join(', ')}${moreHi ? ', …' : ''}}`;
}

// 有限卡组在 + 和 × 下是不是群（封闭、单位元、逆元）。太大或无限时返回 null。
export function groupInfo(D, ops = ['add', 'mul']) {
  if (!D.list || D.list.length === 0 || D.list.length > 64) return null;
  const xs = D.list;
  const keys = new Set(xs.map(vkey));
  const out = {};
  for (const op of ops) {
    const table = new Map();
    let closed = true;
    for (const a of xs) {
      for (const b of xs) {
        const z = binV(op, a, b);
        if (!isV(z) || !keys.has(vkey(z))) {
          closed = false;
          break;
        }
        table.set(`${vkey(a)}|${vkey(b)}`, vkey(z));
      }
      if (!closed) break;
    }
    let identity = null;
    if (closed) {
      identity =
        xs.find(e => xs.every(a => table.get(`${vkey(e)}|${vkey(a)}`) === vkey(a) && table.get(`${vkey(a)}|${vkey(e)}`) === vkey(a))) ??
        null;
    }
    let inverses = false;
    if (identity) {
      const ek = vkey(identity);
      inverses = xs.every(a => xs.some(b => table.get(`${vkey(a)}|${vkey(b)}`) === ek && table.get(`${vkey(b)}|${vkey(a)}`) === ek));
    }
    out[op] = { closed, identity, inverses, group: closed && !!identity && inverses };
  }
  return out;
}

// 简单的字符串哈希，用来给未命名卡组起编号
export function hash(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(36);
}

export { WIN_H, WINDOW };
