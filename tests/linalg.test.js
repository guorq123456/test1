import test from 'node:test';
import assert from 'node:assert/strict';

import {
  CATALOG,
  WALKTHROUGH,
  CHAPTER,
  NAMED_UN,
  V,
  Mx,
  I2,
  det,
  invM,
  powM,
  mulM,
  transpose,
  dot,
  WINDOW_V,
  WINDOW_M,
  PROBES_SMALL_V,
  PROBES_SMALL_M,
  SIZE_CAP,
} from '../src/domains/linalg.js';
import { binV, vkey, fmtV, parseVKey, subtypeOf, typeLabel, windowFor, probesFor, smallProbesFor, sizeV, isV } from '../src/values.js';
import { applyU, namedU, bindU, powU, aff, fmtU, compose, invertU, isId } from '../src/unary.js';
import { groupInfo, previewDeck } from '../src/decks.js';
import { R, NEG1, TWO, OVER } from '../src/math.js';
import { combine, resolveRef, recipeText } from '../src/rules.js';
import { checkCatalog, elementaryHand, run } from './helpers.js';

const k = s => parseVKey(s);
const isErr = r => r && typeof r === 'object' && typeof r.err === 'string';
const key = r => (isV(r) ? vkey(r) : r);

// ───────────────────────── 图鉴、路线、章节 ─────────────────────────

test('图鉴条目：每种做法都能合成，至少两种，至少一种用别的卡组', () => checkCatalog(CATALOG));

test('路线：从初等篇 + 本章赠卡出发，集齐本章全部卡组', () => {
  const hand = elementaryHand();
  assert.ok(hand.has('d:Q'), '初等篇应该已经拿到 ℚ');
  for (const g of CHAPTER.unlock.gives) assert.ok(hand.has(resolveRef(g).id), `拿到 ℚ 时应该附赠 ${g}`);
  assert.ok(hand.has('u:named(TR)'));
  hand.walk(WALKTHROUGH);
  for (const c of CATALOG) assert.ok(hand.has(`d:${c.id}`), c.name);
});

test('章节信息与图鉴条目的形式', () => {
  assert.equal(CHAPTER.id, 7);
  assert.equal(CHAPTER.unlock.when, 'd:Q');
  for (const g of ['c:v:1,0', 'c:v:0,1', 'b:cat', 'u:TR', 'u:DET']) assert.ok(CHAPTER.unlock.gives.includes(g), g);
  assert.deepEqual(
    NAMED_UN.map(u => u.id),
    ['TR', 'DET', 'TRACE'],
  );
  const ids = new Set();
  for (const c of CATALOG) {
    assert.equal(c.ch, 7, c.name);
    assert.ok(/^[A-Za-z0-9]+$/.test(c.id), `id ${c.id} 只能用字母数字`);
    assert.ok(!ids.has(c.id), `重复的 id ${c.id}`);
    ids.add(c.id);
    assert.ok(['vec', 'mat'].includes(c.type), `${c.name} 的类型 ${c.type}`);
    assert.ok(['群', '集合'].includes(c.struct), c.name);
    if (c.struct === '群') assert.ok(['+', '×'].includes(c.groupOp), `${c.name} 要写 groupOp`);
    for (const f of ['short', 'name', 'preview', 'note', 'desc', 'hint']) assert.ok(typeof c[f] === 'string' && c[f].length > 0, `${c.id}.${f}`);
    if (c.list) {
      for (const s of c.list) {
        const v = parseVKey(s);
        assert.ok(v, `${c.name} 的成员 ${s} 解析不了`);
        assert.equal(subtypeOf(v), c.type, `${c.name} 的成员 ${s} 类型不对`);
        assert.equal(c.has(v), true, `${c.name} 的 has 应该认 ${s}`);
      }
      // has 不多认：视野里不在列表里的都不算
      const keys = new Set(c.list);
      for (const v of windowFor(c.type)) assert.equal(c.has(v), keys.has(vkey(v)), `${c.name} has(${vkey(v)})`);
    }
    // has 只认本类型
    assert.equal(c.has(R(1)), false, `${c.name} 不该认有理数`);
    assert.equal(c.has(c.type === 'vec' ? I2 : V(1, 0)), false, `${c.name} 不该认另一种类型`);
  }
});

