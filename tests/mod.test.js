import test from 'node:test';
import assert from 'node:assert/strict';

import { CATALOG, WALKTHROUGH, CHAPTER, M, modInv } from '../src/domains/mod.js';
import { binV, vkey, fmtV, parseVKey, subtypeOf, typeLabel, windowFor, probesFor, TYPES } from '../src/values.js';
import { applyU, powU, aff, bindU, fmtU, compose } from '../src/unary.js';
import { groupInfo } from '../src/decks.js';
import { R, ONE, ZERO, NEG1, TWO } from '../src/math.js';
import { combine, resolveRef, recipeText } from '../src/rules.js';
import { checkCatalog, elementaryHand, run } from './helpers.js';

const k = s => parseVKey(s);
const isErr = r => r && typeof r === 'object' && typeof r.err === 'string';

test('图鉴条目：每种做法都能合成，至少两种，至少一种用别的卡组', () => checkCatalog(CATALOG));

test('路线：从初等篇 + 本章赠卡出发，集齐本章全部卡组', () => {
  const hand = elementaryHand();
  assert.ok(hand.has('d:Z'), '初等篇应该已经拿到 ℤ');
  for (const g of CHAPTER.unlock.gives) assert.ok(hand.has(g), `拿到 ℤ 时应该附赠 ${g}`);
  hand.walk(WALKTHROUGH);
  for (const c of CATALOG) assert.ok(hand.has(`d:${c.id}`), c.name);
});

test('章节信息', () => {
  assert.equal(CHAPTER.id, 5);
  assert.equal(CHAPTER.unlock.when, 'd:Z');
  assert.ok(CHAPTER.unlock.gives.includes('b:mod'));
  for (const c of CATALOG) {
    assert.equal(c.ch, 5, c.name);
    assert.ok(/^[A-Za-z0-9]+$/.test(c.id), `id ${c.id} 只能用字母数字`);
    assert.ok(Array.isArray(c.list) && c.list.length > 0, `${c.name} 应该是有限卡组`);
    for (const key of c.list) {
      const v = parseVKey(key);
      assert.ok(v && v.t === 'mod', `${c.name} 的成员 ${key} 解析不了`);
      assert.equal(subtypeOf(v), c.type, `${c.name} 的成员 ${key} 类型不对`);
      assert.equal(c.has(v), true, `${c.name} 的 has 应该认 ${key}`);
    }
    // has 不多认：同一个 n 下不在列表里的都不算
    const n = Number(c.type.split(':')[1]);
    const keys = new Set(c.list);
    for (let r = 0; r < n; r++) assert.equal(c.has(M(n, r)), keys.has(`[${r}]${n}`), `${c.name} has([${r}]${n})`);
  }
});

test('key 往返、显示文字、类型标签', () => {
  for (const key of ['[3]12', '[0]2', '[6]7', '[11]12', '[99]100']) {
    const v = parseVKey(key);
    assert.ok(v, key);
    assert.equal(vkey(v), key);
    assert.deepEqual(parseVKey(vkey(v)), v);
  }
  assert.equal(fmtV(k('[3]12')), '[3]₁₂');
  assert.equal(fmtV(k('[0]7')), '[0]₇');
  assert.equal(typeLabel(k('[3]12')), '模 12');
  assert.equal(subtypeOf(k('[3]12')), 'mod:12');
  // 不合法的 key
  assert.equal(parseVKey('[12]12'), null);
  assert.equal(parseVKey('[0]1'), null);
  assert.equal(parseVKey('[-1]12'), null);
  assert.equal(parseVKey('3').t, undefined); // 有理数还是有理数，不会被认成余数
  // M 会把 r 规范到 0 ≤ r < n
  assert.equal(vkey(M(12, -1)), '[11]12');
  assert.equal(vkey(M(12, 25)), '[1]12');
});

