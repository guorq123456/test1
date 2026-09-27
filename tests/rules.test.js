import test from 'node:test';
import assert from 'node:assert/strict';

import { CATALOG, START } from '../src/catalog.js';
import { CATALOG_ALL, CHAPTERS_ALL, WALKTHROUGHS } from '../src/content.js';
import { combine, itemFromDesc, resolveRef, recipeText } from '../src/rules.js';
import { R, ONE, TWO, ZERO, NEG1 } from '../src/math.js';
import { fmtU, compose, invertU, aff, powU } from '../src/unary.js';
import { previewDeck, groupInfo } from '../src/decks.js';
import { checkCatalog, elementaryHand, makeHand, ELEM_STEPS } from './helpers.js';

test('图鉴里每一种做法都能真的合成出对应的卡组；每个卡组至少两种做法，至少一种用到别的卡组', () => {
  checkCatalog(CATALOG_ALL);
});

test('图鉴条目的 id 不重复，章节都存在', () => {
  const ids = new Set();
  const chapters = new Set(CHAPTERS_ALL.map(c => c.id));
  for (const c of CATALOG_ALL) {
    assert.ok(!ids.has(c.id), `重复的卡组 id ${c.id}`);
    ids.add(c.id);
    assert.ok(chapters.has(c.ch), `${c.name} 的章节 ${c.ch} 不存在`);
  }
});

test('从开局手牌出发，只用已经拿到的卡，就能集齐全部入门卡组', () => {
  const hand = makeHand(START).walk(ELEM_STEPS);
  for (const c of CATALOG) assert.ok(hand.has(`d:${c.id}`), `没有集齐 ${c.name}`);
});

test('集齐初等篇之后，按各章路线能集齐全部高等篇卡组', () => {
  const hand = elementaryHand();
  for (const { chapter, steps } of WALKTHROUGHS) {
    if (chapter.unlock) assert.ok(hand.has(chapter.unlock.when), `第 ${chapter.id} 章的解锁条件 ${chapter.unlock.when} 还没满足`);
    hand.walk(steps);
    for (const c of CATALOG_ALL.filter(c => c.ch === chapter.id)) {
      assert.ok(hand.has(`d:${c.id}`), `第 ${chapter.id} 章路线没有集齐 ${c.name}`);
    }
  }
});

test('算子能化简、求逆，公式显示正确', () => {
  const succ = aff(ONE, ONE);
  assert.equal(fmtU(compose(succ, succ)), 'x + 2');
  assert.equal(fmtU(compose(aff(TWO, ZERO), succ)), '2x + 1');
  assert.equal(fmtU(compose(succ, powU(TWO))), '(x + 1)²');
  assert.equal(fmtU(compose(powU(TWO), succ)), 'x² + 1');
  assert.equal(fmtU(invertU(succ)), 'x − 1');
  assert.equal(fmtU(invertU(powU(TWO))), '√x');
  assert.equal(fmtU(aff(NEG1, ONE)), '1 − x');
  assert.equal(fmtU(aff(R(1, 2), ZERO)), 'x/2');
  assert.equal(invertU(aff(ZERO, ONE)), null);

  const three = resolveRef('c:3');
  const div = resolveRef('b:div');
  assert.equal(fmtU(combine(three, div, null).item.v), '3/x');
});

test('单卡运算', () => {
  const c = ref => resolveRef(ref);
  assert.equal(combine(c('c:1'), c('b:div'), c('c:3')).item.id, 'c:1/3');
  assert.equal(combine(c('c:4'), c('b:pow'), c('c:1/2')).item.id, 'c:2');
  assert.equal(combine(c('c:2'), c('b:pow'), c('c:-2')).item.id, 'c:1/4');
  // 算不出的值不再是失败，而是分岔：得到为空，带一张缺口
  const hole = (res, kind) => res.ok && res.item === null && res.holes.length === 1 && res.holes[0].v.kind === kind;
  assert.ok(hole(combine(c('c:1'), c('b:div'), c('c:0')), 'undefined'));
  assert.ok(hole(combine(c('c:2'), c('b:pow'), c('c:1/2')), 'unrepresentable'));
  assert.ok(hole(combine(c('c:10'), c('b:pow'), c('c:9')), 'unrepresentable'));
});

test('图鉴外的卡组会成为未命名卡组，并且不会被误认', () => {
  const two = resolveRef('c:2');
  const plus2 = combine(null, resolveRef('b:add'), two).item;
  const evensUp = combine(resolveRef('c:0'), resolveRef('m:extend'), plus2);
  assert.ok(evensUp.ok);
  assert.ok(evensUp.item.id.startsWith('d:~'));
  assert.equal(previewDeck(evensUp.item.v), '{0, 2, 4, 6, 8, …}');

  // (1/7)ℤ 在小范围里看起来和 ℤ 很像，但不能认成 ℤ
  const seventh = resolveRef('c:1/7');
  const r = combine(seventh, resolveRef('m:closure'), resolveRef('b:sub'));
  assert.ok(r.ok);
  assert.notEqual(r.item.id, 'd:Z');

  // 两张单卡取并：有限卡组，名字就是元素
  const pair = combine(resolveRef('c:1'), resolveRef('m:union'), resolveRef('c:3'));
  assert.equal(pair.item.v.name, '{1, 3}');
});

