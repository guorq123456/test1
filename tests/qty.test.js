import test from 'node:test';
import assert from 'node:assert/strict';

import {
  CATALOG,
  WALKTHROUGH,
  CHAPTER,
  QUESTS,
  Q,
  qty,
  dim,
  dimName,
  fmtUnit,
  isQty,
  DIMS,
  NAMED_VALUES,
  WINDOW_Q,
  PROBES_Q,
  PROBES_SMALL_Q,
  SIZE_CAP,
  sizeQty,
} from '../src/domains/qty.js';
import { binV, vkey, fmtV, parseVKey, subtypeOf, typeLabel, windowFor, probesFor, sizeV } from '../src/values.js';
import { applyU, powU, aff, bindU, fmtU } from '../src/unary.js';
import { groupInfo } from '../src/decks.js';
import { R, ZERO, ONE, TWO, NEG1, OVER, isR, eq, neg } from '../src/math.js';
import { combine, resolveRef, recipeText, itemFromDesc } from '../src/rules.js';
import { checkCatalog, elementaryHand, run } from './helpers.js';

const k = s => parseVKey(s);
const isErr = r => r && typeof r === 'object' && typeof r.err === 'string';
const STEP = Q(1, 1, 0, 0);
const BREATH = Q(1, 0, 1, 0);
const HANDFUL = Q(1, 0, 0, 1);
const LI = k('q:300|1,0,0');

test('图鉴条目：每种做法都能合成，至少两种，至少一种用别的卡组', () => checkCatalog(CATALOG));

test('路线：从初等篇 + 本章赠卡出发，集齐本章全部卡组', () => {
  const hand = elementaryHand();
  assert.ok(hand.has('d:Qp'), '初等篇应该已经拿到 ℚ⁺');
  for (const g of CHAPTER.unlock.gives) assert.ok(hand.has(g), `拿到 ℚ⁺ 时应该附赠 ${g}`);
  hand.walk(WALKTHROUGH);
  for (const c of CATALOG) assert.ok(hand.has(`d:${c.id}`), c.name);
  // 任务也都能完成
  for (const q of QUESTS) assert.ok(q.done(id => hand.has(id)), q.title);
});

test('章节信息', () => {
  assert.equal(CHAPTER.id, 8);
  assert.equal(CHAPTER.unlock.when, 'd:Qp');
  for (const key of ['c:q:1|1,0,0', 'c:q:1|0,1,0', 'c:q:1|0,0,1']) assert.ok(CHAPTER.unlock.gives.includes(key), key);
  for (const x of NAMED_VALUES) assert.ok(CHAPTER.unlock.gives.includes(`c:${x.key}`), x.name);
  assert.ok(CHAPTER.intro.length > 50);
  assert.equal(CATALOG.length, DIMS.length);
  for (const c of CATALOG) {
    assert.equal(c.ch, 8, c.name);
    assert.ok(/^[A-Za-z0-9]+$/.test(c.id), `id ${c.id} 只能用字母数字`);
    assert.equal(c.type, 'qty', c.name);
    assert.equal(c.list, undefined, `${c.name} 是无限卡组，不该有 list`);
    assert.equal(c.struct, '群');
    assert.equal(c.groupOp, '+');
    assert.ok(c.note && c.desc && c.hint && c.preview, c.name);
    // has 只认自己的量纲，而且对别的类型的值不会崩
    for (const x of DIMS) assert.equal(c.has(qty(TWO, x.d)), x.id === c.id, `${c.name} has(2 ${fmtUnit(x.d)})`);
    assert.equal(c.has(R(3)), false, `${c.name} has(3)`);
  }
});