test('整数 mod 整数 → 余数；模数、被除数不合法时有解释', () => {
  assert.equal(vkey(binV('mod', R(17), R(5))), '[2]5');
  assert.equal(vkey(binV('mod', R(-1), R(12))), '[11]12');
  assert.equal(vkey(binV('mod', R(24), R(12))), '[0]12');
  assert.equal(vkey(binV('mod', R(0), R(2))), '[0]2');
  assert.equal(vkey(binV('mod', R(5), R(1000))), '[5]1000');
  for (const [x, y] of [
    [R(5), R(1)],
    [R(5), R(0)],
    [R(5), R(-3)],
    [R(5), R(1, 2)],
    [R(1, 2), R(5)],
  ]) {
    const r = binV('mod', x, y);
    assert.ok(isErr(r), `${fmtV(x)} mod ${fmtV(y)} 应该报错`);
  }
  assert.match(binV('mod', R(5), R(1)).err, /不小于 2/);
  assert.match(binV('mod', R(1, 2), R(5)).err, /不是整数/);
  // 余数和分数一起算：分数 p/q 就是 p 乘 q 的逆元；q 没有逆元就没有定义
  assert.equal(vkey(binV('add', k('[0]5'), R(1, 2))), '[3]5');
  assert.equal(binV('add', k('[0]12'), R(1, 2)).reason, 'undefined');
});

test('同一个钟面上的加减乘', () => {
  const a = k('[7]12');
  const b = k('[9]12');
  assert.equal(vkey(binV('add', a, b)), '[4]12');
  assert.equal(vkey(binV('sub', a, b)), '[10]12');
  assert.equal(vkey(binV('sub', b, a)), '[2]12');
  assert.equal(vkey(binV('mul', a, b)), '[3]12');
  assert.equal(vkey(binV('mul', k('[3]12'), k('[4]12'))), '[0]12');
  // 混合运算：整数先化成余数
  assert.equal(vkey(binV('add', a, R(5))), '[0]12');
  assert.equal(vkey(binV('add', R(5), a)), '[0]12');
  assert.equal(vkey(binV('mul', R(3), k('[5]12'))), '[3]12');
  assert.equal(vkey(binV('sub', R(0), k('[5]12'))), '[7]12');
  assert.equal(vkey(binV('mul', R(-1), k('[5]7'))), '[2]7');
  // 分数：分母有逆元就化成余数（[1]₇ + 1/2 = [1]₇ + [4]₇ = [5]₇），没有逆元就没有定义
  const r = binV('add', a, R(1, 2));
  assert.ok(isErr(r));
  assert.equal(r.reason, 'undefined');
  assert.match(r.err, /没有逆元/);
  assert.equal(vkey(binV('add', k('[1]7'), R(1, 2))), '[5]7');
});

test('不同模数不能相加', () => {
  const r = binV('add', k('[1]12'), k('[1]7'));
  assert.ok(isErr(r));
  assert.match(r.err, /模 12/);
  assert.match(r.err, /模 7/);
  for (const op of ['sub', 'mul', 'div']) assert.ok(isErr(binV(op, k('[1]12'), k('[1]7'))), op);
  // 合成台上也是同样的解释
  const res = combine(resolveRef('c:[1]12'), resolveRef('b:add'), resolveRef('c:[1]7'));
  assert.equal(res.ok, false);
  assert.match(res.msg, /钟面/);
});

test('逆元与除法', () => {
  assert.equal(modInv(5, 12), 5);
  assert.equal(modInv(7, 12), 7);
  assert.equal(modInv(3, 7), 5);
  assert.equal(modInv(2, 7), 4);
  assert.equal(modInv(4, 12), null);
  assert.equal(modInv(0, 12), null);
  assert.equal(modInv(1, 2), 1);
  assert.equal(vkey(binV('div', k('[1]7'), k('[3]7'))), '[5]7');
  assert.equal(vkey(binV('div', k('[6]7'), k('[2]7'))), '[3]7');
  assert.equal(vkey(binV('div', k('[7]12'), k('[5]12'))), '[11]12');
  // [6] ÷ [6] 也不行：6 和 12 不互素，"商"不唯一
  assert.ok(isErr(binV('div', k('[6]12'), k('[6]12'))));
  const bad = binV('div', k('[1]12'), k('[4]12'));
  assert.ok(isErr(bad));
  assert.match(bad.err, /最大公约数是 4/);
  const zero = binV('div', k('[1]12'), k('[0]12'));
  assert.ok(isErr(zero));
  assert.match(zero.err, /不能除以/);
  // 除数的写法和它的余数不同（2/5、−2、12）时，先说它在模 n 下是哪张卡，不凭空冒出 [10]₁₂
  assert.match(binV('div', k('[1]12'), R(2, 5)).err, /^2\/5 在模 12 下是 \[10\]₁₂，它没有逆元：10 和 12 的最大公约数是 2/);
  assert.match(binV('div', k('[1]12'), R(-2)).err, /^−2 在模 12 下是 \[10\]₁₂，它没有逆元/);
  assert.match(binV('div', k('[1]12'), R(22)).err, /^22 在模 12 下是 \[10\]₁₂/);
  assert.match(binV('div', k('[1]12'), R(12)).err, /^12 在模 12 下是 \[0\]₁₂，不能除以它/);
  assert.match(binV('div', k('[1]12'), R(12, 5)).err, /^12\/5 在模 12 下是 \[0\]₁₂/);
  assert.equal(binV('div', k('[1]12'), R(2, 5)).reason, 'undefined');
  // 写法和余数一样就不重复说
  assert.match(binV('div', k('[1]12'), R(2)).err, /^\[2\]₁₂ 没有逆元/);
  assert.match(binV('div', k('[1]12'), k('[4]12')).err, /^\[4\]₁₂ 没有逆元/);
  assert.match(binV('div', k('[1]12'), k('[0]12')).err, /^不能除以 \[0\]₁₂/);
  // 1/x 当一元算子：没有逆元的卡算不出
  const recip = powU(NEG1);
  assert.equal(vkey(applyU(recip, k('[5]12'))), '[5]12');
  assert.equal(vkey(applyU(recip, k('[3]7'))), '[5]7');
  assert.ok(isErr(applyU(recip, k('[2]12'))));
});

