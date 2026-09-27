// 测试公用：检查图鉴条目、按步骤模拟玩家合成。

import assert from 'node:assert/strict';

import { GIFTS, START } from '../src/content.js';
import { combine, resolveRef } from '../src/rules.js';

export const run = recipe => {
  const [L, M, Rt] = recipe.map(r => (r ? resolveRef(r) : null));
  return combine(L, M, Rt);
};

// 图鉴条目的基本要求：每种做法都真的能合成出来；至少两种做法；至少一种用到别的卡组
export function checkCatalog(list) {
  for (const c of list) {
    assert.ok(Array.isArray(c.recipes) && c.recipes.length >= 2, `${c.name} 只有 ${c.recipes?.length ?? 0} 种做法`);
    const usesOther = c.recipes.some(rec => rec.some(ref => ref && ref.startsWith('d:') && ref !== `d:${c.id}`));
    assert.ok(usesOther, `${c.name} 没有用别的卡组组成的做法`);
    for (const recipe of c.recipes) {
      const r = run(recipe);
      assert.ok(r.ok, `${c.name}: ${recipe.join(' ')} 失败：${r.msg}`);
      assert.equal(r.item.id, `d:${c.id}`, `${c.name}: ${recipe.join(' ')} 得到了 ${r.item.id}（${r.item.v.name}）`);
    }
  }
}

// 玩家的手牌：只用已经拿到的卡合成，拿到新卡时自动收下赠卡
export function makeHand(refs = START) {
  const owned = new Map();
  const add = it => {
    if (owned.has(it.id)) return;
    owned.set(it.id, it);
    for (const ref of GIFTS[it.id] ?? []) add(resolveRef(ref));
  };
  for (const ref of refs) add(resolveRef(ref));
  return {
    owned,
    has: id => owned.has(id),
    get(id) {
      assert.ok(owned.has(id), `还没有 ${id}`);
      return owned.get(id);
    },
    give(ref) {
      add(resolveRef(ref));
    },
    // 合成一步，返回新卡的 id
    step(l, m, r, expect) {
      const res = combine(l && this.get(l), this.get(m), r && this.get(r));
      assert.ok(res.ok, `${l} ${m} ${r}：${res.msg}`);
      if (expect) assert.equal(res.item.id, expect, `${l} ${m} ${r} 得到了 ${res.item.id}，不是 ${expect}`);
      add(res.item);
      return res.item.id;
    },
    // 按 [左, 中, 右, 期望的 id] 列表逐步合成
    walk(steps) {
      for (const [l, m, r, expect] of steps) this.step(l, m, r, expect);
      return this;
    },
  };
}

// 初等篇：从开局手牌到集齐 14 个入门卡组的路线
export const ELEM_STEPS = [
  ['c:1', 'b:add', 'c:1', 'c:2'],
  ['b:add', 'm:inverse', null, 'b:sub'],
  ['c:0', 'b:sub', 'c:1', 'c:-1'],
  [null, 'b:add', 'c:1', 'u:aff(1,1)'],
  ['c:0', 'm:extend', 'u:aff(1,1)', 'd:N'],
  ['c:1', 'm:extend', 'u:aff(1,1)', 'd:Np'],
  ['b:add', 'm:extend', null, 'b:mul'],
  ['b:mul', 'm:extend', null, 'b:pow'],
  ['b:mul', 'm:inverse', null, 'b:div'],
  [null, 'b:pow', 'c:2', 'u:pow(2)'],
  ['d:N', 'u:pow(2)', null, 'd:Sq'],
  [null, 'b:mul', 'c:2', 'u:aff(2,0)'],
  ['c:1', 'm:extend', 'u:aff(2,0)', 'd:P2'],
  ['c:0', 'b:sub', null, 'u:aff(-1,0)'],
  ['d:Np', 'u:aff(-1,0)', null, 'd:NegZ'],
  ['d:N', 'm:union', 'd:NegZ', 'd:Z'],
  ['c:1', 'm:extend', 'u:aff(-1,0)', 'd:Sign'],
  ['d:Z', 'u:aff(2,0)', null, 'd:Even'],
  ['d:Even', 'b:add', 'c:1', 'd:Odd'],
  ['d:Even', 'm:inter', 'd:Odd', 'd:Empty'],
  ['c:1', 'b:div', null, 'u:pow(-1)'],
  ['d:Np', 'u:pow(-1)', null, 'd:Unit'],
  ['d:Np', 'b:div', 'd:Np', 'd:Qp'],
  ['c:2', 'm:closure', 'b:div', 'd:P2z'],
  ['d:Z', 'b:div', 'd:Np', 'd:Q'],
];

// 一个已经集齐初等篇的玩家
export const elementaryHand = () => makeHand().walk(ELEM_STEPS);
