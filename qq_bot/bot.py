"""最小可用的 QQ 小号机器人：通过 NapCat 的 OneBot 11 正向 WebSocket 收发私聊消息。

只回复 OWNER_QQ（你的主号）发来的私聊，避免误回陌生人、降低风控概率。
"""
import asyncio
import json
import os
import random

from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException

WS_URL = os.environ.get("NAPCAT_WS_URL", "ws://127.0.0.1:3001")
TOKEN = os.environ.get("NAPCAT_TOKEN", "")
OWNER_QQ = os.environ.get("OWNER_QQ", "")

HELP = "可用命令：/ping、/echo <内容>、/help"


def make_reply(text: str) -> str | None:
    if text == "/ping":
        return "pong 🏓"
    if text.startswith("/echo "):
        return text[len("/echo "):]
    if text == "/help":
        return HELP
    return None


async def handle(ws, event: dict, owner: int) -> None:
    if event.get("post_type") != "message" or event.get("message_type") != "private":
        return
    if event.get("user_id") != owner:
        return
    reply = make_reply(event.get("raw_message", "").strip())
    if reply is None:
        return
    await asyncio.sleep(random.uniform(1, 3))  # 别秒回，像真人一点
    await ws.send(json.dumps({
        "action": "send_private_msg",
        "params": {"user_id": owner, "message": reply},
    }))


async def run(owner: int) -> None:
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else None
    tasks = set()
    delay = 1
    while True:
        try:
            async with connect(WS_URL, additional_headers=headers) as ws:
                print(f"已连接 NapCat：{WS_URL}")
                delay = 1
                async for raw in ws:
                    data = json.loads(raw)
                    if data.get("meta_event_type") == "lifecycle":
                        print(f"小号 {data.get('self_id')} 在线，等你用主号私聊它 /ping")
                    elif data.get("status") == "failed":
                        print(f"发送失败：{data.get('wording') or data.get('message')}")
                    else:
                        task = asyncio.create_task(handle(ws, data, owner))
                        tasks.add(task)
                        task.add_done_callback(tasks.discard)
        except (OSError, WebSocketException) as e:
            print(f"连接失败或断开（{e!r}），{delay} 秒后重试")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)


if __name__ == "__main__":
    if not OWNER_QQ.isdigit():
        raise SystemExit("请先设置环境变量 OWNER_QQ（你主号的 QQ 号）")
    try:
        asyncio.run(run(int(OWNER_QQ)))
    except KeyboardInterrupt:
        pass