// ───────────────────────── key、显示、类型标签 ─────────────────────────

test('key 往返、显示文字、类型标签、大小', () => {
  for (const s of ['v:1,0', 'v:-1,1/2', 'v:0,0', 'v:-3/4,-5', 'm:1,0,0,1', 'm:0,-1,1,0', 'm:1/2,-1/3,7,0', 'm:0,0,0,0']) {
    const v = parseVKey(s);
    assert.ok(v, s);
    assert.equal(vkey(v), s);
    assert.deepEqual(parseVKey(vkey(v)), v);
  }
  assert.equal(fmtV(k('v:1,2')), '(1, 2)');
  assert.equal(fmtV(k('v:-1,1/2')), '(−1, 1/2)');
  assert.equal(fmtV(k('m:1,0,0,1')), '[1 0; 0 1]');
  assert.equal(fmtV(k('m:0,-1,1,0')), '[0 −1; 1 0]');
  assert.equal(fmtV(k('m:1/2,-1/3,7,0')), '[1/2 −1/3; 7 0]');
  assert.equal(typeLabel(k('v:1,2')), '向量');
  assert.equal(typeLabel(k('m:1,0,0,1')), '矩阵');
  assert.equal(subtypeOf(k('v:1,2')), 'vec');
  assert.equal(subtypeOf(k('m:1,0,0,1')), 'mat');
  // 快捷写法
  assert.equal(vkey(V(1, 0)), 'v:1,0');
  assert.equal(vkey(V('1/2', -1)), 'v:1/2,-1');
  assert.equal(vkey(Mx(0, -1, 1, 0)), 'm:0,-1,1,0');
  assert.equal(vkey(I2), 'm:1,0,0,1');
  // 不合法的 key
  for (const s of ['v:1', 'v:1,0,0', 'm:1,0', 'm:1,0,0', 'v:1/0,1', 'v:a,b', 'm:1,2,3,4/0', 'v:1.5,0', 'v: 1,0', 'v:1,0 ']) {
    assert.equal(parseVKey(s), null, s);
  }
  assert.equal(parseVKey('3').t, undefined); // 有理数还是有理数
  assert.equal(parseVKey('[3]12').t, 'mod'); // 余数不受影响
  // 大小：分量 height 的最大值；矩阵里 ±2 这样的整数多算 1
  assert.equal(sizeV(k('v:1,0')), 1);
  assert.equal(sizeV(k('v:2,1/3')), 3);
  assert.equal(sizeV(k('v:0,0')), 1);
  assert.equal(sizeV(k('m:1,0,0,1')), 1);
  assert.equal(sizeV(k('m:1/2,0,0,1')), 2);
  assert.equal(sizeV(k('m:2,0,0,1')), 3);
  assert.equal(sizeV(k('m:3/2,0,0,1')), 3);
});

// ───────────────────────── 向量运算 ─────────────────────────

