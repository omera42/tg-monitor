from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio, os
from datetime import datetime

API_ID   = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN= os.environ["BOT_TOKEN"]
CHAT_ID  = int(os.environ["CHAT_ID"])
SESSION  = os.environ["SESSION_STRING"]

AREAS = {
    "ראש העין": "https://maps.google.com/?q=ראש+העין,ישראל",
    "תל אביב דרום": "https://maps.google.com/?q=תל+אביב+דרום,ישראל",
    "שחרות": "https://maps.google.com/?q=שחרות,ישראל",
    "אורים": "https://maps.google.com/?q=אורים,ישראל",
    "באר שבע צפון": "https://maps.google.com/?q=באר+שבע,ישראל",
    "פלמחים": "https://maps.google.com/?q=פלמחים,ישראל",
}

ALERT_WORDS = ["אזעקה","אזעקות","טיל","טילים","נפילה","נפל","פיצוץ","התקפה","חירום","כיפת ברזל","יירוט"]

user_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
bot_client  = TelegramClient(StringSession(), API_ID, API_HASH)

def check_message(text):
    found_areas = [a for a in AREAS if a in text]
    found_alerts = [w for w in ALERT_WORDS if w in text]
    return found_areas, found_alerts

async def main():
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    await bot_client.send_message(CHAT_ID, "✅ מעקב ביטחוני פעיל!\n🎯 עוקב רק אחרי האזורים שלך", parse_mode='md')

    @user_client.on(events.NewMessage)
    async def handler(event):
        if not event.message.text:
            return
        found_areas, found_alerts = check_message(event.message.text)
        if not found_areas:
            return
        chat = await event.get_chat()
        source = getattr(chat, 'title', None) or 'פרטי'
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        areas_str = ", ".join(found_areas)
        map_link = f"\n🗺️ [פתח במפה]({AREAS[found_areas[0]]})"
        alerts_str = f"\n⚠️ {', '.join(found_alerts)}" if found_alerts else ""
        msg = f"🚨 *התראה באזורך!* — {now}\n📍 {source}\n📌 אזור: {areas_str}{alerts_str}{map_link}\n\n{event.message.text[:500]}"
        await bot_client.send_message(CHAT_ID, msg, parse_mode='md', link_preview=False)

    await user_client.run_until_disconnected()

asyncio.run(main())
