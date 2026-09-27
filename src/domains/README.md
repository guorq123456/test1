# 领域模块约定

每个高等篇领域是 `src/domains/<name>.js` 里的一个模块。它做三件事：

1. **注册类型**：告诉引擎这个领域的单卡长什么样、怎么运算（`registerType`）。
2. **注册算子**：这个领域特有的一元算子（`registerNamed`），以及处理跨类型运算的处理器（`registerBin`）。
3. **导出内容**：章节、图鉴卡组、任务、路线。

模块只能改自己的文件：`src/domains/<name>.js`、`tests/<name>.test.js`。核心文件（`src/math.js`、`values.js`、`unary.js`、`decks.js`、`rules.js`、`content.js`、`catalog.js`）不要改；发现核心 bug 时在报告里说明。

## 引擎里已经有的东西

- 有理数 `R(n, d)`，`{n, d}` 对象，`isR`、`add/sub/mul/div/rpow`、`rkey`、`fmtR`、`height`（分子分母最大值）、`OVER`（溢出标记）。见 `src/math.js`。
- 类型系统 `src/values.js`：`registerType(def)`、`registerBin(handler)`、`binV(op, x, y)`、`vkey`、`fmtV`、`isV`、`parseVKey`、`typeOf`、`BIN`（二元算子表：add sub mul div pow mod cat）。
- 一元算子 `src/unary.js`：`registerNamed(def)`、`namedU(id)`、`bindU(op, side, c)`、`fnU(v)`、`applyU(f, x)`、`aff(a, b)`、`powU(n)`。
- 卡组 `src/decks.js`：由引擎自动处理，领域模块通常不用碰。

## registerType(def)

```js
registerType({
  t: 'mod',                       // 类型名
  name: '余数',                    // 中文名
  label: v => `模 ${v.n}`,        // 卡片小字（可选）
  key: v => `[${v.r}]${v.n}`,     // 唯一字符串，也是存档格式。不能和有理数的 "-3" "1/2" 混淆
  parseKey: s => ...,             // key → 值；不是本类型的 key 返回 null
  fmt: v => `[${v.r}]${subscript(v.n)}`,   // 显示文字，可以含 \n（矩阵分两行）
  size: v => 1,                   // "大小"，限制封闭、延展的增长。有理数是 height
  cmp: (a, b) => ...,             // 排序（可选，默认按 key）
  sub: v => `mod:${v.n}`,         // 子类型（可选）。同一子类型的值才会被放进同一个卡组比对
  window: [...],                  // 视野：有代表性的一批值。集合运算（封闭、两两运算、像）在它上面进行
  windowFor: sub => [...],        // 有子类型时按子类型给视野（可选）
  probes: [...],                  // 探针：判断两个卡组是否相同时逐一比对
  probesFor: sub => [...],        // 同上（可选）
  probesSmall: [...],             // 小探针（可选）：近似卡组只比对这些。默认等于 probes
  sizeCap: 20,                    // 两两运算结果的大小上限（可选，默认 20）
  bin(op, x, y) { ... },          // 二元运算，见下
  call(v, x) { ... },             // 可选：把这张卡当函数用（多项式代入）。有它，这张卡就能放在合成台中间
  fmtCall(v, s) { ... },          // 可选：当函数用时的公式，s 是输入的写法（通常是 'x'）
  invertFn(v) { ... },            // 可选：当函数用时的逆算子（返回一元算子或 null）
  fmtBind(op, side, c, s) { ... },// 可选：自定义 "x op c" 的公式写法，返回 null 用默认
});
```

### bin(op, x, y) 的约定

只要 x 或 y 是本类型，就会被调用（先试 x 的类型，再试 y 的类型）。返回：

| 返回 | 含义 |
|---|---|
| 值 | 算出来了 |
| `OVER` | 数字太大 |
| `null` | 没有定义（比如除以 0、不是有理数） |
| `{ err: '原因' }` | 没有定义，并且给玩家一句解释（推荐） |
| `undefined` | 本类型不处理这种组合，交给别的处理器 |

跨类型的组合（比如 `整数 mod 整数 → 余数`）两个操作数都是有理数，类型 `q` 不会处理，这时用 `registerBin((op, x, y) => ...)` 注册一个全局处理器，同样的返回约定。

已有的 `BIN` 算子：`add`(+) `sub`(−) `mul`(×) `div`(÷) `pow`(^) `mod`(mod) `cat`(|)。不要加新的二元算子；需要新的一元变换用 `registerNamed`。

## registerNamed(def)

```js
registerNamed({
  id: 'D',                       // 唯一 id
  name: '求导',
  fmt: s => `d/dx(${s})`,        // 公式写法，s 是输入的写法
  apply: x => ...,               // 输入一个值，返回 值 | OVER | null | {err}
  inverse: 'INT',                // 可选：逆算子的 id（互为逆时两边都写）
  desc: '……',                    // 可选：说明文字
});
```

## 导出

