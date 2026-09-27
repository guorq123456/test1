import test from 'node:test';
import assert from 'node:assert/strict';

import {
  CATALOG,
  WALKTHROUGH,
  CHAPTER,
  NAMED_UN,
  QUESTS,
  P,
  X,
  poly,
  keyP,
  parsePolyKey,
  fmtPoly,
  derive,
  integrate,
  WINDOW_P,
  PROBES_P,
  PROBES_SMALL_P,
  SIZE_CAP,
  MAX_DEG,
  sizeP,
  isP,
} from '../src/domains/poly.js';
import { checkCatalog, elementaryHand, run } from './helpers.js';
import { R, ZERO, ONE, OVER, isR } from '../src/math.js';
import { binV, vkey, fmtV, parseVKey, sizeV, typeLabel, subtypeOf, isV } from '../src/values.js';
import { applyU, compose, invertU, fmtU, namedU, fnU, isId, aff, ukey } from '../src/unary.js';
import { combine, resolveRef, recipeText } from '../src/rules.js';
import { groupInfo, previewDeck } from '../src/decks.js';
import { GIFTS } from '../src/content.js';

const k = v => (isV(v) ? vkey(v) : v);
const D = namedU('D');
const INT = namedU('INT');

// ───────────────────────── 图鉴与路线 ─────────────────────────

test('图鉴条目：每种做法都能合成出来，至少两种做法，至少一种用别的卡组', () => {
  checkCatalog(CATALOG);
  assert.ok(CATALOG.length >= 6 && CATALOG.length <= 8);
  for (const c of CATALOG) {
    assert.equal(c.ch, CHAPTER.id);
    assert.ok(['群', '集合'].includes(c.struct), c.name);
    if (c.struct === '群') assert.ok(c.groupOp, `${c.name} 是群却没写运算`);
    for (const key of ['short', 'name', 'preview', 'note', 'desc', 'hint']) assert.ok(c[key], `${c.id} 缺 ${key}`);
  }
});

test('路线：从初等篇 + 赠卡出发集齐本章', () => {
  const hand = elementaryHand();
  for (const ref of CHAPTER.unlock.gives) assert.ok(hand.has(resolveRef(ref).id), `没有拿到赠卡 ${ref}`);
  assert.deepEqual(GIFTS['d:Q'].filter(g => CHAPTER.unlock.gives.includes(g)), CHAPTER.unlock.gives);
  hand.walk(WALKTHROUGH);
  for (const c of CATALOG) assert.ok(hand.has(`d:${c.id}`), c.name);
  assert.ok(QUESTS.every(q => typeof q.done === 'function'));
  assert.ok(QUESTS.at(-1).done(id => hand.has(id)));
});

test('章节与算子引用', () => {
  assert.equal(CHAPTER.id, 6);
  assert.equal(CHAPTER.unlock.when, 'd:Q');
  assert.equal(resolveRef('c:p:1,0').id, 'c:p:1,0');
  assert.equal(resolveRef('u:D').id, 'u:named(D)');
  assert.equal(resolveRef('u:INT').id, 'u:named(INT)');
  assert.equal(resolveRef('u:mulx').id, 'u:bind(mul,r,p:1,0)');
  assert.ok(NAMED_UN.every(u => u.id && u.name && u.f));
});

test('标 "群" 的卡组真的是群：有限的用 groupInfo 核对，无限的 ℚ∖{0} 在探针上核对乘法封闭、单位元、逆元', () => {
  for (const c of CATALOG.filter(c => c.struct === '群')) {
    const deck = resolveRef(`d:${c.id}`).v;
    if (deck.list) {
      const g = groupInfo(deck);
      assert.equal(g[c.groupOp === '+' ? 'add' : 'mul'].group, true, c.name);
    }
  }
  const qnz = resolveRef('d:Qnz').v;
  assert.equal(qnz.type, 'q');
  const xs = ['1', '-1', '2', '1/2', '-3/4', '7', '-1/7', '97/2'].map(parseVKey);
  assert.equal(qnz.has(ZERO), false);
  assert.equal(qnz.has(ONE), true);
  for (const a of xs) {
    assert.equal(qnz.has(a), true);
    assert.equal(qnz.has(binV('div', ONE, a)), true, `${k(a)} 的倒数`);
    for (const b of xs) assert.equal(qnz.has(binV('mul', a, b)), true, `${k(a)} × ${k(b)}`);
  }
  // 多项式卡组都不是群：一次式相加可能变成数
  assert.equal(k(binV('add', P(1, 1), P(-1, 1))), '2');
  assert.ok(CATALOG.filter(c => c.type === 'poly').every(c => c.struct === '集合'));
});

