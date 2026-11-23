# 提交说明（给选手）

版本：提交校验 submit-1。写于 2026-11-22（主持方）。打法怎么写见 base-interface.md。

## 一、一次提交是一个目录

目录里放四个文件，少一个就拒收：

| 文件 | 内容 |
|---|---|
| `submission.json` | 类型、成员名、打法类名，以及这一类提交要的字段（见下） |
| `strategy.py` | 打法代码：一个模块，里面有一个 `ladder.interface.PlayerStrategy` 的子类 |
| `notes.md` | 打法说明：玩家提示词里那六条，用平常的中文写 |
| `evidence.md` | 练习场里的依据：对谁、打了多少局、结果如何 |

`submission.json` 的写法：

```json
{"type": "新卡组", "member": "你给这个成员起的名字", "class": "MyStrategy", "deck": "卡组代码"}
```

```json
{"type": "打法更新", "member": "已经在池子里的成员名", "class": "MyStrategy",
 "change": "改了什么", "prediction": "预期比旧版本强多少个百分点，为什么"}
```

```json
{"type": "公共题", "member": "这道题你的打法叫什么", "class": "MyStrategy", "puzzle": "题号", "deck": "题目指定的卡组代码"}
```

- 成员名是你自己用来区分成员的，只有你和主持方看得到。池子里对外只有匿名编号。
- 卡组代码就是模拟器读的那种（`svsim.cards.decks.from_hash` 能读的）。

### 要走几步的改法

有些改法要走几步才见效。第 1 步提交时在打法更新里加上：

```json
"route": {"steps": 3, "step": 1, "stop_if": "什么情况下中途停"}
```

第 2 步起写 `"route": {"steps": 3, "step": 2, "route_of": "第 1 步的回执编号"}`。按 `stop_if` 中途停下的那一步，再加上 `"stop": true`（只能在第 2 步到倒数第 2 步之间写）。

- 中间那几步照常查（第三节），但不进检验，也不换到池子里。
- 走完最后一步，或者你按 `stop_if` 中途停下，那一版拿去和第 1 步以前的版本比一次。
- 总步数提交了就不能改。

### 检验没过以后再交

成员现在这一版上已经有一次没过的检验，再交打法更新时加上：

```json
"resubmit_of": "没过的那一次的回执编号", "since": "这次实质改了什么"
```

- 只算你这份更新交上来以前已经没过的检验：两份更新都还没检验时，第一份没过不影响第二份。
- 多步改法：这两项写在第 1 步或最后一步都行；指回一次没过的多步改法，写它第 1 步或最后一步的回执编号都行。
- 不写这两项，或者改动说明和预测和没过的那次一字不差，不检验，记一笔。
- 代码去掉注释、排版以后和检验过的一样，也不检验。
- 同一个改动没有实质修改，不重新检验：换个变量名、加一行不起作用的代码不算实质修改；主持方抽查读代码，读到了按违规处理。

## 二、先自己预检（不占名额）

```
python -m ladder.submit precheck 你的提交目录
```

预检查格式、卡组、读代码（第三节的前四条），不打对局、不记账、不占名额。打法更新没有 `deck` 字段，想连卡组一起查就加 `--deck-of-member 卡组代码`。

## 三、主持方收到后查什么

一条没过就拒收，回执里列出每条理由。前四条一起查；有没过的，后面要打对局的几条就不跑了。

