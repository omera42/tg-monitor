from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio, os
from datetime import datetime

API_ID   = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN= os.environ["BOT_TOKEN"]
CHAT_ID  = int(os.environ["CHAT_ID"])
SESSION  = os.environ["SESSION_STRING"]

KEYWORDS = ["אזעקה","אזעקות","טיל","טילים","נפילה","נפל","איראן","פיצוץ","התקפה","מתקפה","חירום","כיפת ברזל","ראש העין","תל אביב דרום","שחרות","אורים","באר שבע צפון","פלמחים"]

MAPS = {
    "ראש העין": "https://maps.google.com/?q=ראש+העין,ישראל",
    "תל אביב דרום": "https://maps.google.com/?q=תל+אביב+דרום,ישראל",
    "שחרות": "https://maps.google.com/?q=שחרות,ישראל",
    "אורים": "https://maps.google.com/?q=אורים,ישראל",
    "באר שבע צפון": "https://maps.google.com/?q=באר+שבע,ישראל",
    "פלמחים": "https://maps.google.com/?q=פלמחים,ישראל",
}

user_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
bot_client  = TelegramClient(StringSession(), API_ID, API_HASH)

def find_keywords(text):
    return [kw for kw in KEYWORDS if kw in text]

def get_map_link(found):
    for kw in found:
        if kw in MAPS:
            return f"\n🗺️ [פתח במפה]({MAPS[kw]})"
    return ""

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
        map_link = get_map_link(found)
        msg = f"🚨 *התראה* — {now}\n📍 {source}\n🔑 {', '.join(found)}{map_link}\n\n{event.message.text[:500]}"
        await bot_client.send_message(CHAT_ID, msg, parse_mode='md', link_preview=False)

    await user_client.run_until_disconnected()

asyncio.run(main())