// ───────────────────────── 值、key、显示 ─────────────────────────

test('常数多项式不存在：结果是常数就返回有理数', () => {
  assert.equal(k(binV('sub', X, X)), '0');
  assert.ok(isR(binV('sub', X, X)));
  assert.equal(k(binV('sub', P(1, 1), P(1, 0))), '1');
  assert.equal(k(binV('add', P(2, 0, 1), P(-2, 0, 1))), '2');
  assert.equal(k(poly([R(3)])), '3');
  assert.equal(k(poly([])), '0');
  assert.equal(k(poly([R(0), R(0)])), '0');
  assert.equal(k(binV('pow', P(1, 1), ZERO)), '1');
  assert.equal(k(binV('mul', P(1, 1), ZERO)), '0');
});

test('key 往返、显示文字、大小、小字', () => {
  const cases = [
    ['p:1,0', 'x'],
    ['p:1,0,0', 'x²'],
    ['p:1,2,1', 'x² + 2x + 1'],
    ['p:1,0,-1,0', 'x³ − x'],
    ['p:1/2,1', 'x/2 + 1'],
    ['p:1/2,-1', 'x/2 − 1'],
    ['p:-1,0', '−x'],
    ['p:-3/2,0,1/3', '−3x²/2 + 1/3'],
    ['p:2,-3', '2x − 3'],
    ['p:-1,1', '−x + 1'],
    ['p:1,0,0,0,0,0,0,0,0,0,0,0,0', 'x¹²'],
  ];
  for (const [key, text] of cases) {
    const v = parseVKey(key);
    assert.ok(isP(v), key);
    assert.equal(vkey(v), key);
    assert.equal(keyP(v), key);
    assert.equal(fmtV(v), text);
    assert.equal(subtypeOf(v), 'poly');
  }
  assert.equal(fmtPoly(P(1, 2, 1).c, '(x + 1)'), '(x + 1)² + 2(x + 1) + 1');
  assert.equal(typeLabel(P(1, 0)), '一次多项式');
  assert.equal(typeLabel(P(1, 0, 0)), '二次多项式');
  assert.equal(typeLabel(P(1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)), '十二次多项式');
  assert.equal(sizeV(P(1, 0)), 2);
  assert.equal(sizeV(P(3, 1, -5)), 7);
  assert.equal(sizeV(P('1/2', 0)), 3);
  assert.equal(k(P('1/2', -1)), 'p:1/2,-1');
});

test('不合法的 key 解析不出来', () => {
  for (const s of ['p:', 'p:1', 'p:0,1', 'p:0,0', 'p:a,1', '1,0', 'p:1,,0', 'p:1/0,1', '3', '1/2']) {
    assert.equal(parsePolyKey(s), null, s);
  }
  assert.equal(k(parseVKey('3')), '3');
  assert.equal(parsePolyKey('p:' + Array(14).fill('1').join(',')), null, '次数超过上限');
});

// ───────────────────────── 运算 ─────────────────────────

test('加减乘、和有理数互通', () => {
  assert.equal(k(binV('add', X, ONE)), 'p:1,1');
  assert.equal(k(binV('add', ONE, X)), 'p:1,1');
  assert.equal(k(binV('sub', R(3), X)), 'p:-1,3');
  assert.equal(k(binV('mul', R(2), P(1, 1))), 'p:2,2');
  assert.equal(k(binV('mul', P(1, 1), P(1, -1))), 'p:1,0,-1');
  assert.equal(k(binV('mul', P(1, 1), P(1, 1))), 'p:1,2,1');
  assert.equal(k(binV('mul', P('1/2', 0), P(2, 0))), 'p:1,0,0');
  assert.equal(k(binV('div', P(2, 4), R(2))), 'p:1,2');
  assert.equal(k(binV('div', X, R(-1, 2))), 'p:-2,0');
  assert.equal(k(binV('pow', P(1, 1), R(3))), 'p:1,3,3,1');
  assert.equal(k(binV('pow', X, R(12))), 'p:1,0,0,0,0,0,0,0,0,0,0,0,0');
  assert.equal(k(binV('pow', P(1, 1), ONE)), 'p:1,1');
  assert.equal(k(applyU(aff(R(2), ONE), X)), 'p:2,1');
});