test('乘方：正指数反复相乘，负指数用逆元，指数必须是整数', () => {
  assert.equal(vkey(binV('pow', k('[3]7'), R(6))), '[1]7');
  assert.equal(vkey(binV('pow', k('[3]7'), R(2))), '[2]7');
  assert.equal(vkey(binV('pow', k('[3]7'), R(0))), '[1]7');
  assert.equal(vkey(binV('pow', k('[3]7'), R(-1))), '[5]7');
  assert.equal(vkey(binV('pow', k('[3]7'), R(-2))), '[4]7');
  assert.equal(vkey(binV('pow', k('[5]12'), R(-1))), '[5]12');
  assert.equal(vkey(binV('pow', k('[2]12'), R(100))), '[4]12');
  assert.equal(vkey(binV('pow', k('[0]12'), R(0))), '[1]12');
  assert.ok(isErr(binV('pow', k('[2]12'), R(-1))));
  assert.ok(isErr(binV('pow', k('[2]12'), R(1, 2))));
  assert.ok(isErr(binV('pow', k('[2]12'), k('[3]12'))));
  assert.ok(isErr(binV('pow', R(2), k('[3]12'))));
  // 平方当一元算子
  assert.equal(vkey(applyU(powU(TWO), k('[3]7'))), '[2]7');
  assert.equal(vkey(applyU(aff(TWO, R(1)), k('[5]12'))), '[11]12');
});

test('余数和别的类型（量、向量、矩阵、多项式）：交给别的类型，不说成"不是整数"', () => {
  const others = ['q:1|1,0,0', 'v:1,0', 'm:1,0,0,1', 'p:1,0'];
  for (const s of others) {
    const o = k(s);
    assert.ok(o, s);
    for (const op of ['add', 'sub', 'mul', 'div', 'pow', 'mod']) {
      for (const [x, y] of [
        [k('[3]12'), o],
        [o, k('[3]12')],
      ]) {
        const r = binV(op, x, y);
        const what = `${fmtV(x)} ${op} ${fmtV(y)}`;
        assert.ok(isErr(r), `${what} 应该报错，得到 ${JSON.stringify(r)}`);
        assert.doesNotMatch(r.err, /NaN|undefined/, `${what}：${r.err}`);
        assert.doesNotMatch(r.err, /不是整数/, `${what}：${r.err}`);
        assert.match(r.err, /模 12/, `${what}：${r.err}`);
      }
    }
  }
  // 合成台上：[3]₁₂ + 1 步，两种顺序都说的是类型，不是"1 步 不是整数"
  for (const [l, r] of [
    ['c:[3]12', 'c:q:1|1,0,0'],
    ['c:q:1|1,0,0', 'c:[3]12'],
  ]) {
    const res = combine(resolveRef(l), resolveRef('b:add'), resolveRef(r));
    assert.equal(res.ok, false);
    assert.doesNotMatch(res.msg, /NaN|undefined|不是整数/, res.msg);
    assert.match(res.msg, /模 12/);
    assert.match(res.msg, /长度/);
  }
  const vm = combine(resolveRef('c:[3]12'), resolveRef('b:mul'), resolveRef('c:v:1,0'));
  assert.equal(vm.ok, false);
  assert.doesNotMatch(vm.msg, /NaN|undefined|不是整数/, vm.msg);
  assert.match(vm.msg, /向量/);
  // 有理数照旧：整数化成余数，分母没有逆元的分数说"没有逆元"
  assert.equal(vkey(binV('add', k('[3]12'), R(10))), '[1]12');
  assert.match(binV('mul', R(1, 2), k('[3]12')).err, /1\/2 在模 12 下不存在/);
});