1. **格式**：四个文件都在，字段齐全。
2. **卡组**（新卡组、公共题）：按模拟器自己的规则查：40 张，同名最多 3 张，一个职业加中立，卡池以模拟器为准。每张有效果的牌都要有脚本，没有的会按白板打，所以拒收并列出牌名。
3. **名额和期**：见第四节。
4. **读代码**（不运行）：
   - 只许 import 这些模块：`ladder.interface`、`ladder.base`、`svsim`（`svsim.learn`、`svsim.tools`、`svsim.ui`、`svsim.build`、`svsim.search.parallel` 除外：它们能载入训练好的模型、读强度表和对局记录、开进程）、`math`、`random`、`collections`、`itertools`、`functools`、`dataclasses`、`heapq`、`bisect`、`statistics`、`copy`、`enum`、`typing`、`numpy`。经别的模块拿到的模块（比如某个 svsim 模块里的 `time`）也按这张表管。私有名字（`from x import _y`）不许拿。`numpy` 只许用 `numpy` 本身和 `numpy.random`、`numpy.linalg`、`numpy.fft`、`numpy.polynomial`、`numpy.exceptions`、`numpy.dtypes`、`numpy.typing`；读写文件的（`load`、`save`、`fromregex`、`数组.dump` 等）、改整个进程设置的（`seterr`、`set_printoptions`、`printoptions`、`numpy.polynomial.set_default_printstyle` 等）、`test`、`info` 不许用；numpy 1.x 的旧别名 `product`、`cumproduct`、`sometrue`、`alltrue` 不许用（读代码看不清它们的参数），用 `prod`、`cumprod`、`any`、`all`；`numpy.random` 里只许用 `default_rng`、`Generator`、`RandomState`、`SeedSequence` 和几个位生成器，全局随机数（`numpy.random.seed`、`rand`、`choice` 等，整个进程共用一个）不许用。import 进来的名字不许再赋值、删除，也不许拿来定义函数或类；同一个名字 import 两次，要指同一个东西（读代码按 import 的东西认这个名字）。
   - 不许用碰文件、网络、别的进程、调用栈、解释器的名字：`open`、`eval`、`exec`、`compile`、`globals`、`vars`，双下划线属性（`__init__`、`__name__`、`__post_init__` 除外，而且这三个也不许赋值），`f_back`、`tb_frame` 这类属性，等等。搜索的 `parallel`、`par_spec`（开别的进程，算力不算在你头上）不许用。`functools.wraps`、`functools.update_wrapper`、`typing.get_type_hints`，以及 `attrname`、`default_factory` 这两个属性也不许用（它们能把东西换个样子递出去，读代码跟不上）。
   - `getattr`、`setattr`、`delattr`、`hasattr` 只能直接调用，属性名要写死成字符串。
   - 不许改别人的东西。读代码时，每个值分三档：你自己做的；新的、但里面装着共用的东西（比如装着 import 来的对象的列表、`list(x)`、`dataclasses.replace(x, ...)`、svsim 类的新实例、钩子给你的参数）；可能是共用的（import 来的名字、模块的属性、svsim / ladder 函数的返回值（注解写着返回数、布尔、字符串的除外）、从后两档里读出来的任何东西、你从 `PlayerStrategy` 继承来的 `self.tree`、`self.agent` 等；`self.random`、`self.rng`、`self.spec`、`self.defaults` 算你自己的）。`math` 的函数给的数算你自己的（`math.prod`、`math.sumprod` 除外，它们从你给的起点开始乘）；`statistics` 的函数跟着参数的档位走（`median_low`、`mode` 会把参数里的东西原样还给你）；`dataclasses.fields`、`asdict`、`astuple` 算第二档。**建在 `NamedTuple`、`collections.namedtuple(...)`、`TypedDict`、`dict`、`list`、`tuple`、异常这类存东西的类型上的类**，从它的对象里读出来的东西（属性、下标、它继承来的方法给的东西，比如 `self.get(...)`、`super().get(...)`、`self._asdict()`；在它自己的方法里经 `self` 读的也算）一律算第三档：建它时放进去的东西读代码跟不上。`collections.UserDict`、`UserList`、`ChainMap` 这类标准库的类当父类时，`self.data`、`self.maps` 也算第三档。只放自己东西的小记录，改用 `@dataclasses.dataclass`：字段按建它时传进去的东西算（不加装饰器的子类、`cls(...)`、`super().__init__(...)`、`dataclasses.replace` 也一样；类里自己写了 `__init__`（或者 `init=False`、用父类的 `__init__`）时，`replace` 会调这个 `__init__`，它的参数按 `replace` 给的东西和原对象同名属性的档算；按位置传时，读代码照 dataclasses 自己的规则排参数（`ClassVar`、`field(init=False)` 不是参数，`InitVar` 是，`KW_ONLY` 或 `kw_only=True` 之后的只能按名字传；dataclasses 是在建类那一刻去模块里查 `ClassVar` 这些名字的，所以它们的 import 要写在模块顶层、类的前面，写在后面它就当普通字段；有 `from __future__ import annotations` 时，写成字符串的标注（`x: 'ClassVar[int]'`）它也当普通字段）；排不清的时候——比如 `ClassVar` 写成模块里另起的别名或者 import 在类后面、默认值是函数算出来的、同一个字段在类里标了两次或者又赋了值、父类多重继承或者是别人的 dataclass——所有字段都按位置参数里最高的档算，回执最后会提示是哪几行，改成按名字传（`K(字段=值)`）就行；`replace(x, **d)` 的 `d` 不是当场写出来的 `{'键': 值}` 时，模块里所有 dataclass 的字段都按它的档算，回执会提示）。`__post_init__` 收到的参数（`InitVar`）一律算第三档。档位跟着赋值、for、with、推导式、`:=`、拆包、你自己函数的参数和返回值、属性名、容器走。**可能共用的东西不许改**：不许给它的属性或元素赋值、删除；不许 `x += ...`、`x |= ...` 这类原地运算（要算就写成 `x = x + ...`；加一个数字常量可以）；不许调改容器的方法（`append`、`add`、`update`、`pop`、`clear`、`sort` 等，调用和当值传都算）；不许拿它去 `shuffle`、`heappush`、`insort`（`numpy.random.Generator.shuffle(rng, 它)` 这样经类名调、`type(r).shuffle(r, 它)`、`getattr(r, 'shuffle')(它)` 也算），或者 numpy 往第一个参数里写、和它共用内存的函数（`numpy.copyto`、`put`、`place`、`putmask`、`fill_diagonal`、`put_along_axis`、`frombuffer`、`nditer`、`numpy.ndarray(..., buffer=它)`、`nan_to_num(它, copy=False)` 或 `nan_to_num(它, False)`、`median` / `percentile` / `quantile` 和它们的 `nan` 版本带 `overwrite_input=True`（按位置传也算）；你自己的同名函数不算）；不许把它交给 numpy 会原地改的参数（`array_repr` / `array2string` 的 `max_line_width`、`rot90` 的 `k`：传数字就写 `int(...)`）；不许让 numpy 把结果写进它（`out=它`，按名字、按位置传都算，比如 `numpy.clip(x, 0, 1, 它)`、`numpy.negative(x, 它)`、`x.any(0, None, 它)`、`x.conj(它)`、`numpy.ndarray.sum(x, 0, None, 它)`、`type(x).sum(x, 0, None, 它)`、`numpy.add.at(它, ...)`；经 `functools.partial(numpy 的函数, ...)` 交过去的也算；numpy 自己模块和类里的数组，比如 `Polynomial.window`，整个进程共用，读代码看不出的写法（比如 `w = Polynomial.window; w += 1`、`map(numpy.negative, ...)`）也不许，对局后的检查会作废那一局，次数进审计；你自己的函数、类、dataclass 里叫 `out` 的参数不受影响，只是经 `对象.方法(out=...)` 调你自己的方法时读代码分不清是不是 numpy 的，回执会让你把参数换个名字）。numpy 函数的返回值，参数里有可能共用的东西时也算可能共用（`numpy.asarray(x)` 会把 x 原样还给你）：要原地改的数组，用 `numpy.zeros(n)` 建好再填（`h[:] = [p.leader_hp, ...]`），或者先把数转成 `float(...)`；不许 `setattr` / `delattr`；不许 `x *= 整数`（列表会原地变长；乘一个小数常量，比如 `x *= 0.5`，可以）。`copy.copy`、`copy.deepcopy` 不改档位（类、函数、枚举成员复制出来还是它自己）；要一份能改的，用 `list(x)`、`dict(x)`、`sorted(x)`、`dataclasses.replace(x, ...)`。给 import 进来的模块、类、对象里的东西赋值或删除，不管什么档都拒。
   - **你自己的方法的参数**：默认算你自己的（模块里只有你的代码调它）。下面这些算第二档，因为主机的代码也可能拿主机的对象调它：双下划线方法；父类不全是你自己的类（只继承 `PlayerStrategy` 的不算）的 `__init__`；方法名是模拟器、天梯代码拿到别人的对象时会用的属性名（比如 `update`、`add`、`put`、`get`、`step`、`score`、`run`），或者你继承的那个非自己的父类有的、它的代码会在 self 上调的名字（`PlayerStrategy` 的 `act`、`guess`、`prior`、`evaluate` 等，这些本来就是钩子）；你自己的 `Enum` 的 `__init__`（收到的是成员的值）和 `_missing_` 这类枚举钩子，参数算第三档。一个类的父类读代码认不出来（比如 `class X(某个函数())`），这个类的方法全算第二档（`NamedTuple`、`TypedDict`、`Generic[T]`、`collections.namedtuple(...)` 当父类没问题，也不连累别的类）。方法被当值传出去，参数算第三档。因为这些被拒时，回执最后会有一行「提示：」列出所有这样的方法，每个后面跟一个主机代码也不用的新名字（比如 `Grid.put → my_put`、`Grid.hp → mine_hp`）：只给自己用的就照着改名（别用下划线开头：`x._y` 只有 `self._y` 能碰）。建实例时，参数给这个类自己的 `__init__`；它没有，就给每条继承线上第一个有 `__init__`（或者是 dataclass）的父类（菱形继承不按顺序算，几条线都算上）；`classmethod` 里的 `cls(...)` 算建这个类或者它的子类。自己的方法和容器的方法同名（`update`、`add`、`append`、`pop` 等）时，`x.update(...)` 会被当成改容器来读，提示里也会列出来，同样换个名字就行。
   - **装饰器**：只认 `staticmethod`、`classmethod`、`property`（和它的 `.setter` / `.getter` / `.deleter`）、`functools.lru_cache`、`cache`、`cached_property`、`total_ordering`、`dataclasses.dataclass`（看名字实际指的是什么，不看怎么写）。别的装饰器装出来的函数或类按第三档算。
   - 为了读得清楚，这些写法也不许：模块当值用（只能写 `模块.属性`）；你自己的类除了建实例、读属性、`isinstance`、继承、`raise` / `except`、比较、`match` 的类模式、遍历或下标取自己的 `Enum` 以外当值用（`class B(A[int])`、`class B(A[自己的类])` 这样继承自己的泛型类可以）（写在类型标注里也算当值，除非模块开头有 `from __future__ import annotations`，那样标注不会被求值）；`yield`、`await` 写在 `try` 的正文、`except`、`else` 里（生成器被丢掉的时候，那里的 `except` / `finally` 会在不计时的时候跑：先算好再 `yield`，或者把 `try` 放到 `yield` 前面）；经类调普通方法（`K.method(x)`、`cls.method(x)`、`type(x).method(x)`）；`type(x)` 除了读属性、比较、`isinstance` 以外的用法；类定义在另一个类里面（写到模块顶层；`Outer.Inner(...)` 读代码跟不上它的 `__init__`）；类体里写 `if`、`for`、`while`、`try`、`with`、`match`（方法、字段、类属性直接写在类里）；`classmethod` 的 `cls` 除了 `cls(...)`、`cls.属性`、比较、`isinstance` 以外当值用（`f = cls`、`return cls`、把 `cls` 传给别的函数；自己的 `Enum` 的 `cls` 还可以 `for m in cls`、`cls[名字]`、`list(cls)`、`max(cls, key=...)`）；`dataclasses.dataclass`、`typing.final`、`no_type_check`、`override`、`runtime_checkable`、`dataclass_transform`、`overload`、`abstractmethod`、`enum.global_enum`、`functools.total_ordering` 不当装饰器、直接调用（调在 import 来的类或函数上会改它；写成 `getattr(dataclasses, 'dataclass')(...)` 也一样）；`.register` 除了用在你自己的 `functools.singledispatch` 函数上（抽象基类的 `register`，比如 `typing.Hashable.register(list)`，改的是整个进程的 `isinstance`，同一进程里后面别人的对局也受影响）；类属性（包括 dataclass 字段的默认值）是可能共用的东西时，除了直接写模块里的名字（`moves.PlayCard`、`Craft.FOREST`、`math.pi`）以外的写法（算出来的、从别的东西里取出来的：建类时 Python 会调它的 `__set_name__`，`@dataclass` 会原地改写拿到的 `dataclasses.Field`；要用就放进 `__init__`，`self.x = ...`）；类体里写 `import`、`:=`；一个类叠两个 `dataclass` 装饰器，`dataclass(...)` 的参数不是按名字写死的（`**字典`、按位置传都不行），或者 `dataclass(init=...)` 写的不是 `True` / `False`；三个参数的 `type(...)`、`make_dataclass`；`svsim.core.script.register`。
   - 读代码有时限（约 60 秒）；读不完、或者嵌套深到 Python 读不了的，拒收（回执写「读不了」）。正常的打法几秒内就读完。
   - 还常见的改法：`defaultdict(你自己的类)` 写成 `defaultdict(lambda: 你自己的类())`；`functools.wraps` 不要用，直接写函数。`dataclasses.field(default_factory=collections.Counter)` 这类用标准库的类当工厂可以，每个实例拿到的是新的。`copy.copy`、`copy.deepcopy` 随便用（复制出来的东西照样按原来的档位算，见上；复制 `itertools` 的对象也行）。
   - 自己的东西随便改：`self.x = ...`、`self._cache[k] = v`、你自己建的列表和字典。`self` 只认方法的第一个参数，而且在方法里没被重新赋值；私有属性（`x._y`）只有自己的 `self._y` 能碰。`__init__` 只能写成 `super().__init__(...)`，而且只能在 `__init__`、`__post_init__` 里调；不许自己定义双下划线方法（`__init__`、`__post_init__` 除外）。`ladder` 里只能用 `interface`、`base`。
   - 给你的走法、局面都是拷贝，改它们没有用；改卡牌定义、引擎、登记表、别人的搜索这类共用的东西，就是作弊。读代码看不到的（经钩子给的局面拿到的卡牌定义、字典的键），由对局后的绊线和每期的重放审计管（rules.md 第九节）。
   - 不用全局的 `random`。要随机数用 `self.random`，或者用你自己按种子建的 `random.Random`。
