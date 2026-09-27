// 把初等篇和各个高等领域的内容汇总成一份。界面和合成规则只从这里读内容。

import {
  CATALOG as ELEM_CATALOG,
  CHAPTERS as ELEM_CHAPTERS,
  QUESTS as ELEM_QUESTS,
  NAMED_UN as ELEM_NAMED_UN,
  BIN_INFO as ELEM_BIN_INFO,
  START,
  META,
} from './catalog.js';
import * as mod from './domains/mod.js';
import * as poly from './domains/poly.js';
import * as linalg from './domains/linalg.js';
import * as qty from './domains/qty.js';

// 每个领域模块导出：CHAPTER、CATALOG、QUESTS、NAMED_UN、WALKTHROUGH、BIN_INFO（都可以为空）
export const DOMAINS = [mod, poly, linalg, qty];

export const CATALOG_ALL = [
  ...ELEM_CATALOG.map(c => ({ ...c, type: 'q' })),
  ...DOMAINS.flatMap(d => d.CATALOG ?? []),
];

export const CHAPTERS_ALL = [...ELEM_CHAPTERS, ...DOMAINS.map(d => d.CHAPTER).filter(Boolean)];

export const QUESTS_ALL = [...ELEM_QUESTS, ...DOMAINS.flatMap(d => d.QUESTS ?? [])];

export const NAMED_UN_ALL = [...ELEM_NAMED_UN, ...DOMAINS.flatMap(d => d.NAMED_UN ?? [])];

export const BIN_INFO = Object.assign({}, ELEM_BIN_INFO, ...DOMAINS.map(d => d.BIN_INFO ?? {}));

// 拿到某张卡时额外赠送的卡（章节解锁）：{ 'd:Z': ['b:mod'], … }
export const GIFTS = {};
for (const ch of CHAPTERS_ALL) {
  if (!ch.unlock) continue;
  (GIFTS[ch.unlock.when] ||= []).push(...ch.unlock.gives);
}

// 每个领域从"初等篇集齐 + 本章赠卡"出发到集齐本章卡组的一条路线，测试用
export const WALKTHROUGHS = DOMAINS.filter(d => d.CHAPTER).map(d => ({ chapter: d.CHAPTER, steps: d.WALKTHROUGH ?? [] }));

export { START, META };