test('余数再取余：只有模数整除时才行', () => {
  assert.equal(vkey(binV('mod', k('[7]12'), R(2))), '[1]2');
  assert.equal(vkey(binV('mod', k('[7]12'), R(4))), '[3]4');
  assert.equal(vkey(binV('mod', k('[7]12'), R(12))), '[7]12');
  assert.ok(isErr(binV('mod', k('[7]12'), R(5))));
  assert.ok(isErr(binV('mod', k('[7]12'), R(1))));
  assert.ok(isErr(binV('mod', k('[7]12'), k('[2]12'))));
  assert.ok(isErr(binV('mod', R(7), k('[2]12'))));
  // 负数、分数模数也一样：[3]₁₂ 说不清是 3 还是 15，mod −5 和 mod 5 一样没有定义，不是"表示不了"
  for (const y of [R(5), R(-5), R(24), R(-24), R(5, 2), R(-5, 2)]) {
    const r = binV('mod', k('[3]12'), y);
    assert.equal(r.reason, 'undefined', `[3]₁₂ mod ${fmtV(y)}`);
    assert.match(r.err, /说不清是 3 还是 15/, `[3]₁₂ mod ${fmtV(y)}`);
  }
  assert.match(binV('mod', k('[3]12'), R(-5)).err, /对 −5 取余/);
  // 结果不依赖选哪个、只是钟面写不出来的（ℤ/3ℤ、ℚ/⅕ℤ）还是表示不了；对 0 取余没有定义
  for (const y of [R(-3), R(-1), R(1), R(1, 5), R(-12), R(1, 9999999)]) {
    assert.equal(binV('mod', k('[3]12'), y).reason, 'unrepresentable', `[3]₁₂ mod ${fmtV(y)}`);
  }
  assert.equal(binV('mod', k('[3]12'), R(0)).reason, 'undefined');
  // 拼接不归本类型管
  assert.ok(isErr(binV('cat', k('[1]12'), k('[2]12'))));
});

test('错误都带 reason：没有这条法是 type，没有定义是 undefined，表示不了是 unrepresentable', () => {
  const REASONS = ['type', 'undefined', 'unrepresentable'];
  const cases = [
    ['add', k('[1]12'), k('[1]7')], // 不同模数
    ['mul', k('[1]12'), k('[1]7')],
    ['div', k('[1]12'), k('[4]12')], // 没有逆元
    ['div', k('[1]12'), k('[0]12')], // 除以 [0]
    ['pow', k('[2]12'), R(-1)], // 负指数要用逆元
    ['pow', k('[2]12'), R(1, 2)], // 分数指数
    ['pow', k('[2]12'), k('[3]12')], // 指数是余数
    ['pow', R(2), k('[3]12')],
    ['add', k('[3]12'), R(1, 2)], // 分数化不成余数
    ['mul', R(1, 2), k('[3]12')],
    ['mod', k('[7]12'), R(5)], // 5 不整除 12
    ['mod', k('[7]12'), R(1)],
    ['mod', k('[7]12'), k('[2]12')], // 对余数取余
    ['mod', R(7), k('[2]12')],
    ['mod', R(5), R(0)], // 模数不合法
    ['mod', R(5), R(1)],
    ['mod', R(5), R(-3)],
    ['mod', R(5), R(1, 2)],
    ['mod', R(1, 2), R(12)], // 分数取余：2 在模 12 下没有逆元
  ];
  for (const [op, x, y] of cases) {
    const r = binV(op, x, y);
    const what = `${fmtV(x)} ${op} ${fmtV(y)}`;
    assert.ok(isErr(r), `${what} 应该报错`);
    assert.ok(REASONS.includes(r.reason), `${what} 的 reason 是 ${r.reason}`);
  }
  // 当一元算子用时 reason 也带出来
  assert.ok(REASONS.includes(applyU(powU(NEG1), k('[2]12')).reason));
  // 具体的类别
  assert.equal(binV('div', k('[1]12'), k('[4]12')).reason, 'undefined', '[4]₁₂ 没有逆元');
  assert.equal(binV('add', k('[1]12'), k('[1]7')).reason, 'type', '不同模数');
  assert.equal(binV('pow', k('[2]12'), R(1, 2)).reason, 'type', '余数开方不是单值的，没有这条法');
});