test('key 往返、显示文字、类型标签', () => {
  for (const key of ['q:1|1,0,0', 'q:3/2|1,-1,0', 'q:1|1/2,0,0', 'q:-3|0,0,1', 'q:300|1,0,0', 'q:2|2,-3,1', 'q:0|1,0,0', 'q:1/12|-1,-2,1']) {
    const v = parseVKey(key);
    assert.ok(v && isQty(v), key);
    assert.equal(vkey(v), key);
    assert.deepEqual(parseVKey(vkey(v)), v);
    assert.equal(subtypeOf(v), 'qty');
  }
  // 不合法的 key；有理数还是有理数
  for (const bad of ['q:1|0,0,0', 'q:1|1,0', 'q:a|1,0,0', 'q:1/0|1,0,0', 'q:1|1,0,0,0', 'q:|1,0,0', '1|1,0,0']) {
    assert.equal(parseVKey(bad), null, bad);
  }
  assert.ok(isR(parseVKey('3')));
  assert.ok(isR(parseVKey('1/2')));

  assert.equal(fmtV(Q(3, 1, 0, 0)), '3 步');
  assert.equal(fmtV(Q(2, 2, 0, 0)), '2 步²');
  assert.equal(fmtV(Q(1, 3, 0, 0)), '1 步³');
  assert.equal(fmtV(Q('3/2', 1, -1, 0)), '3/2 步/息');
  assert.equal(fmtV(Q(1, 1, -2, 1)), '1 捧·步/息²');
  assert.equal(fmtV(Q(1, 2, -2, 1)), '1 捧·步²/息²');
  assert.equal(fmtV(Q(1, '1/2', 0, 0)), '1 步^(1/2)');
  assert.equal(fmtV(Q(2, '-1/2', 0, 0)), '2/步^(1/2)');
  assert.equal(fmtV(Q(3, 0, -1, 0)), '3/息');
  assert.equal(fmtV(Q('1/2', 0, -1, 0)), '(1/2)/息');
  assert.equal(fmtV(Q(1, -1, -2, 1)), '1 捧/(步·息²)');
  assert.equal(fmtV(Q(-3, 1, 0, 0)), '−3 步');
  assert.equal(fmtV(Q(0, 1, 0, 0)), '0 步');
  assert.equal(fmtV(BREATH), '1 息');
  assert.equal(fmtV(HANDFUL), '1 捧');

  assert.equal(typeLabel(STEP), '长度');
  assert.equal(typeLabel(Q(2, 2, 0, 0)), '面积');
  assert.equal(typeLabel(Q(2, 3, 0, 0)), '体积');
  assert.equal(typeLabel(BREATH), '时间');
  assert.equal(typeLabel(HANDFUL), '质量');
  assert.equal(typeLabel(Q(2, 1, -1, 0)), '速度');
  assert.equal(typeLabel(Q(2, 1, -2, 0)), '加速度');
  assert.equal(typeLabel(Q(2, 0, -1, 0)), '频率');
  assert.equal(typeLabel(Q(2, 1, -2, 1)), '力');
  assert.equal(typeLabel(Q(2, 2, -2, 1)), '能量');
  assert.equal(typeLabel(Q(2, 2, -3, 1)), '功率');
  assert.equal(typeLabel(Q(2, 1, -1, 1)), '动量');
  assert.equal(typeLabel(Q(2, 1, 1, 0)), '量');
  assert.equal(dimName(Q(2, '1/2', 0, 0)), '量');
  // 固定值单卡的小字带着老单位的名字
  assert.equal(typeLabel(LI), '长度（1 里）');
  assert.equal(typeLabel(k('q:20000|0,1,0')), '时间（1 日）');
  assert.equal(typeLabel(k('q:120|0,0,1')), '质量（1 石）');
  assert.equal(typeLabel(k('q:2|1,0,0')), '长度（1 庹）');
});

test('乘除合并量纲', () => {
  assert.equal(vkey(binV('mul', STEP, STEP)), 'q:1|2,0,0');
  assert.equal(vkey(binV('div', STEP, BREATH)), 'q:1|1,-1,0');
  assert.equal(vkey(binV('mul', R(2), Q(3, 1, 0, 0))), 'q:6|1,0,0');
  assert.equal(vkey(binV('mul', Q(3, 1, 0, 0), R(2))), 'q:6|1,0,0');
  assert.equal(vkey(binV('div', Q(6, 1, 0, 0), R(4))), 'q:3/2|1,0,0');
  assert.equal(vkey(binV('div', R(1), BREATH)), 'q:1|0,-1,0');
  assert.equal(vkey(binV('div', R(3), Q(2, 1, 0, 0))), 'q:3/2|-1,0,0');
  assert.equal(typeLabel(binV('mul', HANDFUL, Q(2, 1, -2, 0))), '力');
  assert.equal(typeLabel(binV('mul', Q(2, 1, -2, 1), Q(3, 1, 0, 0))), '能量');
  assert.equal(typeLabel(binV('div', Q(1, 2, -2, 1), Q(2, 0, 1, 0))), '功率');
  assert.equal(fmtV(binV('div', Q(1, 2, -2, 1), Q(2, 0, 1, 0))), '1/2 捧·步²/息³');
  // 分数指数也能合并：步^(1/2) × 步^(1/2) = 步
  assert.equal(vkey(binV('mul', Q(1, '1/2', 0, 0), Q(1, '1/2', 0, 0))), 'q:1|1,0,0');
  // 除以 0
  assert.ok(isErr(binV('div', STEP, Q(0, 1, 0, 0))));
  assert.ok(isErr(binV('div', STEP, ZERO)));
  assert.match(binV('div', STEP, ZERO).err, /不能除以 0/);
  // 太大
  assert.equal(binV('mul', Q(10000000, 1, 0, 0), R(10)), OVER);
});