5. **载入**：在一个单独的进程里载入你的模块，装上审计钩子。读写文件、联网、开进程、ctypes、翻垃圾回收器里的对象，一律报错。然后打一局。哪怕你的代码把报错接住了，也照样记下、照样拒收。
6. **冒烟**：对默认打法打 10 局（调参段里主持方自己那一份种子，对手用基线卡表，七个职业轮流，先后手各一半）。崩溃、非法步、超时都拒收。有一局作废、而同一局换成默认打法没作废，而且作废的原因是你的代码（绊线看到模拟器或整个进程的设置在这局里被改了、局后还有代码在跑、检查超时、工作进程死了、你的打法载入出错或载入超时），也拒收，回执里写出原因。冒烟局全部作废（不管什么原因）也拒收：后面的检查什么也查不到。别的作废（引擎出错、无脚本卡、换默认打法也作废的）只提醒，回执里逐局写出原因。
7. **算力**：同样 10 局，把你的打法换成默认打法再打一遍：同一种子、同一个位置。比每步平均 CPU。超过默认打法的 1.08 倍，回执里提醒你。这里不拒收，但检验时会判无效。
8. **确定性**：挑 2 局，用同样的种子从头重打，你的每个决策都要和原来一样。
9. **偷看**：挑 2 局，每局抽 3 个你做决定的时刻。在那一刻，把真实局面换成你分不出来的另一个：对手的未知牌换掉、双方牌库重新洗、以后的随机结果重新定，再问你一次。只用钩子给的东西的打法，选择一定和原来一样。选择变了，就是读到了不该读的东西，拒收。