test('视野与探针：全部 n 个余数', () => {
  const w = windowFor('mod:12');
  assert.equal(w.length, 12);
  assert.deepEqual(w.map(vkey), Array.from({ length: 12 }, (_, r) => `[${r}]12`));
  assert.equal(probesFor('mod:7').length, 7);
  assert.equal(windowFor('mod:2').length, 2);
  assert.ok(windowFor('mod:100000').length <= 200, '模数太大时视野要截断');
  // 只有凑满一整圈才算精确的有限卡组：少了余数可能只是样本不够
  const ex = TYPES.get('mod').exhaustive;
  assert.equal(ex('mod:12', windowFor('mod:12')), true);
  assert.equal(ex('mod:12', windowFor('mod:12').slice(1)), false);
  assert.equal(ex('mod:23', windowFor('mod:23')), true);
  assert.equal(ex('mod:23', windowFor('mod:23').slice(0, 20)), false);
});

test('图鉴里写「群」的卡组都真的是群，运算符号也对', () => {
  const OP = { '+': 'add', '×': 'mul' };
  for (const c of CATALOG) {
    const D = resolveRef(`d:${c.id}`).v;
    const g = groupInfo(D);
    assert.ok(g, `${c.name} 应该能判断是不是群`);
    if (c.struct === '群') {
      const op = OP[c.groupOp];
      assert.ok(op, `${c.name} 的 groupOp ${c.groupOp} 不认识`);
      assert.equal(g[op].group, true, `${c.name} 对 ${c.groupOp} 应该是群`);
    }
  }
  const g12 = groupInfo(resolveRef('d:Z12').v);
  assert.equal(g12.add.group, true);
  assert.equal(g12.mul.group, false);
  assert.equal(g12.mul.closed, true);
  const u12 = groupInfo(resolveRef('d:U12').v);
  assert.equal(u12.mul.group, true);
  assert.equal(u12.add.closed, false);
  const u7 = groupInfo(resolveRef('d:U7').v);
  assert.equal(u7.mul.group, true);
  assert.equal(u7.add.closed, false);
});