test('向量的加减、数乘、点积、拼接', () => {
  assert.equal(key(binV('add', k('v:1,2'), k('v:1/2,-1'))), 'v:3/2,1');
  assert.equal(key(binV('sub', k('v:1,2'), k('v:1/2,-1'))), 'v:1/2,3');
  assert.equal(key(binV('mul', R(3), k('v:1,-2'))), 'v:3,-6');
  assert.equal(key(binV('mul', k('v:1,-2'), R(1, 2))), 'v:1/2,-1');
  assert.equal(key(binV('div', k('v:1,-2'), R(2))), 'v:1/2,-1');
  assert.equal(key(binV('mul', k('v:1,2'), k('v:3,4'))), '11');
  assert.equal(key(binV('mul', k('v:1,0'), k('v:0,1'))), '0');
  assert.equal(key(dot(V(1, 2), V(-2, 1))), '0');
  assert.equal(key(binV('cat', k('v:1,2'), k('v:3,4'))), 'm:1,3,2,4');
  assert.equal(key(binV('cat', k('v:1,0'), k('v:0,1'))), 'm:1,0,0,1');
  assert.equal(key(binV('cat', k('v:0,1'), k('v:-1,0'))), 'm:0,-1,1,0');
  // 一元算子作用在向量上：2x、x × (1, 0)
  assert.equal(key(applyU(aff(TWO, R(0)), k('v:1,2'))), 'v:2,4');
  assert.equal(key(applyU(bindU('mul', 'r', k('v:1,0')), R(3))), 'v:3,0');
  assert.equal(key(applyU(bindU('mul', 'l', k('m:0,-1,1,0')), k('v:1,0'))), 'v:0,1');
  // 数字太大
  assert.equal(binV('mul', R(1e7), k('v:1e0,0'.replace('1e0', '2'))), OVER);
});

test('向量的错误情况都有解释', () => {
  const bad = (op, x, y, re) => {
    const r = binV(op, x, y);
    assert.ok(isErr(r), `${op} ${fmtV(x)} ${fmtV(y)} 应该报错，得到 ${JSON.stringify(r)}`);
    if (re) assert.match(r.err, re);
  };
  bad('add', k('v:1,2'), R(1), /分量/);
  bad('sub', R(1), k('v:1,2'), /分量/);
  bad('add', k('v:1,2'), k('m:1,0,0,1'), /向量.*矩阵/);
  bad('div', k('v:1,2'), k('v:3,4'), /点积/);
  bad('div', k('v:1,2'), R(0), /不能除以 0/);
  bad('div', R(1), k('v:1,2'));
  bad('div', k('v:1,2'), k('m:1,0,0,1'), /逆矩阵/);
  bad('mul', k('v:1,2'), k('m:1,0,0,1'), /矩阵放左边/);
  bad('pow', k('v:1,2'), R(2));
  bad('pow', R(2), k('v:1,2'));
  bad('mod', k('v:1,2'), R(2));
  bad('cat', k('v:1,2'), R(1), /拼接/);
  bad('cat', R(1), k('v:1,2'));
  bad('cat', k('m:1,0,0,1'), k('m:1,0,0,1'), /列向量/);
  // 合成台上给出的是同样的解释
  const res = combine(resolveRef('c:v:1,2'), resolveRef('b:add'), resolveRef('c:3'));
  assert.equal(res.ok, false);
  assert.match(res.msg, /分量/);
});

// ───────────────────────── 矩阵运算 ─────────────────────────

test('矩阵的加减、数乘、乘法、乘向量', () => {
  assert.equal(key(binV('add', k('m:1,2,3,4'), k('m:1,0,0,1'))), 'm:2,2,3,5');
  assert.equal(key(binV('sub', k('m:1,2,3,4'), k('m:1,0,0,1'))), 'm:0,2,3,3');
  assert.equal(key(binV('mul', R(1, 2), k('m:1,2,3,4'))), 'm:1/2,1,3/2,2');
  assert.equal(key(binV('mul', k('m:1,2,3,4'), R(-1))), 'm:-1,-2,-3,-4');
  assert.equal(key(binV('div', k('m:1,2,3,4'), R(2))), 'm:1/2,1,3/2,2');
  assert.equal(key(binV('mul', k('m:1,2,3,4'), k('m:0,1,1,0'))), 'm:2,1,4,3');
  assert.equal(key(binV('mul', k('m:0,1,1,0'), k('m:1,2,3,4'))), 'm:3,4,1,2');
  assert.equal(key(binV('mul', k('m:1,2,3,4'), k('m:1,0,0,1'))), 'm:1,2,3,4');
  assert.equal(key(binV('mul', k('m:0,-1,1,0'), k('v:1,0'))), 'v:0,1');
  assert.equal(key(binV('mul', k('m:0,-1,1,0'), k('v:0,1'))), 'v:-1,0');
  assert.equal(key(binV('mul', k('m:1,2,3,4'), k('v:1,1'))), 'v:3,7');
  // 矩阵乘法不交换：R × F ≠ F × R
  const Rm = Mx(0, -1, 1, 0);
  const F = Mx(1, 0, 0, -1);
  assert.notEqual(vkey(mulM(Rm, F)), vkey(mulM(F, Rm)));
  assert.equal(vkey(mulM(Rm, F)), 'm:0,1,1,0');
  assert.equal(vkey(mulM(F, Rm)), 'm:0,-1,-1,0');
  assert.equal(vkey(powM(Rm, 2)), 'm:-1,0,0,-1');
  // 数字太大
  assert.equal(binV('mul', R(1e7), k('m:2,0,0,2')), OVER);
});