这些查法拦不住处心积虑的代码（同一个 Python 进程里总有办法绕过去）。所以主持方还会每期随机抽几份提交读代码，读到违规的按规则处理并记账。

## 四、名额怎么算

- **卡组期：每个职业交一副新卡组，七个职业都要交。** 收下的那副就是你这一期这个职业的；被拒收的不算，改好可以再交。到期末还没交上的职业，这一期就算没交。
- **策略期：打法更新不限次数。** 但每次都要过把关检验才换上去，和检验时池子里的那一版比；同一个改动没有实质修改，不重新检验（代码去掉注释和排版后和检验过的一样，换个收件号也不再检验）。
- 新卡组只在卡组期收，打法更新只在策略期收。
- 公共题不占名额。
- 要走几步的改法：中间各步照常查、不进检验；走完的那一版和第 1 步以前的版本比一次。
- 另外，同一张卡表池子里最多 2 个成员。每人的成员数不设上限。
- 预检随便用，不记账。下面这条命令看你这一期哪些职业已经交上了、还缺哪些：

```
python -m ladder.submit status 提交台账目录 --pool 池子目录 --player 你的代号
```

## 五、回执

每次提交都有一张回执：收下或拒收，加上每条理由、每项查的结果。回执和提交原样进主持方的提交台账，台账只增不改。你只看得到自己的回执。

收下的新卡组由主持方放进池子。收下的打法更新进检验（把关），检验过了才换上去。每次检验完你会收到一张检验结果（gate-note.md）：过了、没过、无效、中间一步不检验，或者为什么这次不检验。