```js
export const CHAPTER = {
  id: 5,                          // 章节号：模运算 5，多项式 6，向量矩阵 7，量纲 8
  title: '时钟与余数',
  desc: '一句话',
  intro: '两三句话的章节引言（第 8 章写具身认知的叙事：人怎样用身体丈量世界）',
  unlock: { when: 'd:Z', gives: ['b:mod', 'c:[1]12'], note: '拿到 ℤ 时……' },  // 解锁条件和赠卡
};

export const NAMED_UN = [          // 让 `u:<id>` 引用能找到具名算子；name 是卡上显示的名字
  { id: 'D', name: '求导', f: namedU('D') },
];

export const BIN_INFO = { mod: { desc: '……' } };   // 可选：二元算子的说明

export const CATALOG = [ /* 图鉴卡组，见下 */ ];

export const QUESTS = [            // 本章任务（可选，1～3 个）。done(has) 里 has(id) 查玩家有没有这张卡
  { id: 'mod1', title: '……', text: '……', done: has => has('d:Z12') },
];

export const WALKTHROUGH = [       // 从"集齐初等篇 + 本章赠卡"出发，集齐本章所有卡组的一条路线
  ['d:Z', 'b:mod', 'c:12', 'd:Z12'],   // [左, 中, 右, 期望得到的 id]；空格子写 null
  ...
];
```

### 图鉴卡组

```js
{
  id: 'Z12',                       // 唯一，只用字母数字
  short: 'ℤ₁₂',                    // 卡上的名字
  name: '时钟',                    // 全名
  ch: 5,
  type: 'mod:12',                  // 成员的（子）类型，必须和 subtypeOf(成员) 一致
  preview: '{[0], [1], …, [11]}',  // 图鉴里显示的内容
  list: ['[0]12', '[1]12', ...],   // 有限卡组写出全部成员的 key（可选；无限卡组不写）
  struct: '群',                    // '群' 或 '集合'
  groupOp: '+',                    // struct 是群时写运算符号
  note: '为什么是群 / 不是群',
  desc: '一句话介绍',
  hint: '给玩家的提示',
  has: v => ...,                   // 成员判断。只会收到本类型的值
  recipes: [                       // 至少两种做法，至少一种用到别的卡组（d:xxx，不能是自己）
    ['d:Z', 'b:mod', 'c:12'],      // [左, 中, 右]，空格子写 null
    ['c:[1]12', 'm:closure', 'b:add'],
  ],
}
```

引用写法：`c:<key>` 单卡（有理数 `c:3` `c:1/2`，其他类型用本类型的 key），`b:<op>` 二元算子，`u:<id>` 具名一元算子（初等篇已有 succ pred neg dbl half id recip sq cube sqrt exp2 log2 sign），`m:<构造算子>`（extend closure inverse compose union inter），`d:<卡组 id>`。

## 合成规则（引擎已经实现，领域模块只提供运算）

- `单卡 二元算子 单卡` → 单卡（`binV`）
- `空 二元算子 单卡` / `单卡 二元算子 空` → 一元算子 `x ∘ c` / `c ∘ x`
- `卡组 二元算子 单卡` → 卡组里每张卡都做 `x ∘ c`（像）
- `卡组 二元算子 卡组` → 两两运算
- `卡组 一元算子` → 像；`单卡 一元算子` → 单卡
- `单卡 延展 一元算子` → 轨道 {c, f(c), f(f(c)), …}；进入循环或算不下去就是有限卡组
- `卡组/单卡 封闭 二元算子` → 反复组合直到没有新卡（在视野里算）
- `并`、`交`、`逆`、`复合`
- 有 `call` 的单卡放在中间 → 当一元算子用

### 卡组怎么被认出来

合成出的卡组会和图鉴里**同类型**的卡组逐一比对：

- 有限卡组：成员列表完全相同。
- 视野里算出来的近似卡组（两两运算、封闭、不可逆的像）：算出来的每个成员都在图鉴卡组里，并且图鉴卡组在 `probesSmall` 里的成员都被算出来了。
- 精确谓词卡组（并、交、可逆的像）：在 `probes` 上逐一比对成员判断。

所以视野和探针要一起设计：`probes` 应该是视野里两两运算、封闭常常能覆盖到的值。视野别太大（几十到两百个值），否则两两运算会慢。

## 测试

`tests/<name>.test.js` 至少要有：

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { CATALOG, WALKTHROUGH, CHAPTER } from '../src/domains/<name>.js';
import { checkCatalog, elementaryHand } from './helpers.js';

test('图鉴条目', () => checkCatalog(CATALOG));
test('路线', () => {
  const hand = elementaryHand();          // 已集齐初等篇，赠卡会自动收下
  hand.walk(WALKTHROUGH);
  for (const c of CATALOG) assert.ok(hand.has(`d:${c.id}`), c.name);
});
// 再加上本领域运算的单元测试：运算正确、错误情况有解释、显示文字、key 往返
```

运行：`node --test tests/<name>.test.js`。全部：`npm test`。