test('逆矩阵、除法、乘方', () => {
  assert.equal(key(invM(Mx(1, 1, 1, -1))), 'm:1/2,1/2,1/2,-1/2');
  assert.equal(key(invM(Mx(0, -1, 1, 0))), 'm:0,1,-1,0');
  assert.equal(invM(Mx(1, 2, 2, 4)), null);
  assert.equal(invM(Mx(0, 0, 0, 0)), null);
  assert.equal(key(binV('pow', k('m:1,1,1,-1'), NEG1)), 'm:1/2,1/2,1/2,-1/2');
  assert.equal(key(binV('pow', k('m:1,1,0,1'), R(5))), 'm:1,5,0,1');
  assert.equal(key(binV('pow', k('m:1,1,0,1'), R(-3))), 'm:1,-3,0,1');
  assert.equal(key(binV('pow', k('m:0,-1,1,0'), R(4))), 'm:1,0,0,1');
  assert.equal(key(binV('pow', k('m:0,-1,1,0'), R(3))), 'm:0,1,-1,0');
  assert.equal(key(binV('pow', k('m:0,-1,1,0'), R(-1))), 'm:0,1,-1,0');
  assert.equal(key(binV('pow', k('m:1,2,2,4'), R(0))), 'm:1,0,0,1');
  assert.equal(key(binV('pow', k('m:0,-1,1,0'), R(1001))), 'm:0,-1,1,0');
  assert.equal(binV('pow', k('m:2,0,0,2'), R(100)), OVER);
  assert.equal(key(binV('div', k('m:1,1,0,1'), k('m:1,1,0,1'))), 'm:1,0,0,1');
  assert.equal(key(binV('div', k('m:1,0,0,1'), k('m:0,-1,1,0'))), 'm:0,1,-1,0');
  assert.equal(key(binV('div', R(2), k('m:1,1,1,-1'))), 'm:1,1,1,-1');
  // 1/x 当一元算子：没有逆的矩阵算不出
  assert.equal(key(applyU(powU(NEG1), k('m:0,-1,1,0'))), 'm:0,1,-1,0');
  assert.ok(isErr(applyU(powU(NEG1), k('m:1,2,2,4'))));
  // 错误情况
  const bad = (op, x, y, re) => {
    const r = binV(op, x, y);
    assert.ok(isErr(r), `${op} ${fmtV(x)} ${fmtV(y)} 应该报错`);
    if (re) assert.match(r.err, re);
  };
  bad('div', k('m:1,1,0,1'), k('m:1,2,2,4'), /行列式是 0/);
  bad('pow', k('m:1,2,2,4'), NEG1, /行列式是 0/);
  bad('pow', k('m:1,1,1,-1'), R(1, 2), /整数次方/);
  bad('pow', k('m:1,1,1,-1'), k('m:1,0,0,1'), /整数/);
  bad('pow', R(2), k('m:1,0,0,1'));
  bad('add', k('m:1,0,0,1'), R(2), /2 × I/);
  bad('sub', R(2), k('m:1,0,0,1'));
  bad('div', k('m:1,0,0,1'), R(0), /不能除以 0/);
  bad('div', k('m:1,0,0,1'), k('v:1,0'));
  bad('mod', k('m:1,0,0,1'), R(2));
  bad('cat', k('m:1,0,0,1'), k('v:1,0'));
  const res = combine(resolveRef('c:m:1,2,2,4'), resolveRef('u:recip'), null);
  assert.equal(res.ok, false);
  assert.match(res.msg, /行列式是 0/);
});

