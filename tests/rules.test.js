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
  assert.equal(combine(c('c:1'), c('b:div'), c('c:0')).ok, false);
  assert.equal(combine(c('c:2'), c('b:pow'), c('c:1/2')).ok, false);
  assert.equal(combine(c('c:10'), c('b:pow'), c('c:9')).ok, false);
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

const C = (a, b, c) => combine(a, b, c);
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
  assert.equal(C(rr('c:3'), lg.item, null).ok, false);
  const inv2 = C(rr('u:recip'), rr('m:compose'), rr('u:recip')).item;
  assert.equal(C(rr('c:0'), inv2, null).ok, false, '1/(1/0) 没有定义');
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
  assert.equal(r13.ok, false);
  assert.match(r13.msg, /分母/);
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
