from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio, os, aiohttp, json
from datetime import datetime
import pytz

API_ID    = int(os.environ["API_ID"])
API_HASH  = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID   = int(os.environ["CHAT_ID"])
SESSION   = os.environ["SESSION_STRING"]

IL_TZ = pytz.timezone('Asia/Jerusalem')

AREAS = {
    "ראש העין": "https://www.google.com/maps/search/ראש+העין+ישראל",
    "תל אביב דרום": "https://www.google.com/maps/search/תל+אביב+דרום+ישראל",
    "תל אביב - דרום": "https://www.google.com/maps/search/תל+אביב+דרום+ישראל",
    "שחרות": "https://www.google.com/maps/search/שחרות+ישראל",
    "אורים": "https://www.google.com/maps/search/אורים+ישראל",
    "באר שבע צפון": "https://www.google.com/maps/search/באר+שבע+ישראל",
    "באר שבע - צפון": "https://www.google.com/maps/search/באר+שבע+ישראל",
    "פלמחים": "https://www.google.com/maps/search/פלמחים+ישראל",
    "ראש העין - מזרח": "https://www.google.com/maps/search/ראש+העין+ישראל",
    "ראש העין - מערב": "https://www.google.com/maps/search/ראש+העין+ישראל",
}

ALERT_WORDS = ["אזעקה","אזעקות","טיל","טילים","נפילה","נפל","פיצוץ","התקפה","חירום","כיפת ברזל","יירוט","ירי","נפגע","נפגעים"]
EARLY_WARNINGS = ["התראה מוקדמת","שיגור מאיראן","טילים בדרך","שיגור בליסטי"]

ALLOWED_SOURCES = [
    "חדשות מהשנייה בטלגרם",
    "חדשות מהשניה",
    "דיווחים און ליין",
    "דיווחים אונליין",
    "ניצן שפירא בטלגרם",
    "ניצן שפירא",
    "חדשות N12",
    "N12",
]

OREF_API  = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
OREF_LIVE = "https://www.oref.org.il/heb/alerts-history"

last_alert    = {}
seen_messages = set()
seen_oref     = set()
COOLDOWN      = 600
start_time    = None

user_client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
bot_client  = TelegramClient(StringSession(), API_ID, API_HASH)

def now_il():
    return datetime.now(IL_TZ).strftime('%d/%m/%Y %H:%M')

def check_message(text):
    found_areas  = [a for a in AREAS if a in text]
    found_alerts = [w for w in ALERT_WORDS if w in text]
    found_early  = [w for w in EARLY_WARNINGS if w in text]
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
    key = text[:50].strip()
    if key in seen_messages:
        return True
    seen_messages.add(key)
    if len(seen_messages) > 200:
        seen_messages.clear()
    return False

async def check_oref():
    try:
        headers = {
            'Referer': 'https://www.oref.org.il/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(OREF_API, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return
                text = await resp.text()
                if not text.strip():
                    return
                data   = json.loads(text)
                alerts = data.get('data', [])
                for alert in alerts:
                    if alert in seen_oref:
                        continue
                    seen_oref.add(alert)
                    if len(seen_oref) > 500:
                        seen_oref.clear()
                    found = [a for a in AREAS if a in alert]
                    if found:
                        area      = found[0]
                        map_link  = "\n🗺️ [פתח במפה](" + AREAS[area] + ")"
                        oref_link = "\n🚨 [מפת אזעקות בלייב](" + OREF_LIVE + ")"
                        msg = "🚨 *אזעקה בזמן אמת!* — " + now_il() + "\n📡 פיקוד העורף\n📌 אזור: " + alert + map_link + oref_link
                        await bot_client.send_message(CHAT_ID, msg, parse_mode='md', link_preview=False)
    except Exception:
        pass

async def oref_loop():
    while True:
        await check_oref()
        await asyncio.sleep(3)

async def main():
    global start_time
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    start_time = datetime.now().timestamp()

    await bot_client.send_message(
        CHAT_ID,
        "✅ *מעקב ביטחוני פעיל!*\n"
        "📡 פיקוד העורף — בזמן אמת כל 3 שניות\n"
        "📰 ערוצי חדשות — התראות מוקדמות\n"
        "🎯 עוקב רק אחרי האזורים שלך",
        parse_mode='md'
    )

    @user_client.on(events.NewMessage)
    async def handler(event):
        if not event.message.text:
            return
        if event.message.date.timestamp() < start_time:
            return
        chat = await event.get_chat()
        if not is_allowed_source(chat):
            return
        text = event.message.text
        found_areas, found_alerts, found_early = check_message(text)
        source = getattr(chat, 'title', None) or 'לא ידוע'

        if found_early:
            if is_duplicate(text):
                return
            early_str = ", ".join(found_early)
            oref_link = "\n🚨 [מפת אזעקות בלייב](" + OREF_LIVE + ")"
            msg = "⚡ *התראה מוקדמת!* — " + now_il() + "\n📍 " + source + "\n🔔 " + early_str + oref_link + "\n\n" + text[:500]
            await bot_client.send_message(CHAT_ID, msg, parse_mode='md', link_preview=False)
            return

        if not found_areas:
            return
        new_areas = [a for a in found_areas if should_send(a)]
        if not new_areas:
            return
        areas_str  = ", ".join(new_areas)
        map_link   = "\n🗺️ [פתח במפה](" + AREAS[new_areas[0]] + ")"
        oref_link  = "\n🚨 [מפת אזעקות בלייב](" + OREF_LIVE + ")"
        alerts_str = "\n⚠️ " + ", ".join(found_alerts) if found_alerts else ""
        msg = "🚨 *התראה באזורך!* — " + now_il() + "\n📍 " + source + "\n📌 אזור: " + areas_str + alerts_str + map_link + oref_link + "\n\n" + text[:500]
        await bot_client.send_message(CHAT_ID, msg, parse_mode='md', link_preview=False)

    asyncio.create_task(oref_loop())
    await user_client.run_until_disconnected()

asyncio.run(main())