test('无量纲的结果退回有理数', () => {
  const one = binV('div', STEP, STEP);
  assert.ok(isR(one));
  assert.ok(eq(one, ONE));
  assert.ok(eq(binV('div', Q(3, 1, 0, 0), STEP), R(3)));
  assert.ok(eq(binV('mul', STEP, Q(2, -1, 0, 0)), TWO));
  assert.ok(eq(binV('div', Q(2, 1, -1, 0), Q(4, 1, -1, 0)), R(1, 2)));
  assert.ok(eq(binV('pow', Q(5, 1, 0, 0), ZERO), ONE));
  // 有理数不会被认成量
  assert.equal(parseVKey('1').t, undefined);
});

test('同量纲加减', () => {
  assert.equal(vkey(binV('add', Q(3, 1, 0, 0), Q(2, 1, 0, 0))), 'q:5|1,0,0');
  assert.equal(vkey(binV('sub', Q(3, 1, 0, 0), Q(5, 1, 0, 0))), 'q:-2|1,0,0');
  assert.equal(vkey(binV('add', Q('1/2', 1, -1, 0), Q('1/3', 1, -1, 0))), 'q:5/6|1,-1,0');
  // 3 步 − 3 步 = 0 步：还是长度，不是数
  const z = binV('sub', Q(3, 1, 0, 0), Q(3, 1, 0, 0));
  assert.ok(isQty(z));
  assert.equal(vkey(z), 'q:0|1,0,0');
  assert.equal(vkey(binV('add', Q(1, 1, -2, 1), Q(1, 1, -2, 1))), 'q:2|1,-2,1');
});

test('不同量纲加减报错，量和数加减报错', () => {
  const r = binV('add', STEP, BREATH);
  assert.ok(isErr(r));
  assert.match(r.err, /长度和时间不能相加/);
  assert.match(binV('sub', STEP, HANDFUL).err, /长度和质量不能相减/);
  assert.match(binV('add', STEP, Q(1, 2, 0, 0)).err, /长度和面积不能相加/);
  assert.match(binV('add', Q(1, 1, 1, 0), STEP).err, /单位是 步·息 的量和长度不能相加/);
  assert.match(binV('add', STEP, ONE).err, /没有单位/);
  assert.match(binV('add', ONE, STEP).err, /没有单位/);
  assert.match(binV('sub', R(1, 2), Q(1, 0, 1, 0)).err, /不能相减/);
  // 合成台上也是同样的解释
  const res = combine(resolveRef('c:q:1|1,0,0'), resolveRef('b:add'), resolveRef('c:q:1|0,1,0'));
  assert.equal(res.ok, false);
  assert.match(res.msg, /长度和时间不能相加/);
  // x + 1 对量算不出
  assert.ok(isErr(applyU(aff(ONE, ONE), STEP)));
});

test('乘方与分数指数', () => {
  assert.equal(vkey(binV('pow', Q(4, 2, 0, 0), R(1, 2))), 'q:2|1,0,0');
  assert.equal(vkey(binV('pow', Q(8, 3, 0, 0), R(1, 3))), 'q:2|1,0,0');
  assert.equal(vkey(binV('pow', Q(3, 1, -1, 0), TWO)), 'q:9|2,-2,0');
  assert.equal(vkey(binV('pow', STEP, R(1, 2))), 'q:1|1/2,0,0');
  assert.equal(vkey(binV('pow', Q(1, '1/2', 0, 0), TWO)), 'q:1|1,0,0');
  assert.equal(vkey(binV('pow', Q(2, 1, 0, 0), NEG1)), 'q:1/2|-1,0,0');
  assert.equal(vkey(binV('pow', Q(1, 2, 0, 0), R(3, 2))), 'q:1|3,0,0');
  assert.equal(vkey(binV('pow', Q(0, 1, 0, 0), TWO)), 'q:0|2,0,0');
  // 开不出有理数
  const r = binV('pow', Q(2, 1, 0, 0), R(1, 2));
  assert.ok(isErr(r));
  assert.match(r.err, /不是有理数/);
  assert.ok(isErr(binV('pow', Q(2, 2, 0, 0), R(1, 2))));
  // 指数不能带单位；分母太大；0 的 0 次方
  assert.match(binV('pow', STEP, BREATH).err, /指数不能带单位/);
  assert.match(binV('pow', TWO, STEP).err, /指数不能带单位/);
  assert.match(binV('pow', STEP, R(1, 13)).err, /分母太大/);
  assert.ok(isErr(binV('pow', Q(0, 1, 0, 0), ZERO)));
  assert.ok(isErr(binV('pow', Q(0, 1, 0, 0), NEG1)));
  // 当一元算子
  assert.equal(vkey(applyU(powU(R(1, 2)), Q(4, 2, 0, 0))), 'q:2|1,0,0');
  assert.equal(vkey(applyU(powU(NEG1), Q(2, 0, 1, 0))), 'q:1/2|0,-1,0');
  assert.equal(vkey(applyU(aff(TWO, ZERO), Q(3, 1, 0, 0))), 'q:6|1,0,0');
  assert.equal(vkey(applyU(bindU('mul', 'r', STEP), R(3))), 'q:3|1,0,0');
  assert.equal(vkey(applyU(bindU('div', 'l', STEP), Q(2, 0, 1, 0))), 'q:1/2|1,-1,0');
});