test('次数超过 12、系数太大都返回 OVER', () => {
  assert.equal(binV('pow', X, R(13)), OVER);
  assert.equal(binV('mul', P(1, 0, 0, 0, 0, 0, 0), P(1, 0, 0, 0, 0, 0, 0, 0)), OVER);
  assert.equal(binV('mul', P(1e7, 0), P(1e7, 0)), OVER);
  assert.equal(k(binV('pow', P(1, 0, 0), R(6))), 'p:1,0,0,0,0,0,0,0,0,0,0,0,0', '刚好 12 次还可以');
  assert.equal(binV('pow', P(1, 0, 0), R(7)), OVER);
  assert.equal(applyU(fnU(P(1, 0, 0, 0, 0)), P(1, 0, 0, 0, 0)), OVER, '4 次复合 4 次得 16 次');
  assert.equal(integrate(P(1, ...Array(12).fill(0))), OVER);
  assert.equal(MAX_DEG, 12);
});

test('没有定义的运算给出解释', () => {
  const err = r => (r && r.err) || '';
  assert.match(err(binV('div', X, X)), /分式/);
  assert.match(err(binV('div', ONE, X)), /分式/);
  assert.match(err(binV('div', X, ZERO)), /0/);
  assert.match(err(binV('pow', R(2), X)), /指数/);
  assert.match(err(binV('pow', X, R(1, 2))), /整数次方/);
  assert.match(err(binV('pow', X, R(-1))), /分式/);
  assert.match(err(binV('mod', X, R(2))), /带余除法/);
  assert.match(err(binV('cat', X, X)), /拼接/);
  // 通过合成台看到的文字
  const c = ref => resolveRef(ref);
  const r = combine(c('c:p:1,0'), c('b:div'), c('c:p:1,1'));
  assert.equal(r.ok, false);
  assert.match(r.msg, /分式/);
  assert.equal(combine(c('c:p:1,0'), c('b:pow'), c('c:13')).ok, false);
  assert.equal(combine(null, c('b:pow'), c('c:p:1,0')).ok, false, 'x ^ x 对任何输入都算不出来');
});

// ───────────────────────── 求导与积分 ─────────────────────────

test('求导、积分', () => {
  assert.equal(k(derive(P(1, 2, 1))), 'p:2,2');
  assert.equal(k(derive(P(1, 0, 0, 1))), 'p:3,0,0');
  assert.equal(k(derive(X)), '1');
  assert.equal(k(derive(R(5))), '0');
  assert.equal(k(derive(P('1/2', 0, 0))), 'p:1,0');
  assert.equal(k(integrate(R(3))), 'p:3,0');
  assert.equal(k(integrate(ZERO)), '0');
  assert.equal(k(integrate(X)), 'p:1/2,0,0');
  assert.equal(k(integrate(P(2, 2))), 'p:1,2,0');
  assert.equal(k(integrate(P(3, 0, 0))), 'p:1,0,0,0');
  assert.equal(k(applyU(D, P(1, 1))), '1');
  assert.equal(k(applyU(INT, ONE)), 'p:1,0');
  assert.match(derive({ t: 'nope' }).err ?? '', /求导/);
});

test('先积分再求导回到原样；先求导再积分会丢掉常数项（数学事实，不是 bug）', () => {
  for (const p of [X, P(1, 1), P(2, -3, 5), R(7)]) {
    assert.equal(k(applyU(D, applyU(INT, p))), k(p), `D(INT(${k(p)}))`);
  }
  // 求导把常数项抹掉了：x + 1 和 x 求导都是 1，所以积分回来只能得到 x
  assert.equal(k(applyU(INT, applyU(D, P(1, 1)))), 'p:1,0');
  assert.equal(k(applyU(INT, applyU(D, P(1, 2, 3)))), 'p:1,2,0');
  assert.equal(k(applyU(INT, applyU(D, R(7)))), '0');
  // 所以：积分有逆（求导），求导没有逆
  assert.equal(ukey(invertU(INT)), 'named(D)');
  assert.equal(invertU(D), null);
  // 复合：先积分再求导化简成恒等；先求导再积分不能化简，算出来确实丢常数项
  assert.ok(isId(compose(INT, D)));
  const DI = compose(D, INT);
  assert.equal(DI.t, 'chain');
  assert.equal(k(applyU(DI, P(1, 1))), 'p:1,0');
  assert.equal(fmtU(DI), '∫₀ˣ (x′) dx');
  assert.equal(fmtU(D), 'x′');
  assert.equal(fmtU(compose(aff(ONE, ONE), D)), '(x + 1)′');
  assert.equal(fmtU(INT), '∫₀ˣ x dx');
  assert.equal(fmtU(compose(aff(ONE, ONE), INT)), '∫₀ˣ (x + 1) dx');
  // 合成台上「逆」的反应
  const c = ref => resolveRef(ref);
  const inv = combine(c('u:D'), c('m:inverse'), null);
  assert.equal(inv.ok, false);
  assert.match(inv.msg, /没有逆/);
  assert.equal(combine(c('u:INT'), c('m:inverse'), null).item.id, 'u:named(D)');
});

