"""PreToolUse hook: block edits that could leak secrets or create a real-order path.

Exit code 2 = block the tool call; the message on stderr is shown to Claude.
"""
import json
import os
import sys

data = json.load(sys.stdin)
tool = data.get("tool_input", {}) or {}
path = str(tool.get("file_path", ""))
name = os.path.basename(path)
text = " ".join(str(tool.get(k, "")) for k in ("content", "new_string"))
for e in tool.get("edits", []) or []:
    text += " " + str(e.get("new_string", ""))

if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
    print(f"Blocked: {name} holds secrets. The owner edits .env by hand.", file=sys.stderr)
    sys.exit(2)

FORBIDDEN = ["order_send(", "api-fxtrade.oanda.com", "trading_mode: Literal[\"live\""]
hit = [f for f in FORBIDDEN if f in text]
if hit:
    print(f"Blocked: {hit} would add a real-order path. Live trading needs the owner's explicit approval first.",
          file=sys.stderr)
    sys.exit(2)
sys.exit(0)