test('转置、行列式、迹', () => {
  assert.equal(key(transpose(Mx(1, 2, 3, 4))), 'm:1,3,2,4');
  assert.equal(key(det(Mx(1, 2, 3, 4))), '-2');
  assert.equal(key(det(Mx(0, -1, 1, 0))), '1');
  assert.equal(key(det(Mx(1, 2, 2, 4))), '0');
  assert.equal(key(det(Mx('1/2', 0, 0, '1/2'))), '1/4');
  const TR = namedU('TR');
  const DET = namedU('DET');
  const TRACE = namedU('TRACE');
  assert.equal(key(applyU(TR, k('m:1,2,3,4'))), 'm:1,3,2,4');
  assert.equal(key(applyU(DET, k('m:1,2,3,4'))), '-2');
  assert.equal(key(applyU(TRACE, k('m:1,2,3,4'))), '5');
  assert.equal(key(applyU(DET, k('m:1,0,0,-1'))), '-1');
  for (const f of [TR, DET, TRACE]) {
    assert.ok(isErr(applyU(f, k('v:1,2'))), '向量算不了');
    assert.ok(isErr(applyU(f, R(3))), '数算不了');
    assert.match(applyU(f, k('v:1,2')).err, /只对矩阵/);
  }
  assert.match(applyU(TR, k('v:1,2')).err, /列向量/);
  // 转置是自己的逆；行列式没有逆
  assert.equal(fmtU(TR), 'xᵀ');
  assert.equal(fmtU(DET), 'det(x)');
  assert.equal(fmtU(TRACE), 'tr(x)');
  assert.ok(isId(compose(TR, TR)));
  assert.equal(fmtU(invertU(TR)), 'xᵀ');
  assert.equal(invertU(DET), null);
  assert.equal(invertU(TRACE), null);
  // 合成台：逆
  const inv = combine(resolveRef('u:TR'), resolveRef('m:inverse'), null);
  assert.ok(inv.ok);
  assert.equal(inv.item.id, 'u:named(TR)');
  const noInv = combine(resolveRef('u:DET'), resolveRef('m:inverse'), null);
  assert.equal(noInv.ok, false);
});

test('绑定算子与做法文字的显示', () => {
  assert.equal(fmtU(bindU('mul', 'r', k('v:1,0'))), 'x × (1, 0)');
  assert.equal(fmtU(bindU('mul', 'l', k('m:0,-1,1,0'))), '[0 −1; 1 0] × x');
  assert.equal(fmtU(bindU('cat', 'r', k('v:0,1'))), 'x | (0, 1)');
  assert.equal(fmtU(compose(bindU('mul', 'l', k('m:0,-1,1,0')), namedU('TR'))), '([0 −1; 1 0] × x)ᵀ');
  assert.equal(recipeText(['d:Q', 'b:mul', 'c:v:1,0']), 'ℚ × (1, 0)');
  assert.equal(recipeText(['d:Mat2', 'u:recip', null]), 'M₂ 经 1/x');
  assert.equal(recipeText(['c:m:0,-1,1,0', 'b:pow', 'd:Z']), '[0 −1; 1 0] ^ ℤ');
  assert.equal(recipeText(['d:Xaxis', 'b:cat', 'd:Yaxis']), 'ℚe₁ | ℚe₂');
  assert.equal(recipeText(['d:Rot4', 'm:union', 'd:Refl']), 'C₄ ∪ 反射');
  // 空位绑定
  const r = combine(resolveRef('c:v:1,0'), resolveRef('b:cat'), null);
  assert.ok(r.ok);
  assert.equal(fmtU(r.item.v), '(1, 0) | x');
  assert.equal(key(applyU(r.item.v, k('v:0,1'))), 'm:1,0,0,1');
});