test('有限卡组能自动判断是不是群', () => {
  const sign = resolveRef('d:Sign').v;
  const g = groupInfo(sign);
  assert.equal(g.mul.group, true);
  assert.equal(g.add.group, false);
  const pair = combine(resolveRef('c:1'), resolveRef('m:union'), resolveRef('c:3')).item.v;
  assert.equal(groupInfo(pair).add.closed, false);
});

test('存档描述可以重建出同一张卡', () => {
  const plus2 = combine(null, resolveRef('b:add'), resolveRef('c:2')).item;
  const deck = combine(resolveRef('c:0'), resolveRef('m:extend'), plus2).item;
  const again = itemFromDesc(JSON.parse(JSON.stringify(deck.desc)));
  assert.equal(again.id, deck.id);
  const cat = itemFromDesc({ k: 'deck', cat: 'Q' });
  assert.equal(cat.id, 'd:Q');
});

test('做法文字', () => {
  assert.equal(recipeText(['c:0', 'm:extend', 'u:succ']), '0 延展 x + 1');
  assert.equal(recipeText(['d:N', 'm:union', 'd:NegZ']), 'ℕ ∪ 负整数');
  assert.equal(recipeText(['d:Z', 'u:sq', null]), 'ℤ 经 x²');
});

// ───────────── 审查回归：探针之外的差别、定义域、溢出 ─────────────

const C = (a, b, c, w = null) => combine(a, b, c, w);
const rr = resolveRef;
const isUnnamed = res => res.ok && res.item.id.startsWith('d:~');

test('形状相似但不同的卡组不会被认成图鉴卡组', () => {
  const x1 = C(null, rr('b:add'), rr('c:1')).item;
  const x2 = C(null, rr('b:add'), rr('c:2')).item;
  assert.ok(isUnnamed(C(rr('c:-1025'), rr('m:extend'), x1)), '−1025 ⟳ x+1 不是 ℤ');
  assert.ok(isUnnamed(C(rr('c:-5000'), rr('m:extend'), x2)), '−5000 ⟳ x+2 不是偶数');
  assert.equal(C(rr('c:0'), rr('m:extend'), x1).item.id, 'd:N');
  assert.ok(isUnnamed(C(rr('d:Z'), rr('b:add'), rr('c:1/13'))), 'ℤ + 1/13 不是空集');
  assert.ok(isUnnamed(C(rr('c:7/11'), rr('m:extend'), x1)), '7/11 ⟳ x+1 不是空集');
  assert.ok(isUnnamed(C(rr('d:N'), rr('m:union'), rr('c:-5000'))), 'ℕ ∪ {−5000} 不是 ℕ');
  assert.ok(isUnnamed(C(rr('d:Z'), rr('m:union'), rr('c:1/13'))), 'ℤ ∪ {1/13} 不是 ℤ');
  const A = C(rr('c:0'), rr('m:union'), rr('c:1/21')).item;
  assert.ok(isUnnamed(C(A, rr('b:add'), rr('d:Z'))), '{0, 1/21} + ℤ 不是 ℤ');
  assert.equal(C(rr('d:N'), rr('b:add'), rr('d:Z')).item.id, 'd:Z');
  // 混合类型的自造卡组各有各的 id；不同类型的交是空集
  const u1 = C(rr('d:N'), rr('m:union'), rr('d:Len')).item.id;
  const u2 = C(rr('d:Z'), rr('m:union'), rr('d:Z12')).item.id;
  assert.notEqual(u1, u2);
  assert.equal(C(rr('d:Qp'), rr('m:inter'), rr('d:Len')).item.id, 'd:Empty');
});

test('数学上相同的卡组能被认出来：偶数 ÷ 偶数 = ℚ，含空集的两两运算是空集', () => {
  assert.equal(C(rr('d:Even'), rr('b:div'), rr('d:Even')).item.id, 'd:Q');
  assert.equal(C(rr('d:N'), rr('b:div'), rr('d:Even')).item.id, 'd:Q');
  assert.equal(C(rr('d:Even'), rr('m:closure'), rr('b:div')).item.id, 'd:Q');
  assert.equal(C(rr('d:Z'), rr('b:add'), rr('d:Empty')).item.id, 'd:Empty');
  assert.equal(C(rr('d:Empty'), rr('b:mul'), rr('d:Q')).item.id, 'd:Empty');
});