test('合成台上的用法与文字', () => {
  const c = ref => resolveRef(ref);
  // 单卡 mod 单卡
  assert.equal(combine(c('c:17'), c('b:mod'), c('c:5')).item.id, 'c:[2]5');
  // 空位绑定：x mod 12
  const r = combine(null, c('b:mod'), c('c:12'));
  assert.ok(r.ok);
  assert.equal(fmtU(r.item.v), 'x mod 12');
  assert.equal(vkey(applyU(r.item.v, R(-5))), '[7]12');
  // 卡组 mod 单卡 认成 ℤ₁₂；对任何 n ≥ 2 都能算
  assert.equal(combine(c('d:Z'), c('b:mod'), c('c:12')).item.id, 'd:Z12');
  assert.equal(combine(c('d:Z'), c('b:mod'), c('c:7')).item.id, 'd:Z7');
  const z5 = combine(c('d:Z'), c('b:mod'), c('c:5'));
  assert.ok(z5.ok);
  assert.ok(z5.item.id.startsWith('d:~'), 'ℤ₅ 不在图鉴里，是自造卡组');
  // 模 5 只有 5 个余数，视野就是全部，所以结果是精确的有限卡组而不是近似卡组
  assert.equal(z5.item.v.approx, false);
  assert.equal(z5.item.v.list.length, 5);
  const big = combine(c('d:Z'), c('b:mod'), c('c:1000'));
  assert.ok(big.ok);
  // ℤ mod 1 在绑定 x mod 1 时就被拦下了（核心的 bindRight：对任何输入都算不出），还没走到分岔
  assert.equal(combine(c('d:Z'), c('b:mod'), c('c:1')).ok, false);
  // 单卡 mod 卡组：每张卡都算不出（模数不能是余数），引擎给出解释而不是空集
  const none = combine(c('c:5'), c('b:mod'), c('d:Z12'));
  assert.equal(none.ok, false);
  assert.ok(none.msg.length > 0);
  // 做法文字
  assert.equal(recipeText(['d:Z', 'b:mod', 'c:12']), 'ℤ mod 12');
  assert.equal(recipeText(['d:Z12', 'u:recip', null]), 'ℤ₁₂ 经 1/x');
  assert.equal(recipeText(['c:[3]12', 'm:closure', 'b:add']), '[3]₁₂ 在 + 下封闭');
  // 图鉴之外：ℤ₁₂ 经 x² 是 {0, 1, 4, 9}
  const sq = combine(c('d:Z12'), c('u:sq'), null);
  assert.ok(sq.ok);
  assert.deepEqual(sq.item.v.list.map(vkey), ['[0]12', '[1]12', '[4]12', '[9]12']);
  assert.equal(groupInfo(sq.item.v).mul.closed, true);
  // 不同模数的卡组两两运算，一张都算不出
  const mixed = combine(c('d:Z12'), c('b:add'), c('d:Z7'));
  assert.equal(mixed.ok, false);
  // 复合的化简不放过没有定义的地方：x/2 在 ℤ₁₂ 上没有定义（2 没有逆元），所以 x/2 接 2x 不能化成 x
  const half = aff(R(1, 2), ZERO);
  const dbl = aff(TWO, ZERO);
  const hd = compose(half, dbl);
  assert.equal(hd.t, 'chain');
  assert.equal(fmtU(hd), '2(x/2)');
  assert.equal(fmtU(compose(dbl, half)), '(2x)/2', '两种顺序写法分得开');
  assert.equal(applyU(hd, k('[1]12')).reason, 'undefined');
  assert.equal(applyU(compose(dbl, half), k('[1]12')).reason, 'undefined');
  assert.equal(vkey(applyU(hd, k('[1]7'))), '[1]7', '2 在模 7 下有逆元，照样回到原来的数');
  assert.equal(vkey(applyU(hd, R(3))), '3');
  assert.equal(applyU(compose(aff(ONE, R(1, 2)), dbl), k('[1]12')).reason, 'undefined', 'x + 1/2 接 2x 不能化成 2x + 1');
  assert.equal(applyU(compose(half, aff(ZERO, R(5))), k('[1]12')).reason, 'undefined', 'x/2 接常数 5 不能化成 5');
  assert.equal(fmtU(compose(half, aff(R(1, 3), ZERO))), 'x/6', '分母的素因子都还在，照样化简');
  assert.equal(fmtU(compose(dbl, aff(ONE, ONE))), '2x + 1');
  // 合成台上：[1]₁₂ 经「x/2 接 2x」是没有定义的缺口；ℤ₁₂ 经「2x 接 x/2」不是时钟；ℤ、[1]₇ 照旧
  const hg = combine(c('u:half'), c('m:compose'), c('u:dbl'));
  assert.ok(hg.ok);
  const h1 = combine(c('c:[1]12'), hg.item, null);
  assert.ok(h1.ok && h1.item === null && h1.holes[0].v.kind === 'undefined', h1.msg);
  const h2 = combine(c('d:Z12'), combine(c('u:dbl'), c('m:compose'), c('u:half')).item, null);
  assert.notEqual(h2.item?.id, 'd:Z12');
  assert.equal(combine(c('c:[1]7'), hg.item, null).item.id, 'c:[1]7');
  assert.equal(combine(c('d:Z'), hg.item, null).item.id, 'd:Z');
});

test('另外几种自然的做法也能被认出来', () => {
  const ok = (recipe, id) => {
    const r = run(recipe);
    assert.ok(r.ok, `${recipe.join(' ')}：${r.msg}`);
    assert.equal(r.item.id, id, recipe.join(' '));
  };
  ok(['d:Z12', 'b:pow', 'c:-1'], 'd:U12');
  ok(['d:Sign', 'b:mod', 'c:12'], 'd:~' + run(['d:Sign', 'b:mod', 'c:12']).item.id.slice(3)); // {[1],[11]} 不在图鉴里
  ok(['d:Odd', 'b:mod', 'c:2'], 'd:~' + run(['d:Odd', 'b:mod', 'c:2']).item.id.slice(3)); // 只有 [1]₂
  ok(['d:Z7', 'b:mod', 'c:7'], 'd:Z7');
  ok(['d:Sub3', 'b:add', 'd:Sub3'], 'd:Sub3');
  ok(['d:Sub3', 'b:mul', 'd:Sub2'], 'd:Sub6');
  ok(['d:U12', 'b:mul', 'd:U12'], 'd:U12');
  ok(['d:U7', 'b:mul', 'd:QR7'], 'd:U7');
  ok(['d:QR7', 'b:mul', 'c:[3]7'], 'd:~' + run(['d:QR7', 'b:mul', 'c:[3]7']).item.id.slice(3)); // 非平方数 {3,5,6}
  ok(['d:Z12', 'b:sub', 'c:[1]12'], 'd:Z12');
  ok(['c:[1]12', 'm:extend', 'u:succ'], 'd:Z12');
  ok(['c:[1]7', 'm:extend', 'u:dbl'], 'd:QR7');
  ok(['d:Z2', 'b:add', 'd:Z2'], 'd:Z2');
});