// ───────────────────────── 视野与探针 ─────────────────────────

test('视野与探针：不大，小探针都在视野里', () => {
  assert.equal(windowFor('vec').length, 49);
  assert.equal(WINDOW_V.length, 49);
  assert.equal(WINDOW_M.length, 91);
  assert.ok(windowFor('mat').length <= 100);
  assert.ok(WINDOW_V.length * WINDOW_V.length <= 5000, '向量两两运算不超过几千次');
  assert.ok(WINDOW_M.length * WINDOW_M.length <= 10000, '矩阵两两运算不超过一万次');
  const inWindow = (xs, w) => xs.every(x => w.some(y => vkey(x) === vkey(y)));
  assert.ok(inWindow(smallProbesFor('vec'), WINDOW_V));
  assert.ok(inWindow(smallProbesFor('mat'), WINDOW_M));
  assert.ok(PROBES_SMALL_V.every(v => sizeV(v) <= SIZE_CAP));
  assert.ok(PROBES_SMALL_M.every(v => sizeV(v) <= SIZE_CAP));
  assert.ok(probesFor('vec').length > WINDOW_V.length);
  assert.ok(probesFor('mat').length > WINDOW_M.length);
  // 视野里没有重复
  for (const w of [WINDOW_V, WINDOW_M]) assert.equal(new Set(w.map(vkey)).size, w.length);
  // 探针能把图鉴里同类型的卡组两两区分开
  for (const type of ['vec', 'mat']) {
    const cs = CATALOG.filter(c => c.type === type);
    const probes = probesFor(type);
    for (let i = 0; i < cs.length; i++) {
      for (let j = i + 1; j < cs.length; j++) {
        assert.ok(
          probes.some(x => cs[i].has(x) !== cs[j].has(x)),
          `${cs[i].name} 和 ${cs[j].name} 在探针上分不开`,
        );
      }
    }
  }
});

// ───────────────────────── 群 ─────────────────────────

test('有限卡组：写「群」的都真的是群，写「集合」的都不是', () => {
  const OP = { '+': 'add', '×': 'mul' };
  for (const c of CATALOG.filter(c => c.list)) {
    const D = resolveRef(`d:${c.id}`).v;
    const g = groupInfo(D);
    assert.ok(g, `${c.name} 应该能判断是不是群`);
    if (c.struct === '群') {
      assert.equal(g[OP[c.groupOp]].group, true, `${c.name} 对 ${c.groupOp} 应该是群`);
    } else {
      assert.equal(g.add.group, false, `${c.name} 对 + 不该是群`);
      assert.equal(g.mul.group, false, `${c.name} 对 × 不该是群`);
    }
  }
  const c4 = groupInfo(resolveRef('d:Rot4').v);
  assert.equal(c4.mul.group, true);
  assert.equal(c4.add.closed, false);
  assert.equal(vkey(c4.mul.identity), 'm:1,0,0,1');
  const d4 = groupInfo(resolveRef('d:Dih4').v);
  assert.equal(d4.mul.group, true);
  assert.equal(d4.mul.identity && vkey(d4.mul.identity), 'm:1,0,0,1');
  assert.equal(groupInfo(resolveRef('d:Refl').v).mul.closed, false);
  assert.equal(groupInfo(resolveRef('d:Cross').v).add.closed, false);
  // D₄ 不交换
  const Rm = k('m:0,-1,1,0');
  const F = k('m:1,0,0,-1');
  assert.notEqual(vkey(binV('mul', Rm, F)), vkey(binV('mul', F, Rm)));
});

