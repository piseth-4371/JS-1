"""Telegram alert setup helper (run from the backend folder).

Step 1 - find your chat id (after you sent any message to your bot in Telegram):
    .\\.venv\\Scripts\\python scripts\\telegram_setup.py chat-id
Step 2 - send a test message:
    .\\.venv\\Scripts\\python scripts\\telegram_setup.py test

Reads TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID from backend/.env. Never prints the token.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.core import telegram  # noqa: E402


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    s = get_settings()
    if not s.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is not set in backend\\.env (see .env.example).")
        return 1
    if cmd == "chat-id":
        token = s.telegram_bot_token.get_secret_value()
        try:
            r = httpx.get(f"{telegram.API}/bot{token}/getUpdates", timeout=10)
        except Exception as e:
            print(f"Could not reach Telegram: {type(e).__name__}")
            return 1
        if r.status_code != 200:
            print(f"Telegram said HTTP {r.status_code}. Is the token correct (copied fully from BotFather)?")
            return 1
        chats = {}
        for u in r.json().get("result", []):
            chat = (u.get("message") or u.get("channel_post") or {}).get("chat")
            if chat:
                chats[chat["id"]] = chat.get("title") or chat.get("first_name") or chat.get("username") or ""
        if not chats:
            print("No messages yet. Open your bot in Telegram, press START (or send 'hi'), then run this again.")
            return 1
        for cid, name in chats.items():
            print(f"chat id {cid}   ({name})")
        print("Put the id in backend\\.env as TELEGRAM_CHAT_ID=<id>, then run:  ... telegram_setup.py test")
        return 0
    if cmd == "test":
        if not s.telegram_chat_id:
            print("TELEGRAM_CHAT_ID is not set in backend\\.env. Run the chat-id step first.")
            return 1
        ok = telegram.send("✅ Test from your NAS100 learning lab. Alerts are working (signals only, never trades).")
        print("Sent! Check Telegram." if ok else "Failed - see the warning above (wrong chat id, or you never pressed START).")
        return 0 if ok else 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