// ───────────────────────── 当函数用 ─────────────────────────

test('代入求值、复合、公式、逆', () => {
  const p = P(1, 2, 1); // x² + 2x + 1
  assert.equal(k(applyU(fnU(p), R(3))), '16');
  assert.equal(k(applyU(fnU(p), R(-1))), '0');
  assert.equal(k(applyU(fnU(p), R(1, 2))), '9/4');
  assert.equal(k(applyU(fnU(p), P(1, -1))), 'p:1,0,0'); // (x − 1 + 1)² = x²
  assert.equal(k(applyU(fnU(P(1, 0, 0)), P(1, 1))), 'p:1,2,1'); // (x + 1)²
  assert.equal(k(applyU(fnU(X), P(3, 1))), 'p:3,1');
  assert.equal(fmtU(fnU(p)), 'x² + 2x + 1');
  assert.equal(fmtU(compose(aff(ONE, ONE), fnU(p))), '(x + 1)² + 2(x + 1) + 1');
  assert.equal(fmtU(compose(fnU(p), aff(R(2), ZERO))), '2(x² + 2x + 1)');
  // 一次式当函数用可以倒推
  assert.equal(ukey(invertU(fnU(P(2, 1)))), 'aff(1/2,-1/2)');
  assert.equal(ukey(invertU(fnU(P(-1, 3)))), 'aff(-1,3)');
  assert.equal(invertU(fnU(p)), null);
  // 合成台：多项式放中间
  const c = ref => resolveRef(ref);
  assert.equal(combine(c('c:3'), c('c:p:1,2,1'), null).item.id, 'c:16');
  assert.equal(combine(null, c('c:p:1,1'), c('c:p:1,1')).item.id, 'c:p:1,2');
  assert.equal(combine(c('d:L1'), c('c:p:2,1'), null).item.id, 'd:L1', '一次式代进一次式还是一次式');
  assert.equal(applyU(fnU(p), { t: 'nope' }), null, '不是卡的东西代不进去');
});

// ───────────────────────── 视野与探针 ─────────────────────────

test('视野和探针：都是合法的非常数多项式，不重复，小探针大小不超过上限', () => {
  const keys = new Set();
  for (const v of WINDOW_P) {
    assert.ok(isP(v));
    assert.equal(k(parseVKey(vkey(v))), vkey(v));
    assert.ok(!keys.has(vkey(v)), `视野里重复的 ${vkey(v)}`);
    keys.add(vkey(v));
  }
  assert.ok(WINDOW_P.length >= 100 && WINDOW_P.length <= 300, `视野有 ${WINDOW_P.length} 张`);
  assert.ok(PROBES_SMALL_P.every(isP) && PROBES_P.every(isP));
  assert.ok(PROBES_P.length > PROBES_SMALL_P.length);
  const sk = new Set(PROBES_SMALL_P.map(vkey));
  assert.equal(new Set(PROBES_P.map(vkey)).size, PROBES_P.length, '探针不重复');
  assert.ok(PROBES_SMALL_P.every(v => sizeP(v) <= SIZE_CAP), '小探针都在大小上限内');
  assert.ok(PROBES_P.filter(v => sk.has(vkey(v))).length === PROBES_SMALL_P.length);
  // 每个卡组在小探针里至少有两个成员，并且探针能把图鉴里的卡组两两区分开
  for (const c of CATALOG.filter(c => c.type === 'poly')) {
    assert.ok(PROBES_SMALL_P.filter(c.has).length >= 2, `${c.name} 在小探针里成员太少`);
  }
  const sig = c => PROBES_P.map(v => (c.has(v) ? 1 : 0)).join('');
  const polys = CATALOG.filter(c => c.type === 'poly');
  for (const a of polys) for (const b of polys) if (a !== b) assert.notEqual(sig(a), sig(b), `${a.name} 和 ${b.name} 在探针上分不开`);
  // has 拿到别的类型不会报错
  for (const c of CATALOG) assert.equal(c.has(R(2)) && c.type === 'poly', false);
  for (const c of CATALOG) assert.equal(c.has(X) && c.type === 'q', false);
});