test('复合的化简不放过定义域外的输入', () => {
  const lg = C(rr('u:log2'), rr('m:compose'), rr('u:exp2'));
  assert.ok(lg.ok);
  assert.notEqual(lg.item.id, 'u:aff(1,0)');
  assert.equal(C(rr('d:Z'), lg.item, null).item.id, 'd:P2', 'ℤ 经 2^(log₂x) 是 2ⁿ');
  const r3 = C(rr('c:3'), lg.item, null);
  assert.ok(r3.ok && r3.item === null && r3.holes[0].v.kind === 'unrepresentable');
  const inv2 = C(rr('u:recip'), rr('m:compose'), rr('u:recip')).item;
  const r0 = C(rr('c:0'), inv2, null);
  assert.ok(r0.ok && r0.item === null && r0.holes[0].v.kind === 'undefined', '1/(1/0) 没有定义');
});

test('视野外的卡组做常数算子、(−1)ˣ 不会被认成空集', () => {
  const x1 = C(null, rr('b:add'), rr('c:1')).item;
  const far = C(rr('c:1000'), rr('m:extend'), x1).item;
  const times0 = C(null, rr('b:mul'), rr('c:0')).item;
  const z = C(far, times0, null);
  assert.ok(z.ok && z.item.id !== 'd:Empty' && z.item.v.has(R(0)) === true);
  assert.equal(C(far, rr('u:sign'), null).item.id, 'd:Sign');
  assert.equal(C(rr('d:Z'), rr('u:sign'), null).item.id, 'd:Sign');
});

test('绑定算子的逆：不可逆的 c 没有逆，矩阵的 c ÷ x 不是自己的逆', () => {
  assert.equal(C(C(null, rr('b:mul'), rr('c:[2]12')).item, rr('m:inverse'), null).ok, false);
  const shear = C(C(rr('c:m:1,1,0,1'), rr('b:div'), null).item, rr('m:inverse'), null);
  assert.ok(shear.ok && shear.item.id !== 'u:bind(div,l,m:1,1,0,1)');
  assert.equal(C(C(rr('c:[5]12'), rr('b:div'), null).item, rr('m:inverse'), null).item.id, 'u:bind(div,l,[5]12)');
  assert.equal(C(C(null, rr('b:mul'), rr('c:m:1,2,3,4')).item, rr('m:inverse'), null).item.id, 'u:bind(div,r,m:1,2,3,4)');
});

test('溢出与边界：溢出的成员不会被悄悄丢掉；轨道末尾、大分母指数', () => {
  const big = C(rr('d:Sign'), rr('m:union'), rr('c:5000000')).item;
  assert.ok(isUnnamed(C(big, rr('u:cube'), null)), '{±1, 5000000} 经 x³ 不是 {±1}');
  const dbl = C(null, rr('b:mul'), rr('c:2')).item;
  assert.equal(C(rr('c:1/2'), rr('m:extend'), dbl).item.v.has(R(8388608)), true);
  assert.equal(C(rr('c:1'), rr('b:pow'), rr('c:1/13')).item.id, 'c:1');
  assert.equal(C(rr('c:0'), rr('b:pow'), rr('c:1/13')).item.id, 'c:0');
  const r13 = C(rr('c:8192'), rr('b:pow'), rr('c:1/13'));
  assert.ok(r13.ok && r13.item === null && r13.holes[0].v.kind === 'unrepresentable');
  assert.match(r13.text, /分母/);
  const m8 = C(rr('c:-8'), rr('b:pow'), null).item;
  assert.equal(C(rr('d:Unit'), m8, null).item.v.has(R(-2)), true, '(−8)^(1/3) = −2 在像里');
});

test('多项式当算子用的卡组能存档重建；预览和提示', () => {
  const fdeck = C(rr('d:Even'), rr('c:p:1,0,0'), null);
  assert.ok(fdeck.ok);
  assert.equal(itemFromDesc(JSON.parse(JSON.stringify(fdeck.item.desc)))?.id, fdeck.item.id);
  assert.match(previewDeck(C(rr('d:Z'), rr('u:recip'), null).item.v), /…/);
  const cl = C(rr('c:300'), rr('m:closure'), rr('b:mul'));
  assert.match(previewDeck(cl.item.v), /…/);
  assert.match(cl.text, /超出/);
  assert.match(C(rr('c:[3]12'), rr('b:add'), rr('c:q:1|1,0,0')).msg, /模 12 和 长度/);
  assert.match(C(null, rr('b:mod'), rr('c:1/2')).msg, /不小于 2 的整数/);
});

// ───────────── v0.3 第 1 步：缺口、分岔、填、反推 ─────────────

const holeOf = (res, kind) => res.holes.find(h => h.v.kind === kind);

