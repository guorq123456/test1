# QQ 小号机器人（NapCat + Python）

小号由 NapCat 登录，`bot.py` 通过 WebSocket 连接 NapCat 来收发消息。
脚本**只回复你主号的私聊**，命令有：`/ping`、`/echo <内容>`、`/help`。

> ⚠️ NapCat 属于非官方框架，违反腾讯用户协议，**有封号风险**。只用小号，别用主号。

## 1. 在你自己电脑上装 NapCat

- 官方文档：<https://napneko.github.io/>
- Windows 最省事：去 NapCat 的 GitHub Releases 下载 Windows 一键包（文件名带 `OneKey` 的那个），解压后运行。
- 启动后用**小号的手机 QQ** 扫码登录。

## 2. 在 NapCat 里开 WebSocket 服务

1. 打开 NapCat 的 WebUI（默认 `http://127.0.0.1:6099/webui`，登录 token 在启动日志里）。
2. 进入「网络配置」，新建一个「WebSocket 服务器」：
   - Host：`127.0.0.1`，Port：`3001`
   - Token：自己设一串随机字符串，记下来
   - 「上报自身消息」保持关闭

（不同版本的界面叫法可能略有差别，意思对上就行。）

## 3. 运行机器人（需要 Python 3.10+）

```bash
pip install -r requirements.txt
```

Windows PowerShell：

```powershell
$env:OWNER_QQ="你的主号QQ号"
$env:NAPCAT_TOKEN="上一步设的token"
python bot.py
```

macOS / Linux：

```bash
OWNER_QQ=你的主号QQ号 NAPCAT_TOKEN=上一步设的token python3 bot.py
```

看到「小号 xxx 在线」后，用主号给小号发 `/ping`，1～3 秒后会收到 `pong 🏓`。

可选环境变量：`NAPCAT_WS_URL`，默认 `ws://127.0.0.1:3001`。

## 降低风控的小建议

- 小号先在手机上正常用几天，再挂 NapCat。
- NapCat 尽量和平时登录 QQ 的网络放在同一处，不要挂到海外服务器上。
- 别在群里刷屏，也别秒回。脚本已经加了 1～3 秒的随机延迟。
