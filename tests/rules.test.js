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