test('固定值换算', () => {
  for (const x of NAMED_VALUES) {
    const v = parseVKey(x.key);
    assert.ok(v && isQty(v), x.name);
    assert.match(typeLabel(v), new RegExp(`1 ${x.name}`));
  }
  const ZHA = k('q:1/5|1,0,0');
  const TUO = k('q:2|1,0,0');
  const KE = k('q:200|0,1,0');
  const RI = k('q:20000|0,1,0');
  const DAN = k('q:120|0,0,1');
  assert.equal(fmtV(LI), '300 步');
  assert.ok(eq(binV('div', LI, STEP), R(300)));
  assert.ok(eq(binV('div', LI, ZHA), R(1500)));
  assert.ok(eq(binV('div', TUO, ZHA), R(10)));
  assert.ok(eq(binV('div', STEP, ZHA), R(5)));
  assert.ok(eq(binV('div', RI, KE), R(100)));
  assert.ok(eq(binV('div', KE, BREATH), R(200)));
  assert.ok(eq(binV('div', DAN, HANDFUL), R(120)));
  // 1 里走 300 息，速度是 1 步/息
  assert.equal(vkey(binV('div', LI, Q(300, 0, 1, 0))), 'q:1|1,-1,0');
  // 合成台：里 ÷ 步 = 300
  const r = combine(resolveRef('c:q:300|1,0,0'), resolveRef('b:div'), resolveRef('c:q:1|1,0,0'));
  assert.equal(r.item.id, 'c:300');
  assert.equal(r.text, '300 步 ÷ 1 步 = 300');
});

test('取余、拼接都做不了', () => {
  assert.match(binV('mod', Q(7, 1, 0, 0), R(2)).err, /带着单位/);
  assert.ok(isErr(binV('mod', R(7), Q(2, 1, 0, 0))));
  assert.ok(isErr(binV('mod', STEP, STEP)));
  assert.match(binV('cat', STEP, STEP).err, /拼接/);
});

