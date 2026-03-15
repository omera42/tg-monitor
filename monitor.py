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

EARLY_WARNINGS = ["התראה מוקדמת","שיגור מאיראן","טילים בדרך","שיגור בליסטי"]

ALLOWED_SOURCES = [
    "חדשות מהשניה",
    "דיווחים אונליין",
    "ניצן שפירא",
    "חדשות N12",
    "N12",
]

OREF_LIVE = "https://www.oref.org.il/heb/alerts-history"

last_alert = {}
seen_messages = set()
COOLDOWN = 600

user_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
bot_client  = TelegramClient(StringSession(), API_ID, API_HASH)

def check_message(text):
    found_areas = [a for a in AREAS if a in text]
    found_alerts = [w for w in ALERT_WORDS if w in text]
    found_early = [w for w in EARLY_WARNINGS if w in text]
    return found_areas, found_alerts, found_early

def is_allowed_source(chat):
    title = getattr(chat, 'title', '') or ''
    return any(s.lower() in title.lower() for s in ALLOWED_SOURCES)

def should_send(area):
    now = datetime.now().timestamp()
    if area not in last_alert or now - last_alert[area] > COOLDOWN:
        last_alert[area] = now
        return True
    return False

def is_duplicate(text):
    # בודק אם ההודעה נשלחה כבר (לפי 50 תווים ראשונים)
    key = text[:50].strip()
    if key in seen_messages:
        return True
    seen_messages.add(key)
    if len(seen_messages) > 200:
        seen_messages.pop()
    return False

async def main():
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    await bot_client.send_message(CHAT_ID, "✅ מעקב ביטחוני פעיל!\n🎯 עוקב אחרי האזורים שלך\n⚡ כולל התראות מוקדמות", parse_mode='md')

    @user_client.on(events.NewMessage)
    async def handler(event):
        if not event.message.text:
            return
        chat = await event.get_chat()
        if not is_allowed_source(chat):
            return
        text = event.message.text
        found_areas, found_alerts, found_early = check_message(text)
        source = getattr(chat, 'title', None) or 'פרטי'
        now = datetime.now().strftime('%d/%m/%Y %H:%M')

        # התראה מוקדמת — כל פעם, רק בלי כפילויות
        if found_early:
            if is_duplicate(text):
                return
            early_str = ", ".join(found_early)
            oref_link = f"\n🚨 [מפת אזעקות בלייב]({OREF_LIVE})"
            msg = f"⚡ *התראה מוקדמת!* — {now}\n📍 {source}\n🔔 {early_str}{oref_link}\n\n{text[:500]}"
            await bot_client.send_message(CHAT_ID, msg, parse_mode='md', link_preview=False)
            return

        # התראה על אזור ספציפי
        if not found_areas:
            return
        new_areas = [a for a in found_areas if should_send(a)]
        if not new_areas:
            return
        areas_str = ", ".join(new_areas)
        map_link = f"\n🗺️ [פתח במפה]({AREAS[new_areas[0]]})"
        oref_link = f"\n🚨 [מפת אזעקות בלייב]({OREF_LIVE})"
        alerts_str = f"\n⚠️ {', '.join(found_alerts)}" if found_alerts else ""
        msg = f"🚨 *התראה באזורך!* — {now}\n📍 {source}\n📌 אזור: {areas_str}{alerts_str}{map_link}{oref_link}\n\n{text[:500]}"
        await bot_client.send_message(CHAT_ID, msg, parse_mode='md', link_preview=False)

    await user_client.run_until_disconnected()

asyncio.run(main())
