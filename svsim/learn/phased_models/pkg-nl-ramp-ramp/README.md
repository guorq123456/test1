# 装档包 pkg-nl-ramp-ramp（没装）

**条件：**对手卡表已知（牌序、手牌未知）。

- **内容：**现装全部模型文件逐字节拷贝，只有 ramp-ramp-ended.json 换成 cand-nl-ramp-ramp 的。来源和 sha256 见 PACKAGE.json。
- **生成：**`python3 analysis/install/make_pkg.py cand-nl-ramp-ramp pkg-nl-ramp-ramp`。
- **核对：**tests/test_install_packages.py。
- **说明：**analysis/install/WINDOWS_CHECKLIST.md 第 5 节。
- **装机：**用不用、用在哪一档，要 Salem 本人的话。
