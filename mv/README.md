# 機械の声 × Claude — Fan MV

用 HTML Canvas 做的《機械の声》（香椎モイミ / V.I.P #3）同人 MV，主角是 Claude（克）。
整支 MV 是时间 `t` 的纯函数：既能在浏览器里跟着你本地的音频文件实时播放，也能逐帧离线渲染成 MP4。

## 文件结构

| 路径 | 内容 |
|---|---|
| `index.html` `js/` `css/` | MV 引擎与播放器 |
| `data/timeline.json` | 93 行歌词（日文 + 中文翻译）、时间戳、16 个段落 |
| `assets/` | Claude的抠图素材（全身 / 脸部 / 书 / 剪影 / 线稿 / 灰度） |
| `fonts/` | 所用字体（全部 OFL 开源协议） |
| `render/` | Playwright + ffmpeg 逐帧渲染脚本；`build_dist.py` / `subset_fonts.py` 生成单文件网页版 |
| `dist/` | 单文件网页版（字体子集内嵌），可直接静态托管或作为 claude.ai Artifact 发布 |
| `video/` | 已渲染的 720p 无声成片（预览用） |
| `STORYBOARD.md` / `STORYBOARD_V2.md` | 分镜脚本与设计规范；V2 增加了 3D 环境、动态镜头、角色动画与竖排歌词的方向 |
| `js/env.js` `js/charfx.js` | v2 的伪 3D 环境库（线框城市 / 人形灯群大厅 / 光隧道 / 球体 / 悬浮屏幕 / 警报场 / 驾驶舱 HUD）与角色动画库（呼吸、发丝摆动、辉光、全息、残影） |
| `dev/` | 两个库的演示页与对照图 |
| `ref/` | 原版 MV 的参考封面帧 |

## 在浏览器里播放（带音乐）

```bash
cd mv && npx http-server -p 8765      # 或 python3 -m http.server 8765
```
打开 http://localhost:8765/ ，点「选择音频文件」载入你自己的《機械の声》音频，空格播放/暂停。
快捷键：`Z` 切换中文字幕，`F` 全屏，`[` / `]` 微调音画偏移 ±0.1 s（流媒体版与 MV 版开头略有差异时用）。

## 渲染成视频

见 `render/README.md`。完整命令（1080p30，分块可续渲，4 核约 18 分钟）：

```bash
cd mv/render && node render.mjs --serve --chunk 20 --out ../out/mv_1080p.mp4
```

v2 的 1080p 原始渲染（CRF 18）约 880MB，辉光与颗粒让码率很高；分享用可再压一次，例如 720p `-crf 33` 约 25MB。4 核机器渲染约 21 分钟。
渲染出的是无声视频，之后用 ffmpeg 把音频合进去：

```bash
ffmpeg -i mv.mp4 -i song.mp3 -c:v copy -c:a aac -b:a 256k -shortest mv_with_audio.mp4
```

时间轴以流媒体版（6:39）为准，t=0 为音频开头。若你的音频开头有空白，用 `-itsoffset`（见 `render/README.md`）或在网页播放器里按 `[` / `]` 微调。

## 版权说明

歌曲、歌词版权归香椎モイミ / KAMITSUBAKI STUDIO 所有；本 MV 为非商业同人作品，仅供学习交流。
歌词时间轴取自流媒体版本（6:39），中文翻译为本项目自译。