test('视野与探针', () => {
  assert.equal(windowFor('qty'), WINDOW_Q);
  assert.equal(probesFor('qty'), PROBES_Q);
  assert.ok(WINDOW_Q.length < 300, `视野有 ${WINDOW_Q.length} 个值，太多了`);
  const keys = new Set(WINDOW_Q.map(vkey));
  assert.equal(keys.size, WINDOW_Q.length, '视野里有重复');
  for (const v of WINDOW_Q) {
    assert.ok(isQty(v), vkey(v));
    assert.deepEqual(parseVKey(vkey(v)), v);
  }
  for (const c of CATALOG) {
    const inWin = WINDOW_Q.filter(c.has);
    assert.ok(inWin.length >= 10, `${c.name} 在视野里的值太少`);
    // 量纲类带符号：视野里有 0 和负值，两两运算、封闭才算得出它们
    const d = inWin[0].dim;
    for (const s of ['0', '-1', '-2']) assert.ok(keys.has(vkey(qty(k(s), d))), `${c.name} 的视野里应该有 ${s} ${fmtUnit(d)}`);
    const small = PROBES_SMALL_Q.filter(c.has);
    assert.ok(small.length >= 3, `${c.name} 的小探针太少`);
    for (const p of small) assert.ok(sizeV(p) <= SIZE_CAP, `${c.name} 的探针 ${fmtV(p)} 太大（${sizeV(p)}），两两运算会把它丢掉`);
    // 小探针是正值加一个 0（近似卡组只比对它们）；大探针里还有 −1，精确卡组才分得出 ℚ⁺·步 和 ℚ·步
    for (const p of small) assert.ok(p.v.n >= 0, `小探针 ${fmtV(p)} 不应该是负的`);
    assert.ok(small.some(p => p.v.n === 0), `${c.name} 的小探针里应该有 0`);
    const big = PROBES_Q.filter(c.has);
    assert.ok(big.length > small.length, `${c.name} 应该有几个大探针`);
    assert.ok(big.some(p => p.v.n === 0), `${c.name} 的大探针里应该有 0`);
    assert.ok(big.some(p => p.v.n < 0), `${c.name} 的大探针里应该有负值`);
  }
  for (const p of PROBES_Q) assert.ok(PROBES_Q.filter(x => vkey(x) === vkey(p)).length === 1, `探针 ${vkey(p)} 重复`);
  // 大小：值的高度加上指数
  assert.equal(sizeQty(STEP), 3);
  assert.equal(sizeQty(Q(8, 3, 0, 0)), 14);
  assert.equal(sizeQty(Q(2, 2, -3, 1)), 14);
  assert.equal(sizeQty(Q(1, '1/2', 0, 0)), 2);
});

test('每个量纲类对 + 都是群：封闭、有 0、有相反数；对 × 不封闭', () => {
  for (const c of CATALOG) {
    const D = resolveRef(`d:${c.id}`).v;
    assert.equal(groupInfo(D), null, `${c.name} 是无限卡组，groupInfo 判断不了`);
    const P = PROBES_Q.filter(x => D.has(x));
    assert.ok(P.length >= 3, c.name);
    const d = P[0].dim;
    const zero = qty(ZERO, d);
    assert.equal(D.has(zero), true, `${c.name} 应该有 0 ${fmtUnit(d)}`);
    for (const a of P) {
      for (const b of P) {
        assert.equal(D.has(binV('add', a, b)), true, `${fmtV(a)} + ${fmtV(b)}`);
        assert.equal(D.has(binV('sub', a, b)), true, `${fmtV(a)} − ${fmtV(b)}`);
        assert.equal(D.has(binV('mul', a, b)), false, `${fmtV(a)} × ${fmtV(b)} 不该还在 ${c.name} 里`);
      }
      assert.equal(vkey(binV('add', a, zero)), vkey(a));
      const inv = qty(neg(a.v), d);
      assert.equal(D.has(inv), true, `${c.name} 应该有 ${fmtV(inv)}`);
      assert.equal(vkey(binV('add', a, inv)), vkey(zero));
    }
    // 别的量纲类的探针都不在里面
    for (const x of PROBES_Q) if (!P.includes(x)) assert.equal(D.has(x), false, `${c.name} 不该有 ${fmtV(x)}`);
  }
});

test('合成台上的用法与文字', () => {
  const c = ref => resolveRef(ref);
  // 单卡 × 单卡
  assert.equal(combine(c('c:q:1|1,0,0'), c('b:mul'), c('c:q:1|1,0,0')).item.id, 'c:q:1|2,0,0');
  assert.equal(combine(c('c:q:1|1,0,0'), c('b:mul'), c('c:q:1|1,0,0')).text, '1 步 × 1 步 = 1 步²');
  // 空位绑定：x × 1 步
  const r = combine(null, c('b:mul'), c('c:q:1|1,0,0'));
  assert.ok(r.ok);
  assert.equal(fmtU(r.item.v), 'x × (1 步)');
  assert.equal(vkey(applyU(r.item.v, R(3))), 'q:3|1,0,0');
  assert.equal(fmtU(bindU('div', 'l', BREATH)), '(1 息) ÷ x');
  assert.equal(fmtU(bindU('mul', 'r', Q(3, 0, -1, 0))), 'x × 3/息');
  // 做法文字
  assert.equal(recipeText(['d:Len', 'b:mul', 'd:Len']), '长度 × 长度');
  assert.equal(recipeText(['d:Time', 'u:recip', null]), '时间 经 1/x');
  assert.equal(recipeText(['d:Q', 'b:mul', 'c:q:1|1,0,0']), 'ℚ × 1 步');
  assert.equal(recipeText(['d:Len', 'u:sq', null]), '长度 经 x²');
  // 长度 经 x² 只有平方数，不是整个面积；ℚ⁺ ÷ 时间 没有 0，不是整个频率
  assert.ok(combine(c('d:Len'), c('u:sq'), null).item.id.startsWith('d:~'));
  assert.ok(combine(c('d:Len'), c('u:cube'), null).item.id.startsWith('d:~'));
  assert.ok(combine(c('d:Qp'), c('b:div'), c('d:Time')).item.id.startsWith('d:~'));
  assert.equal(combine(c('d:Q'), c('b:div'), c('d:Time')).item.id, 'd:Freq');
  // 存档描述可以重建
  const card = c('c:q:3/2|1,-1,0');
  assert.equal(itemFromDesc(JSON.parse(JSON.stringify(card.desc))).id, card.id);
  const area = combine(c('d:Len'), c('b:mul'), c('d:Len')).item;
  assert.equal(itemFromDesc(JSON.parse(JSON.stringify(area.desc))).id, 'd:Area');
});