test('分岔：得到 + 缺口，没有底板时所有做法不变', () => {
  const N = rr('d:N');
  // 没有底板：ℕ − ℕ 就是 ℤ，和以前一样
  assert.equal(C(N, rr('b:sub'), N).item.id, 'd:Z');
  // 有底板：得到 ℕ，缺口是负整数，可以填成 ℤ
  const r = C(N, rr('b:sub'), N, N);
  assert.ok(r.ok);
  assert.equal(r.item.id, 'd:N');
  const h = holeOf(r, 'outside');
  assert.ok(h, '应该有越出世界的缺口');
  assert.equal(h.v.name, '负整数');
  assert.equal(h.v.status, 'fillable');
  assert.equal(h.v.targetId, 'Z');
  // 守恒：越出的部分和底板不相交
  for (const x of [R(-1), R(-5), R(-20)]) assert.equal(h.v.where.has(x), true);
  for (const x of [R(0), R(3)]) assert.equal(h.v.where.has(x), false);
  // 值级：1 − 2 在 ℕ 里
  const v = C(rr('c:1'), rr('b:sub'), rr('c:2'), N);
  assert.ok(v.ok && v.item === null && holeOf(v, 'outside').v.targetId === 'Z');
  // 没有定义 / 表示不了
  const zero = C(rr('d:Z'), rr('u:recip'), null);
  assert.ok(zero.item.id.startsWith('d:~'));
  assert.equal(holeOf(zero, 'undefined').v.status, 'unfillable');
  const root = C(N, rr('u:sqrt'), null);
  assert.equal(root.item.id, 'd:N', '完全平方数开方正好得到 ℕ');
  assert.equal(holeOf(root, 'unrepresentable').v.status, 'frontier');
  // ℤ ÷ ℤ 在 ℤ 里：两种缺口同时出现
  const dv = C(rr('d:Z'), rr('b:div'), rr('d:Z'), rr('d:Z'));
  assert.equal(dv.item.id, 'd:Z');
  assert.equal(holeOf(dv, 'undefined').v.status, 'unfillable');
  assert.equal(holeOf(dv, 'outside').v.targetId, 'Q');
  // 延展和封闭也会分岔
  const orb = C(rr('c:3'), rr('m:extend'), rr('u:pred'), N);
  assert.equal(previewDeck(orb.item.v), '{0, 1, 2, 3}');
  assert.equal(holeOf(orb, 'outside').v.targetId, 'Z');
  const cl = C(rr('c:2'), rr('m:closure'), rr('b:div'), rr('d:Z'));
  assert.equal(holeOf(cl, 'outside').v.targetId, 'Q');
});

test('缺口卡当材料；填与手填的三档', () => {
  const N = rr('d:N');
  const h = holeOf(C(N, rr('b:sub'), N, N), 'outside');
  assert.equal(C(N, rr('m:union'), h).item.id, 'd:Z', 'ℕ ∪ 缺口(负整数) = ℤ');
  const auto = C(h, rr('m:fill'), null);
  assert.equal(auto.item.id, 'd:Z');
  assert.equal(auto.grade, 'auto');
  assert.equal(auto.filled, h.id);
  const exact = C(h, rr('m:fill'), C(N, rr('m:union'), rr('d:NegZ')).item);
  assert.equal(exact.grade, 'exact');
  assert.equal(exact.item.id, 'd:Z');
  const over = C(h, rr('m:fill'), rr('d:Q'));
  assert.equal(over.grade, 'over');
  assert.equal(C(h, rr('m:fill'), C(N, rr('m:union'), rr('c:-1')).item).ok, false, '没包住缺的部分');
  assert.equal(C(h, rr('m:fill'), rr('d:Even')).ok, false, '没包住出发世界');
  // 前沿：√ 的缺口没有目标；用 ℚ 手填不合规
  const root = holeOf(C(N, rr('u:sqrt'), null), 'unrepresentable');
  assert.equal(C(root, rr('m:fill'), null).ok, false);
  assert.equal(C(root, rr('m:fill'), rr('d:Q')).ok, false);
  // 补不上：除以 0
  const zero = holeOf(C(rr('d:Z'), rr('u:recip'), null), 'undefined');
  assert.equal(C(zero, rr('m:fill'), null).ok, false);
  // 手填时候选包住了缺的部分、却关不住法：给出新的缺口而不是失败
  const cl = holeOf(C(rr('c:2'), rr('m:closure'), rr('b:div'), rr('d:Z')), 'outside');
  assert.equal(previewDeck(cl.v.where), '{1/2}');
  const half = C(rr('d:Z'), rr('m:union'), rr('c:1/2')).item;
  const again = C(cl, rr('m:fill'), half);
  assert.ok(again.ok && again.item === null && holeOf(again, 'outside'), '1/2 ÷ 2 = 1/4 又跑出去了');
  // 手填时没包住缺的部分：直接提示
  const dv = holeOf(C(rr('d:Z'), rr('b:div'), rr('d:Z'), rr('d:Z')), 'outside');
  assert.equal(C(dv, rr('m:fill'), half).ok, false);
});

