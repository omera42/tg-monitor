from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio, os
from datetime import datetime

API_ID   = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN= os.environ["BOT_TOKEN"]
CHAT_ID  = int(os.environ["CHAT_ID"])
SESSION  = os.environ["SESSION_STRING"]

KEYWORDS = ["אזעקה","אזעקות","טיל","טילים","נפילה","נפל","איראן","פיצוץ","התקפה","מתקפה","חירום","כיפת ברזל"]

user_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
bot_client  = TelegramClient(StringSession(), API_ID, API_HASH)

def find_keywords(text):
    return [kw for kw in KEYWORDS if kw in text]

async def main():
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    await bot_client.send_message(CHAT_ID, "✅ מעקב ביטחוני פעיל!", parse_mode='md')

    @user_client.on(events.NewMessage)
    async def handler(event):
        if not event.message.text:
            return
        found = find_keywords(event.message.text)
        if not found:
            return
        chat = await event.get_chat()
        source = getattr(chat, 'title', None) or 'פרטי'
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        msg = f"🚨 *התראה* — {now}\n📍 {source}\n🔑 {', '.join(found)}\n\n{event.message.text[:500]}"
        await bot_client.send_message(CHAT_ID, msg, parse_mode='md')

    await user_client.run_until_disconnected()

asyncio.run(main())
```

---

**קובץ 2 — `requirements.txt`**
```
telethon==1.34.0
```

---

**קובץ 3 — `Procfile`**
```
worker: python monitor.py