test('另外几种自然的做法也能被认出来；不该认的不认', () => {
  const ok = (recipe, id) => {
    const r = run(recipe);
    assert.ok(r.ok, `${recipe.join(' ')}：${r.msg}`);
    assert.equal(r.item.id, id, recipe.join(' '));
  };
  const unnamed = recipe => {
    const r = run(recipe);
    assert.ok(r.ok, `${recipe.join(' ')}：${r.msg}`);
    assert.ok(r.item.id.startsWith('d:~'), `${recipe.join(' ')} 得到了 ${r.item.id}，不该在图鉴里`);
    return r.item.v;
  };
  // 长度平方只有平方数（凑不出 2 步²），立方只有立方数：都不是整个面积、体积
  unnamed(['d:Len', 'b:pow', 'c:2']);
  unnamed(['d:Len', 'b:pow', 'c:3']);
  // 体积开立方：负数也开得出，恰好是整个长度
  ok(['d:Vol', 'b:pow', 'c:1/3'], 'd:Len');
  ok(['d:Len', 'b:mul', 'c:2'], 'd:Len');
  ok(['d:Len', 'b:add', 'c:q:1|1,0,0'], 'd:Len');
  ok(['d:Len', 'b:div', 'c:q:1|0,1,0'], 'd:Vel');
  ok(['d:Len', 'b:mul', 'c:q:1|1,0,0'], 'd:Area');
  ok(['d:Len', 'b:mul', 'c:q:300|1,0,0'], 'd:Area');
  ok(['d:Mass', 'b:mul', 'c:q:1|1,-2,0'], 'd:Force');
  ok(['d:Len', 'b:div', 'd:Area'], 'd:~' + run(['d:Len', 'b:div', 'd:Area']).item.id.slice(3));
  ok(['d:Len', 'm:closure', 'b:add'], 'd:Len');
  ok(['d:Len', 'm:closure', 'b:sub'], 'd:Len');
  ok(['d:Force', 'b:mul', 'd:Vel'], 'd:Power');
  ok(['d:Vel', 'b:mul', 'd:Len'], 'd:~' + run(['d:Vel', 'b:mul', 'd:Len']).item.id.slice(3)); // 步²/息 不在图鉴里
  ok(['d:Q', 'b:div', 'd:Time'], 'd:Freq');
  ok(['d:Acc', 'b:div', 'd:Vel'], 'd:Freq');
  ok(['d:Len', 'u:neg', null], 'd:Len');
  // 彩蛋：长度 ÷ 1 步 回到 ℚ
  ok(['d:Len', 'b:div', 'c:q:1|1,0,0'], 'd:Q');
  ok(['d:Time', 'b:div', 'c:q:1|0,1,0'], 'd:Q');
  // 不该认的
  const n = unnamed(['d:N', 'b:mul', 'c:q:1|1,0,0']); // ℕ 步：没有 1/2 步
  assert.equal(n.has(Q('1/2', 1, 0, 0)), false);
  assert.equal(n.has(Q(3, 1, 0, 0)), true);
  // √面积 只有不往回走的长度：有 0 步、1/2 步，没有 −1 步
  const root = unnamed(['d:Area', 'u:sqrt', null]);
  assert.equal(root.has(Q(0, 1, 0, 0)), true);
  assert.equal(root.has(Q('1/2', 1, 0, 0)), true);
  assert.equal(root.has(Q(-1, 1, 0, 0)), false);
  // 时间倒过来少了 0/息（0 息倒不过来），不是整个频率
  for (const rec of [['d:Time', 'u:recip', null], ['d:Time', 'b:pow', 'c:-1']]) {
    const inv = unnamed(rec);
    assert.equal(inv.has(Q(0, 0, -1, 0)), false, recipeText(rec));
    assert.equal(inv.has(Q(-2, 0, -1, 0)), true, recipeText(rec));
  }
  assert.equal(unnamed(['d:Freq', 'u:recip', null]).has(Q(0, 0, 1, 0)), false);
  // 1 步 ÷ 时间 同样得不到 0 步/息，不是整个速度
  const perT = unnamed(['c:q:1|1,0,0', 'b:div', 'd:Time']);
  assert.equal(perT.has(Q(0, 1, -1, 0)), false);
  assert.equal(perT.has(Q(-1, 1, -1, 0)), true);
  assert.equal(perT.has(Q(2, 1, -1, 0)), true);
  unnamed(['d:Len', 'u:recip', null]); // 1/步
  unnamed(['d:Len', 'b:pow', 'c:1/2']); // 步^(1/2)
  unnamed(['d:Len', 'm:closure', 'b:mul']); // 步、步²、步³……
  unnamed(['d:Len', 'b:mul', 'd:Time']); // 步·息
  // 1 步 延展 x + 1 步：1 步、2 步、3 步……只有整数步，不是长度
  const plusStep = combine(null, resolveRef('b:add'), resolveRef('c:q:1|1,0,0')).item;
  const orbit = combine(resolveRef('c:q:1|1,0,0'), resolveRef('m:extend'), plusStep);
  assert.ok(orbit.ok && orbit.item.id.startsWith('d:~'));
  assert.equal(orbit.item.v.has(Q(5, 1, 0, 0)), true);
  assert.equal(orbit.item.v.has(Q('1/2', 1, 0, 0)), false);
  // 长度 + 时间：一张都算不出，引擎带出解释
  const bad = run(['d:Len', 'b:add', 'd:Time']);
  assert.equal(bad.ok, false);
  assert.match(bad.msg, /不能相加/);
  // 1 步 在 × 下封闭：步的各次幂，长到大小上限就停
  const pw = run(['c:q:1|1,0,0', 'm:closure', 'b:mul']);
  assert.ok(pw.ok);
  assert.deepEqual(
    pw.item.v.elems.slice(0, 3).map(vkey),
    ['q:1|1,0,0', 'q:1|2,0,0', 'q:1|3,0,0'],
  );
});