test('合成速度：两两运算和封闭都在 200ms 内', () => {
  const c = ref => resolveRef(ref);
  const cases = [
    () => combine(c('d:Z12'), c('b:mul'), c('d:Z12')),
    () => combine(c('d:Z12'), c('b:add'), c('d:Z12')),
    () => combine(c('c:[1]12'), c('m:closure'), c('b:add')),
    () => combine(c('d:Z'), c('b:mod'), c('c:97')),
    () => combine(c('c:[1]97'), c('m:closure'), c('b:add')),
    () => combine(c('d:Z'), c('b:mod'), c('c:10000')),
  ];
  for (const f of cases) {
    const t0 = performance.now();
    const r = f();
    const dt = performance.now() - t0;
    assert.ok(r.ok, r.msg);
    assert.ok(dt < 200, `用了 ${dt.toFixed(0)}ms`);
  }
});

test('绑定算子的显示', () => {
  assert.equal(fmtU(bindU('mul', 'r', k('[3]12'))), 'x × [3]₁₂');
  assert.equal(fmtU(bindU('div', 'l', k('[1]12'))), '[1]₁₂ ÷ x');
  // 分数、负数常数加括号；x ^ c 和 x^(1/5) 一样写，不写 x ^ 1/13（会读成 x¹/13）
  assert.equal(fmtU(bindU('pow', 'r', R(1, 13))), 'x^(1/13)');
  assert.equal(fmtU(bindU('pow', 'r', R(-1, 13))), 'x^(−1/13)');
  assert.equal(fmtU(bindU('mod', 'r', R(-5))), 'x mod (−5)');
  assert.equal(fmtU(bindU('mul', 'r', R(1, 13))), 'x × (1/13)');
  assert.equal(fmtU(bindU('mod', 'r', R(12))), 'x mod 12');
  // 负号开头的输入加括号：(−3) mod 12、−(−3)、2·(−3)，不写 −−3
  assert.equal(fmtU(bindU('mod', 'r', R(12)), '−3'), '(−3) mod 12');
  assert.equal(fmtU(aff(NEG1, ZERO), '−3'), '−(−3)');
  assert.equal(fmtU(aff(NEG1, ONE), '−3'), '1 − (−3)');
  assert.equal(fmtU(aff(TWO, ZERO), '−3'), '2·(−3)');
  // c ÷ x 写成 2/(3x)，不写 2/x/3；1/x 接 2x、x 接 1/x 的写法也不含糊
  const d23 = combine(resolveRef('c:2/3'), resolveRef('b:div'), null).item.v;
  assert.equal(fmtU(d23), '2/(3x)');
  assert.equal(fmtU(d23, '0'), '2/(3·0)');
  assert.equal(fmtU(compose(powU(NEG1), aff(R(1, 3), ZERO))), '1/(3x)');
  assert.equal(fmtU(compose(aff(TWO, ZERO), powU(NEG1))), '1/(2x)');
  // 0 代进 1/x、2/(3x)：说"不能除以 0"，不说"0 的负数次方"
  assert.deepEqual(applyU(powU(NEG1), ZERO), { err: '不能除以 0。', reason: 'undefined' });
  assert.deepEqual(applyU(d23, ZERO), { err: '不能除以 0。', reason: 'undefined' });
  assert.deepEqual(applyU(powU(R(-2)), ZERO), { err: '不能除以 0。', reason: 'undefined' });
  assert.match(applyU(powU(R(-2, 3)), ZERO).err, /0 的 0 次方、0 的负数次方/, '分数次方照旧');
});