test('反推', () => {
  assert.equal(previewDeck(C(rr('c:4'), rr('m:reverse'), rr('u:sq')).item.v), '{−2, 2}');
  assert.equal(C(rr('d:Even'), rr('m:reverse'), rr('u:succ')).item.id, 'd:Odd');
  assert.equal(C(rr('d:N'), rr('m:reverse'), rr('u:sq')).item.id, 'd:Z');
  assert.equal(previewDeck(C(rr('c:8'), rr('m:reverse'), rr('u:exp2')).item.v), '{3}');
  const dd = C(rr('c:1'), rr('m:reverse'), rr('u:D'));
  assert.ok(dd.ok && dd.item.v.has(resolveRef('c:p:1,5').v) === true, '求导得 1 的多项式包括 x + 5');
  assert.equal(C(rr('c:1'), rr('m:reverse'), rr('u:DET')).item.v.has(resolveRef('c:m:1,0,0,1').v), true);
  // 有底板时反推也限制在世界里
  const rv = C(rr('c:4'), rr('m:reverse'), rr('u:sq'), rr('d:N'));
  assert.equal(previewDeck(rv.item.v), '{2}');
  assert.ok(holeOf(rv, 'outside'));
});

test('第二轮审查的回归：目标查找、手填分档、缺口命名', () => {
  const N = rr('d:N');
  const Z = rr('d:Z');
  // [0]/[22] 带底板的并、交不再崩溃
  const un = C(N, rr('m:union'), rr('d:NegZ'), N);
  assert.equal(un.item.id, 'd:N');
  assert.equal(holeOf(un, 'outside').v.targetId, 'Z');
  assert.ok(C(Z, rr('m:inter'), rr('d:Q'), N).ok);
  // [1] 写不出来的结果也算没关住：ℤ 做 2ˣ 的越出缺口是前沿，ℚ 手填不合规
  const e2 = holeOf(C(Z, rr('u:exp2'), null, Z), 'outside');
  assert.equal(e2.v.status, 'frontier');
  assert.equal(C(e2, rr('m:fill'), rr('d:Q')).ok, false);
  // [2]/[23] 补不上的缺口手填也拒绝
  const zero = holeOf(C(Z, rr('u:recip'), null), 'undefined');
  assert.equal(C(zero, rr('m:fill'), rr('d:Q')).ok, false);
  const big = C(rr('c:1000000'), rr('b:mul'), rr('c:1000000')).holes[0];
  assert.equal(C(big, rr('m:fill'), rr('d:Q')).ok, false);
  // [3]/[12] 封闭检查不看样本顺序，有限来源的成员必查
  const hh = holeOf(C(Z, rr('u:half'), null, Z), 'outside');
  const Zh = C(Z, rr('u:half'), null).item;
  for (const K of [C(Z, rr('m:union'), Zh).item, C(Zh, rr('m:union'), Z).item]) {
    const r = C(hh, rr('m:fill'), K);
    assert.ok(r.ok && r.item === null && holeOf(r, 'outside') && !r.filled, 'ℤ ∪ ℤ/2 关不住 x/2');
  }
  const hN = holeOf(C(N, rr('b:sub'), N, N), 'outside');
  const r12 = C(hN, rr('m:fill'), C(Z, rr('m:union'), rr('c:1/2')).item);
  assert.ok(r12.ok && r12.item === null && !r12.filled, 'ℤ ∪ 1/2 关不住 −');
  // [5]/[13]/[24] 更小的合规候选是"比图鉴更紧"，不是"多了一块"
  const hd = holeOf(C(N, rr('b:div'), N, N), 'outside');
  const tight = C(hd, rr('m:fill'), C(rr('d:Qp'), rr('m:union'), rr('c:0')).item);
  assert.equal(tight.grade, 'tighter');
  assert.equal(tight.firstFill, true);
  assert.equal(C(hd, rr('m:fill'), rr('d:Q')).grade, 'exact');
  assert.equal(C(hN, rr('m:fill'), rr('d:Q')).grade, 'over');
  // [4] 0 ÷ x 在 0 处没有定义
  assert.ok(holeOf(C(rr('c:0'), rr('b:div'), Z), 'undefined'));
  assert.equal(C(rr('c:0'), rr('m:reverse'), C(rr('c:0'), rr('b:div'), null).item).item.id, 'd:Qnz');
  // [6] 没有定义的缺口落在真正出问题的那一边：ℤ₁₂ˣ ÷ ℤ₁₂ 缺的是没有逆元的除数
  const ud = holeOf(C(rr('d:U12'), rr('b:div'), rr('d:Z12')), 'undefined');
  assert.equal(ud.v.where.has(resolveRef('c:[1]12').v), false);
  assert.equal(ud.v.where.has(resolveRef('c:[2]12').v), true);
  // [7] 反推混合类型时不认成图鉴：ℤ ← 求导 不是 ℚ，而且含 x + 5
  const rd = C(Z, rr('m:reverse'), rr('u:D'));
  assert.notEqual(rd.item.id, 'd:Q');
  assert.equal(rd.item.v.has(resolveRef('c:p:1,5').v), true);
  // [8] 越出的部分不只看样本：ℚe₁ 做 2x 在 ℤ² 里有越出缺口
  assert.ok(holeOf(C(rr('d:Xaxis'), rr('u:dbl'), null, rr('d:Lattice')), 'outside'));
  // [9] 被大小上限丢掉的结果也要和底板比：力 × 力 在 力 里全部越出
  const ff = C(rr('d:Force'), rr('b:mul'), rr('d:Force'), rr('d:Force'));
  assert.ok(ff.ok && ff.item === null && holeOf(ff, 'outside'));
  // [10] ℤ ÷ 0、ℤ ^ (1/13) 是分岔不是用法错误
  const dz = C(Z, rr('b:div'), rr('c:0'));
  assert.ok(dz.ok && dz.item === null && holeOf(dz, 'undefined'));
  assert.ok(holeOf(C(Z, rr('b:pow'), rr('c:1/13')), 'unrepresentable'));
  // [11]/[17]/[26] 反推的缺口：法是"反推"，填的文案说"包含 ℕ 和 {−2}"
  const rv = holeOf(C(rr('c:4'), rr('m:reverse'), rr('u:sq'), N), 'outside');
  assert.equal(rv.v.law.t, 'pre');
  const rvAuto = C(rv, rr('m:fill'), null);
  assert.equal(rvAuto.item.id, 'd:Z');
  assert.match(rvAuto.text, /包含 ℕ 和 \{−2\}/);
  const K2 = C(N, rr('m:union'), rr('c:-2')).item;
  assert.equal(C(rv, rr('m:fill'), K2).grade, 'tighter');
  assert.equal(C(rv, rr('m:fill'), C(K2, rr('m:union'), rr('c:1/2')).item).holes.length, 0);
  // [16] 两边都是缺口：右边那张当候选，不自动填
  const h1 = holeOf(C(rr('c:1'), rr('b:sub'), rr('c:2'), N), 'outside');
  assert.equal(C(h1, rr('m:fill'), hN).ok, false);
  // [17]/[18] 越出缺口记住真正的输入；底板限制后的结果带底板名
  const hx = C(hN, rr('u:succ'), null, N);
  assert.equal(holeOf(hx, 'outside').v.sourceName, 'ℕ');
  assert.equal(holeOf(hx, 'outside').v.inputName, '缺口(负整数)');
  assert.match(hx.item.v.name, /∩ ℕ$/);
  // [21]/[31] 值级缺口：出发世界是卡组，算式另放在 expr
  const d0 = holeOf(C(rr('c:1'), rr('b:div'), rr('c:0')), 'undefined');
  assert.equal(d0.v.sourceName, '{0, 1}');
  assert.equal(d0.v.expr, '1 ÷ 0');
  assert.match(C(d0, rr('m:fill'), null).msg, /1 ÷ 0 没有定义/);
  // [27] 带底板时的说明不说"这就是"
  assert.match(C(N, rr('b:sub'), N, N).text, /留在 ℕ 里的结果就是/);
  // [29] 换了类型的越出不是缺口，也不是前沿：不能填，手填也不给首次发现
  const rt = holeOf(C(Z, rr('b:mod'), rr('c:12'), Z), 'outside');
  assert.equal(rt.v.status, 'retyped');
  assert.equal(rt.v.targetId, 'Z12');
  assert.equal(C(rt, rr('m:fill'), null).ok, false);
  assert.equal(C(rt, rr('m:fill'), C(Z, rr('m:union'), rr('d:Z12')).item).ok, false);
  assert.equal(holeOf(C(rr('d:Len'), rr('b:mul'), rr('d:Len'), rr('d:Len')), 'outside').v.status, 'retyped');
  // [30]/[36] 对数缺口和反推结果的名字
  assert.equal(C(rr('c:3'), rr('u:log2'), null).holes[0].v.name, 'log₂3');
  assert.equal(C(Z, rr('m:reverse'), rr('u:dbl')).item.v.name, '{ x | 2x ∈ ℤ }');
  // [37] 余数除以 2：有逆元就算得出，没有就没有定义
  assert.equal(C(rr('c:[1]7'), rr('u:half'), null).item.id, 'c:[4]7');
  assert.equal(holeOf(C(rr('c:[1]12'), rr('u:half'), null), 'undefined').v.status, 'unfillable');
});