test('量纲类带符号：ℚ·步 是长度，ℚ⁺·步 不是；除回去不会自相矛盾', () => {
  const r = (...rec) => {
    const res = run(rec);
    assert.ok(res.ok, `${rec.join(' ')}：${res.msg}`);
    return res;
  };
  const STEP_REF = 'c:q:1|1,0,0';
  // ℚ × 1 步 = 长度，里面有 0 步和往回走的 −3 步
  const len = r('d:Q', 'b:mul', STEP_REF);
  assert.equal(len.item.id, 'd:Len');
  assert.equal(len.item.v.has(Q(-3, 1, 0, 0)), true);
  assert.equal(len.item.v.has(Q(0, 1, 0, 0)), true);
  // ℚ⁺ × 1 步 只有往前走的长度：自造卡组，不是长度
  const pos = r('d:Qp', 'b:mul', STEP_REF);
  assert.ok(pos.item.id.startsWith('d:~'), `ℚ⁺ × 1 步 得到了 ${pos.item.id}`);
  assert.equal(pos.item.v.has(Q(3, 1, 0, 0)), true);
  assert.equal(pos.item.v.has(Q('1/2', 1, 0, 0)), true);
  assert.equal(pos.item.v.has(Q(0, 1, 0, 0)), false);
  assert.equal(pos.item.v.has(Q(-3, 1, 0, 0)), false);
  // 除回去：(ℚ⁺ × 1 步) ÷ 1 步 = ℚ⁺，长度 ÷ 1 步 = ℚ
  assert.equal(combine(pos.item, resolveRef('b:div'), resolveRef(STEP_REF)).item.id, 'd:Qp');
  assert.equal(r('d:Len', 'b:div', STEP_REF).item.id, 'd:Q');
  // 长度 ÷ 长度 不再是 ℚ⁺。视野里每个量纲类只有 −1、−2 两个负值，凑不出 −4/3、−7/5 这样的负探针，
  // 所以得到的是在视野里算出来的 ℚ 的近似子卡组：有 0、有负数、ℚ⁺ 的小探针都在
  const ll = r('d:Len', 'b:div', 'd:Len');
  assert.notEqual(ll.item.id, 'd:Qp');
  if (ll.item.id !== 'd:Q') {
    const D = ll.item.v;
    assert.ok(ll.item.id.startsWith('d:~') && D.approx, ll.item.id);
    assert.ok(D.elems.every(isR));
    for (const s of ['0', '-1', '-2', '-12', '-1/2', '-1/12', '1', '12', '1/6', '5/6', '7/5', '12/11']) {
      assert.equal(D.has(k(s)), true, `长度 ÷ 长度 应该有 ${s}`);
    }
  }
  // 时间 ÷ 时间、力 ÷ 力 得到同一个卡组
  assert.equal(r('d:Time', 'b:div', 'd:Time').item.id, ll.item.id);
  assert.equal(r('d:Force', 'b:div', 'd:Force').item.id, ll.item.id);
  // −3 步 ÷ 1 步 = −3
  const m3 = r('c:q:-3|1,0,0', 'b:div', STEP_REF);
  assert.equal(m3.item.id, 'c:-3');
  assert.equal(m3.text, '−3 步 ÷ 1 步 = −3');
  // ℤ、ℕ⁺、ℕ × 1 步，ℚ⁺ × 1 步，√面积：各不相同，都不是长度
  const Zs = r('d:Z', 'b:mul', STEP_REF);
  const Nps = r('d:Np', 'b:mul', STEP_REF);
  const Ns = r('d:N', 'b:mul', STEP_REF);
  const root = r('d:Area', 'u:sqrt', null);
  const ids = [Zs, Nps, Ns, pos, root].map(x => x.item.id);
  for (const id of ids) assert.ok(id.startsWith('d:~'), id);
  assert.equal(new Set(ids).size, ids.length, ids.join(' '));
  assert.equal(Zs.item.v.has(Q(-1, 1, 0, 0)), true);
  assert.equal(Nps.item.v.has(Q(-1, 1, 0, 0)), false);
  assert.equal(Nps.item.v.has(Q(0, 1, 0, 0)), false);
  assert.equal(Ns.item.v.has(Q(0, 1, 0, 0)), true);
  // 同一个卡组第二次合成得到同一个 id
  assert.equal(r('d:Np', 'b:mul', STEP_REF).item.id, Nps.item.id);
});