test('无限卡组：写「群」的在视野样本上封闭、有单位元、有逆元', () => {
  const OP = { '+': 'add', '×': 'mul' };
  for (const c of CATALOG.filter(c => !c.list && c.struct === '群')) {
    const op = OP[c.groupOp];
    const sample = windowFor(c.type).filter(c.has);
    assert.ok(sample.length >= 3, `${c.name} 的样本太少`);
    for (const a of sample) {
      for (const b of sample) {
        const z = binV(op, a, b);
        assert.ok(isV(z) && c.has(z), `${c.name}：${fmtV(a)} ${c.groupOp} ${fmtV(b)} 跑出去了`);
      }
    }
    const e = sample.find(e => sample.every(a => vkey(binV(op, e, a)) === vkey(a) && vkey(binV(op, a, e)) === vkey(a)));
    assert.ok(e, `${c.name} 没有单位元`);
    for (const a of sample) {
      const ai = op === 'add' ? binV('sub', e, a) : binV('pow', a, NEG1);
      assert.ok(isV(ai) && c.has(ai), `${c.name}：${fmtV(a)} 的逆元不在里面`);
      assert.equal(vkey(binV(op, a, ai)), vkey(e), `${c.name}：${fmtV(a)} 乘逆元不是单位元`);
    }
  }
});

// ───────────────────────── 认卡组 ─────────────────────────

test('另外几种自然的做法也能被认出来；近似但不相同的不会被误认', () => {
  const got = recipe => {
    const r = run(recipe);
    assert.ok(r.ok, `${recipe.join(' ')}：${r.msg}`);
    return r.item.id;
  };
  const is = (recipe, id) => assert.equal(got(recipe), id, recipe.join(' '));
  const unnamed = recipe => assert.ok(got(recipe).startsWith('d:~'), `${recipe.join(' ')} 不该被认成图鉴卡组`);
  is(['d:Xaxis', 'b:add', 'd:Xaxis'], 'd:Xaxis');
  is(['d:Yaxis', 'b:sub', 'd:Xaxis'], 'd:Plane');
  is(['d:Plane', 'b:mul', 'd:Q'], 'd:Plane');
  is(['d:Plane', 'm:closure', 'b:add'], 'd:Plane');
  is(['d:Plane', 'b:add', 'c:v:1/2,0'], 'd:Plane');
  is(['d:Lattice', 'm:closure', 'b:add'], 'd:Lattice');
  is(['d:Rot4', 'b:mul', 'd:Rot4'], 'd:Rot4');
  is(['d:Dih4', 'b:mul', 'd:Dih4'], 'd:Dih4');
  is(['d:Dih4', 'b:mul', 'd:Rot4'], 'd:Dih4');
  is(['d:Diag', 'b:mul', 'd:Diag'], 'd:Diag');
  is(['d:Diag', 'u:TR', null], 'd:Diag');
  is(['d:Anti', 'u:TR', null], 'd:Anti');
  is(['d:Mat2', 'u:TR', null], 'd:Mat2');
  is(['d:Scalar', 'b:add', 'd:Scalar'], 'd:Scalar');
  is(['d:Scalar', 'b:mul', 'd:Mat2'], 'd:Mat2');
  is(['d:Mat2', 'b:add', 'd:Mat2'], 'd:Mat2');
  is(['d:Mat2', 'b:mul', 'd:Mat2'], 'd:Mat2');
  is(['d:GL2', 'b:mul', 'd:GL2'], 'd:GL2');
  is(['d:GL2', 'b:div', 'd:GL2'], 'd:GL2');
  is(['d:Dih4', 'b:mul', 'd:GL2'], 'd:GL2');
  is(['d:Dih4', 'u:DET', null], 'd:Sign'); // 8 个对称的行列式只有 ±1
  is(['d:Refl', 'b:mul', 'c:m:1,0,0,-1'], 'd:Rot4'); // 反射乘反射是旋转
  {
    // 向量没有乘方，一张都算不出：引擎给出解释而不是空集
    const r = run(['d:Plane', 'b:pow', 'c:2']);
    assert.equal(r.ok, false);
    assert.match(r.msg, /乘方/);
  }
  // 近似但不同
  unnamed(['d:Z', 'b:mul', 'c:m:1,0,0,1']); // ℤ·I 不是 ℚ·I
  unnamed(['d:Z', 'b:mul', 'c:v:1,0']); // ℤe₁ 不是 x 轴
  unnamed(['d:Lattice', 'b:cat', 'd:Lattice']); // M₂(ℤ) 不是 M₂
  unnamed(['d:Lattice', 'b:add', 'c:v:1/2,0']); // 平移后的格点
  unnamed(['d:Rot4', 'm:union', 'c:m:1,0,0,-1']); // 差三张才是 D₄
  unnamed(['d:Diag', 'm:inter', 'd:Dih4']); // 克莱因四元群，不在图鉴里
  unnamed(['d:Anti', 'b:mul', 'd:Anti']); // 反对角乘反对角是对角，但视野里凑不齐对角矩阵
  unnamed(['c:m:1,1,0,1', 'b:pow', 'd:Z']); // 剪切
  unnamed(['d:Rot4', 'u:DET', null]); // {1}
  // 交、并
  assert.equal(previewDeck(run(['d:Xaxis', 'm:inter', 'd:Yaxis']).item.v), '{(0, 0)}');
  assert.equal(previewDeck(run(['d:Diag', 'm:inter', 'd:Dih4']).item.v), '{[−1 0; 0 −1], [−1 0; 0 1], [1 0; 0 −1], [1 0; 0 1]}');
  // 延展：从 e₁ 出发反复转 90°
  const rot = combine(resolveRef('c:m:0,-1,1,0'), resolveRef('b:mul'), null);
  assert.ok(rot.ok);
  assert.equal(fmtU(rot.item.v), '[0 −1; 1 0] × x');
  const orbit = combine(resolveRef('c:v:1,0'), resolveRef('m:extend'), rot.item);
  assert.ok(orbit.ok);
  assert.equal(orbit.item.id, 'd:Cross');
  // 单卡运算
  assert.equal(combine(resolveRef('c:v:1,0'), resolveRef('b:cat'), resolveRef('c:v:0,1')).item.id, 'c:m:1,0,0,1');
  assert.equal(combine(resolveRef('c:m:0,-1,1,0'), resolveRef('b:pow'), resolveRef('c:2')).item.id, 'c:m:-1,0,0,-1');
  assert.equal(combine(resolveRef('c:v:1,2'), resolveRef('b:mul'), resolveRef('c:v:3,4')).item.id, 'c:11');
  // 两个无限卡组一张都算不出（向量除以向量）：引擎带出解释，而不是给一个空卡组
  const none = combine(resolveRef('d:Plane'), resolveRef('b:div'), resolveRef('d:Plane'));
  assert.equal(none.ok, false);
  assert.ok(none.msg.length > 0);
});