test('单次合成在 200ms 内（两两运算、封闭、像）', () => {
  const cases = [
    ['d:Prop', 'b:add', 'd:Q'],
    ['d:Root0Q', 'b:add', 'd:Q'],
    ['d:Q', 'b:mul', 'd:Q2'],
    ['d:L1', 'b:mul', 'd:L1'],
    ['d:Q2', 'b:mul', 'd:Q2'],
    ['d:L1', 'm:closure', 'b:add'],
    ['d:L1', 'm:closure', 'b:mul'],
    ['d:Q2', 'm:closure', 'b:add'],
    ['d:Q2', 'm:closure', 'b:mul'],
    ['d:Q2', 'u:D', null],
    ['d:L1', 'u:cube', null],
  ];
  for (const rec of cases) {
    const t0 = performance.now();
    const r = run(rec);
    const ms = performance.now() - t0;
    assert.ok(r.ok, rec.join(' '));
    assert.ok(ms < 200, `${rec.join(' ')} 用了 ${ms.toFixed(0)}ms`);
  }
});

// ───────────────────────── 卡组的认与不认 ─────────────────────────

test('跨章联系：求导、积分把卡组连起来', () => {
  const id = rec => run(rec).item.id;
  assert.equal(id(['d:Prop', 'u:D', null]), 'd:Qnz');
  assert.equal(id(['d:L1', 'u:D', null]), 'd:Qnz');
  assert.equal(id(['d:Qnz', 'u:INT', null]), 'd:Prop');
  assert.equal(id(['d:Sq2', 'u:D', null]), 'd:Prop');
  assert.equal(id(['d:Root0Q', 'u:D', null]), 'd:L1');
  assert.equal(id(['d:Q2', 'u:D', null]), 'd:L1');
  assert.equal(id(['d:L1', 'u:INT', null]), 'd:Root0Q');
  assert.equal(id(['d:Q', 'u:recip', null]), 'd:Qnz', 'ℚ 取倒数也是 ℚ∖{0}');
});

test('不该被认成图鉴卡组的不会被认错', () => {
  const r = rec => run(rec);
  // ℕ⁺·x 不是正比例式（少了负的和分数）
  const nx = r(['d:Np', 'b:mul', 'c:p:1,0']);
  assert.ok(nx.ok && nx.item.id.startsWith('d:~'));
  // x 在 − 下封闭：x − x = 0 混进了数，成了混合卡组
  const zx = r(['c:p:1,0', 'm:closure', 'b:sub']);
  assert.ok(zx.ok && zx.item.id.startsWith('d:~'));
  assert.equal(zx.item.v.type, 'set');
  // 平方项 + 一次式 缺了 x² + 1 这类卡，不是二次式
  const q = r(['d:Sq2', 'b:add', 'd:L1']);
  assert.ok(q.ok && q.item.id.startsWith('d:~'));
  // 一次式 × 一次式 只有能因式分解的二次式，也不是二次式
  const ll = r(['d:L1', 'b:mul', 'd:L1']);
  assert.ok(ll.ok && ll.item.id.startsWith('d:~'));
  assert.ok(!ll.item.v.has(P(1, 0, 1)));
  // 单项式是无限卡组，不会被当成有限卡组
  const mono = r(['c:p:1,0', 'm:extend', 'u:mulx']);
  assert.equal(mono.item.id, 'd:Mono');
  assert.ok(!mono.item.v.list);
});

test('做法文字与预览', () => {
  assert.equal(recipeText(['d:Qnz', 'u:INT', null]), 'ℚ∖{0} 经 ∫₀ˣ x dx');
  assert.equal(recipeText(['d:Prop', 'b:add', 'd:Q']), 'ax + ℚ');
  assert.equal(recipeText(['c:p:1,0', 'm:extend', 'u:mulx']), 'x 延展 x × x');
  assert.equal(recipeText(['d:L1', 'c:p:1,0,0', null]), '(ax + b) 经 x²');
  assert.equal(previewDeck(resolveRef('d:Mono').v, 4), '{x, x², x³, x⁴, …}');
  assert.equal(previewDeck(resolveRef('d:L1').v, 3), '{x, −x, x + 1, …}');
  const one = run(['c:p:1,1', 'm:extend', 'u:mulx']);
  assert.ok(one.ok);
  assert.equal(previewDeck(one.item.v), '{x + 1, x² + x, x³ + x², x⁴ + x³, x⁵ + x⁴, …}');
});
