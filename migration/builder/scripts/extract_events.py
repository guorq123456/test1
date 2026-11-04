import json, sys
raw = open(sys.argv[1]).read()
start = raw.index('{"ccr"'); end = raw.rindex('}') + 1
d = json.loads(raw[start:end])
events = sorted(d["ccr"]["data"], key=lambda e: e["created_at"])
lim_tool = int(sys.argv[2]) if len(sys.argv) > 2 else 1200
for e in events:
    for role in ("user", "assistant"):
        if role not in e:
            continue
        msg = e[role].get("internal_anthropic_catchall", {}).get("message") or e[role].get("message") or e[role]
        content = msg.get("content") if isinstance(msg, dict) else msg
        if isinstance(content, str):
            print(f"\n[{e['created_at'][11:19]} {role}] {content}")
            continue
        for c in content or []:
            t = c.get("type")
            if t == "text":
                print(f"\n[{e['created_at'][11:19]} {role} text] {c['text']}")
            elif t == "tool_use":
                print(f"\n[{e['created_at'][11:19]} {role} tool_use] {json.dumps(c.get('input'), ensure_ascii=False)[:lim_tool]}")
            elif t == "tool_result":
                cc = c.get("content")
                if isinstance(cc, list):
                    cc = " ".join(x.get("text", "") for x in cc if isinstance(x, dict))
                print(f"\n[{e['created_at'][11:19]} {role} tool_result] {str(cc)[:2500]}")
print("\nhas_more", d["ccr"].get("has_more"), "first", d["ccr"].get("first_id"), "last", d["ccr"].get("last_id"))