test('合成速度：两两运算、像、封闭都在 200ms 内', () => {
  const c = ref => resolveRef(ref);
  const cases = [
    () => combine(c('d:Len'), c('b:mul'), c('d:Len')),
    () => combine(c('d:Len'), c('b:div'), c('d:Len')),
    () => combine(c('d:Q'), c('b:div'), c('d:Freq')),
    () => combine(c('d:Q'), c('b:div'), c('d:Time')),
    () => combine(c('d:Q'), c('b:mul'), c('c:q:1|1,0,0')),
    () => combine(c('d:Len'), c('u:sq'), null),
    () => combine(c('d:Len'), c('m:closure'), c('b:add')),
    () => combine(c('d:Len'), c('m:closure'), c('b:mul')),
    () => combine(c('d:Force'), c('m:closure'), c('b:div')),
    () => combine(c('c:q:1|1,0,0'), c('m:extend'), combine(null, c('b:mul'), c('c:q:1|1,0,0')).item),
  ];
  // 第一次跑会带上 JIT 预热，先热一下
  combine(c('d:Vel'), c('m:closure'), c('b:div'));
  for (const f of cases) {
    const t0 = performance.now();
    const r = f();
    const dt = performance.now() - t0;
    assert.ok(r.ok, r.msg);
    assert.ok(dt < 200, `用了 ${dt.toFixed(0)}ms`);
  }
});

// 长度、时间 在 ÷ 下封闭是最慢的用例，不放进上面的速度测试：量纲类带符号以后，大小上限内能算出的卡
// 多了一倍（约 1200 张），封闭会一直算到引擎的运算预算用完才停（单独跑约 500ms）。这里只检查它们能算完、
// 结果标成被截断的近似卡组，时间不失控
test('长度、时间 在 ÷ 下封闭：能算完，停在引擎的运算预算上', () => {
  const c = ref => resolveRef(ref);
  for (const id of ['d:Len', 'd:Time']) {
    const t0 = performance.now();
    const r = combine(c(id), c('m:closure'), c('b:div'));
    const dt = performance.now() - t0;
    assert.ok(r.ok, r.msg);
    assert.ok(r.item.v.approx && r.item.v.truncated, id);
    assert.ok(dt < 2000, `${id} 在 ÷ 下封闭用了 ${dt.toFixed(0)}ms`);
  }
});