test('合成速度：图鉴做法、路线和常见的两两运算都在 200ms 内', () => {
  const c = ref => resolveRef(ref);
  const cases = [
    ...CATALOG.flatMap(x => x.recipes.map(recipe => () => run(recipe))),
    () => combine(c('d:Q'), c('b:mul'), c('d:Mat2')),
    () => combine(c('d:Mat2'), c('b:mul'), c('d:Mat2')),
    () => combine(c('d:GL2'), c('b:div'), c('d:GL2')),
    () => combine(c('d:Plane'), c('b:mul'), c('d:Q')),
    () => combine(c('d:Plane'), c('b:cat'), c('d:Plane')),
    () => combine(c('d:Diag'), c('m:closure'), c('b:mul')),
    () => combine(c('d:GL2'), c('m:closure'), c('b:mul')),
    () => combine(c('c:m:0,-1,1,0'), c('b:pow'), c('c:1000000')),
  ];
  for (const f of cases) {
    const t0 = performance.now();
    const r = f();
    const dt = performance.now() - t0;
    assert.ok(r.ok, r.msg);
    assert.ok(dt < 200, `用了 ${dt.toFixed(0)}ms`);
  }
  const hand = elementaryHand();
  for (const [l, m, r, e] of WALKTHROUGH) {
    const t0 = performance.now();
    hand.step(l, m, r, e);
    assert.ok(performance.now() - t0 < 200, `${l} ${m} ${r} 太慢`);
  }
});
