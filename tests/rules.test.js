import test from 'node:test';
import assert from 'node:assert/strict';

import { CATALOG, START } from '../src/catalog.js';
import { combine, itemFromDesc, resolveRef, recipeText } from '../src/rules.js';
import { R, fmtU, compose, invertU, aff, powU, ONE, TWO, ZERO, NEG1, previewDeck } from '../src/math.js';

const run = recipe => {
  const [L, M, Rt] = recipe.map(r => (r ? resolveRef(r) : null));
  return combine(L, M, Rt);
};

test('图鉴里每一种做法都能真的合成出对应的卡组', () => {
  for (const c of CATALOG) {
    for (const recipe of c.recipes) {
      const r = run(recipe);
      assert.ok(r.ok, `${c.name}: ${recipe.join(' ')} 失败：${r.msg}`);
      assert.equal(r.item.id, `d:${c.id}`, `${c.name}: ${recipe.join(' ')} 得到了 ${r.item.id}（${r.item.v.name}）`);
    }
  }
});

test('每个卡组至少有两种做法，并且至少一种用到了别的卡组', () => {
  for (const c of CATALOG) {
    assert.ok(c.recipes.length >= 2, `${c.name} 只有 ${c.recipes.length} 种做法`);
    const usesOther = c.recipes.some(rec => rec.some(ref => ref && ref.startsWith('d:') && ref !== `d:${c.id}`));
    assert.ok(usesOther, `${c.name} 没有用别的卡组组成的做法`);
  }
});

test('从开局手牌出发，只用已经拿到的卡，就能集齐全部入门卡组', () => {
  const owned = new Map(START.map(ref => [resolveRef(ref).id, resolveRef(ref)]));
  const get = id => {
    assert.ok(owned.has(id), `还没有 ${id}`);
    return owned.get(id);
  };
  const step = (l, m, r) => {
    const res = combine(l && get(l), get(m), r && get(r));
    assert.ok(res.ok, `${l} ${m} ${r}：${res.msg}`);
    owned.set(res.item.id, res.item);
    return res.item.id;
  };

  assert.equal(step('c:1', 'b:add', 'c:1'), 'c:2');
  assert.equal(step('b:add', 'm:inverse', null), 'b:sub');
  assert.equal(step('c:0', 'b:sub', 'c:1'), 'c:-1');
  const succ = step(null, 'b:add', 'c:1');
  assert.equal(succ, 'u:aff(1,1)');
  assert.equal(step('c:0', 'm:extend', succ), 'd:N');
  assert.equal(step('c:1', 'm:extend', succ), 'd:Np');
  assert.equal(step('b:add', 'm:extend', null), 'b:mul');
  assert.equal(step('b:mul', 'm:extend', null), 'b:pow');
  assert.equal(step('b:mul', 'm:inverse', null), 'b:div');
  const sq = step(null, 'b:pow', 'c:2');
  assert.equal(step('d:N', sq, null), 'd:Sq');
  const dbl = step(null, 'b:mul', 'c:2');
  assert.equal(step('c:1', 'm:extend', dbl), 'd:P2');
  const neg = step('c:0', 'b:sub', null);
  assert.equal(step('d:Np', neg, null), 'd:NegZ');
  assert.equal(step('d:N', 'm:union', 'd:NegZ'), 'd:Z');
  assert.equal(step('c:1', 'm:extend', neg), 'd:Sign');
  assert.equal(step('d:Z', dbl, null), 'd:Even');
  assert.equal(step('d:Even', 'b:add', 'c:1'), 'd:Odd');
  assert.equal(step('d:Even', 'm:inter', 'd:Odd'), 'd:Empty');
  const recip = step('c:1', 'b:div', null);
  assert.equal(step('d:Np', recip, null), 'd:Unit');
  assert.equal(step('d:Np', 'b:div', 'd:Np'), 'd:Qp');
  assert.equal(step('c:2', 'm:closure', 'b:div'), 'd:P2z');
  assert.equal(step('d:Z', 'b:div', 'd:Np'), 'd:Q');

  for (const c of CATALOG) assert.ok(owned.has(`d:${c.id}`), `没有集齐 ${c.name}`);
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