test('第三轮复查的回归：取样、分档、换了类型、命名', () => {
  const N = rr('d:N');
  const Z = rr('d:Z');
  const Q = rr('d:Q');
  const U = (a, b) => C(a, rr('m:union'), b).item;
  const F = (h, k = null) => C(h, rr('m:fill'), k);
  // 没有定义 / 表示不了的缺口和底板无关：出发世界是真正的输入，world 为 null
  const e2 = holeOf(C(Q, rr('u:exp2'), null, rr('d:Np')), 'unrepresentable');
  assert.equal(e2.v.status, 'frontier');
  assert.equal(e2.v.world, null);
  assert.equal(F(holeOf(C(N, rr('u:sqrt'), null, Z), 'unrepresentable'), N).ok, false);
  const F01 = U(rr('c:0'), rr('c:1'));
  assert.equal(F(holeOf(C(N, rr('u:sqrt'), null, F01), 'unrepresentable'), F01).ok, false);
  // 包含检查看整段样本：0 排在越出部分的中间也要算
  const hq = holeOf(C(Q, rr('b:mul'), Q, rr('d:Qp')), 'outside');
  assert.equal(hq.v.targetId, 'Q');
  assert.equal(F(hq, rr('d:Qnz')).ok, false);
  // 候选自己的样本不会被缺口里的值挤掉：ℤ 在 ^ 下不封闭
  const hp = holeOf(C(N, rr('b:pow'), N, rr('d:Sq')), 'outside');
  assert.equal(F(hp, Z).item, null);
  assert.equal(F(hp, Q).ok, false);
  assert.equal(holeOf(C(rr('d:Np'), rr('b:pow'), rr('d:Np'), rr('d:Odd')), 'outside').v.status, 'frontier');
  const hN = holeOf(C(N, rr('b:sub'), N, N), 'outside');
  const Zp3 = C(Z, rr('b:add'), rr('c:1/3')).item;
  for (const K of [U(Z, Zp3), U(Zp3, Z)]) assert.equal(F(hN, K).item, null, 'ℤ ∪ (ℤ + 1/3) 关不住 −');
  // 一元法查候选的全部样本：ℚ∖{0} 在 x − 1、x + 7 下不封闭
  assert.equal(C(rr('c:1/3'), rr('u:pred'), null, rr('d:Odd')).holes[0].v.targetId, 'Q');
  assert.equal(F(C(rr('d:Sign'), rr('b:add'), rr('c:7'), rr('d:NegZ')).holes[0], rr('d:Qnz')).item, null);
  // 有限来源、像卡组的来源、样本末尾都查
  let Fb = F01;
  for (let i = 0; i < 7; i++) Fb = C(Fb, rr('b:add'), Fb).item;
  assert.equal(F(C(F01, rr('u:succ'), null, F01).holes[0], Fb).item, null, '{0..128} 关不住 x + 1');
  assert.equal(F(hN, C(U(Z, rr('c:3/2')), rr('b:sub'), rr('c:1')).item).item, null, '(ℤ ∪ 3/2) − 1 关不住 −');
  // 近似候选：视野外的"没有"不可信，视野内的越出照样算
  const hm = C(rr('d:Mono'), rr('b:mul'), rr('c:p:-4,0'), rr('d:Q2')).holes[0];
  assert.equal(F(hm, U(rr('d:Q2'), hm)).item, null);
  // 近似候选只在视野里比：½ℤ 是多了一块，ℤ × 2ᶻ 填 x/2 的缺口是比图鉴更紧
  assert.equal(F(hN, C(rr('c:1/2'), rr('m:closure'), rr('b:sub')).item).grade, 'over');
  const hh = holeOf(C(Z, rr('u:half'), null, Z), 'outside');
  assert.equal(F(hh, C(Z, rr('b:mul'), rr('d:P2z')).item).grade, 'tighter');
  // 两两运算的表示不了缺口要装得下两边：ℕ⁺ ^ ℚ⁺ 是前沿
  const hu = holeOf(C(rr('d:Np'), rr('b:pow'), rr('d:Qp')), 'unrepresentable');
  assert.equal(hu.v.status, 'frontier');
  assert.equal(F(hu, rr('d:Np')).ok, false);
  // 反推在视野里没碰到解不算空集
  const r7 = C(rr('c:1/7'), rr('m:reverse'), rr('u:D'));
  assert.notEqual(r7.item.id, 'd:Empty');
  assert.equal(r7.item.v.has(resolveRef('c:p:1/7,0').v), true);
  assert.equal(C(rr('c:p:1,0'), rr('m:reverse'), rr('u:D')).item.v.has(resolveRef('c:p:1/2,0,0').v), true);
  assert.notEqual(r7.item.id, C(rr('c:13'), rr('m:reverse'), rr('u:D')).item.id);
  // 拿缺口当候选，结果有名字
  const B = C(C(Z, rr('u:half'), null).item, rr('b:div'), rr('c:0')).holes[0];
  assert.ok(F(hN, B).item.v.name);
  // 模 n 的像凑满一整圈才精确
  assert.equal(C(N, rr('b:mod'), rr('c:23')).item.v.list.length, 23);
  assert.equal(C(Z, rr('b:mod'), rr('c:50')).item.v.list.length, 50);
  // 图鉴里另一个极小世界也是恰到好处，不算发明者
  assert.equal(F(C(rr('d:Sign'), rr('u:dbl'), null, rr('d:Sign')).holes[0], rr('d:Qnz')).grade, 'exact');
  // 换了类型：按族逐值比，不看并集顺序，常数算 0 次多项式；认成别的类型的图鉴世界才算
  assert.equal(holeOf(C(N, rr('b:sub'), N, U(N, rr('c:[1]12'))), 'outside').v.status, 'frontier');
  const s2 = rr('c:q:1|2,0,0');
  assert.equal(C(s2, rr('b:add'), s2, U(rr('d:Len'), s2)).holes[0].v.status, 'frontier');
  assert.equal(C(s2, rr('b:add'), s2, U(s2, rr('d:Len'))).holes[0].v.status, 'frontier');
  assert.equal(holeOf(C(rr('d:Q2'), rr('b:add'), rr('d:Q2'), rr('d:Q2')), 'outside').v.status, 'frontier');
  assert.equal(holeOf(C(Z, rr('u:half'), null, U(Z, rr('c:p:1,0'))), 'outside').v.status, 'frontier');
  assert.equal(holeOf(C(rr('d:Prop'), rr('u:D'), null, rr('d:Prop')), 'outside').v.status, 'retyped');
  assert.equal(holeOf(C(Z, rr('b:mod'), rr('c:12'), Z), 'outside').v.status, 'retyped');
  // inputName 是真正的输入
  assert.equal(C(rr('d:NegZ'), rr('m:union'), N, N).holes[0].v.inputName, '负整数 ∪ ℕ');
  assert.equal(F(hN, U(Z, rr('c:1/2'))).holes[0].v.inputName, '(ℤ ∪ 1/2)');
  // 混合原像 ∩ ℚ 认成 ℚ；同一张缺口放两边时右边当候选
  assert.equal(C(Z, rr('m:reverse'), rr('u:D'), Q).item.id, 'd:Q');
  assert.equal(F(hN, hN).ok, false);
  // 缺口指纹按内容：偶数 − 偶数 和 ⟨偶数 | −⟩ 在 ℕ 里是同一张
  assert.equal(C(rr('d:Even'), rr('b:sub'), rr('d:Even'), N).holes[0].id, C(rr('d:Even'), rr('m:closure'), rr('b:sub'), N).holes[0].id);
  // 并集只有一边跑出去：缺口就是那一边，认得出 ℤ₁₂
  assert.equal(C(N, rr('m:union'), rr('d:Z12'), N).holes[0].v.targetId, 'Z12');
  // 命名
  assert.equal(C(rr('d:Odd'), rr('b:sub'), rr('d:Odd'), N).item.v.name, '(奇数 − 奇数) ∩ ℕ');
  assert.equal(C(rr('c:2'), rr('m:extend'), rr('u:sqrt')).holes[0].v.name, '√2');
  assert.equal(previewDeck(C(rr('c:0'), rr('b:div'), Z).item.v), '{0}');
  assert.equal(C(Z, rr('m:reverse'), C(null, rr('b:mul'), rr('c:p:1,1')).item).item.v.name, '{ □ | □ × (x + 1) ∈ ℤ }');
  // 视野外的成员也要包住：{1, 101, 201, …} 的缺口填不成 2ⁿ
  const W = C(rr('c:1'), rr('m:extend'), C(null, rr('b:add'), rr('c:100')).item).item;
  assert.equal(F(C(W, rr('u:dbl'), null, W).holes[0], rr('d:P2')).ok, false);
  // 近似底板视野外的值不算越出
  assert.equal(C(Z, rr('u:succ'), null, C(rr('c:1/2'), rr('m:closure'), rr('b:sub')).item).holes.length, 0);
  // 常数捷径只对数成立；0 ^ x、x ^ 0 逐值算
  assert.equal(previewDeck(C(rr('d:Z12'), rr('b:mul'), rr('c:0')).item.v), '{[0]₁₂}');
  assert.equal(C(rr('d:Len'), rr('b:mul'), rr('c:0'), rr('d:Len')).holes.length, 0);
  assert.equal(previewDeck(C(rr('d:Rot4'), rr('b:pow'), rr('c:0')).item.v), '{[1 0; 0 1]}');
  assert.ok(holeOf(C(rr('c:0'), rr('b:pow'), Z), 'undefined'));
  // 另一边是别种卡：法带着它，ℤ² × ℚ 在 ℤ² 里填成 ℚ²，和单卡的左右顺序无关
  const hv = holeOf(C(rr('d:Lattice'), rr('b:mul'), Q, rr('d:Lattice')), 'outside');
  assert.equal(hv.v.targetId, 'Plane');
  assert.equal(F(hv, rr('d:Plane')).grade, 'exact');
  assert.equal(F(hv, U(rr('d:Plane'), Q)).grade, 'over');
  assert.equal(holeOf(C(rr('c:v:1,0'), rr('b:mul'), rr('c:1/2'), rr('d:Lattice')), 'outside').v.targetId, 'Plane');
});

test('缺口卡和带底板的卡组能存档重建', () => {
  const N = rr('d:N');
  const r = C(N, rr('b:sub'), N, N);
  const h = holeOf(r, 'outside');
  assert.equal(itemFromDesc(JSON.parse(JSON.stringify(h.desc)))?.id, h.id);
  const orb = C(rr('c:3'), rr('m:extend'), rr('u:pred'), N).item;
  assert.equal(itemFromDesc(JSON.parse(JSON.stringify(orb.desc)))?.id, orb.id);
  // 同一个缺口每次是同一张卡
  assert.equal(holeOf(C(N, rr('b:sub'), N, N), 'outside').id, h.id);
});
