#!/usr/bin/env python3
"""
בוט טלגרם — מציאת המקלט הציבורי הקרוב ביותר.
המשתמש שולח מיקום (📎 ← Location) והבוט מחזיר את המקלט הקרוב + קישורי ניווט.

הרצה:
  1. pip install "python-telegram-bot>=20"
  2. צרי בוט אצל @BotFather בטלגרם וקבלי טוקן
  3. export TELEGRAM_TOKEN="<הטוקן שלך>"
  4. python3 bot.py
"""

import os
import json
import math
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes,
)

# ---------- טעינת נתוני המקלטים ----------
DATA_FILE = Path(__file__).with_name("shelters.json")
SHELTERS = json.loads(DATA_FILE.read_text(encoding="utf-8"))  # [[lat, lon, type], ...]


def haversine(lat1, lon1, lat2, lon2):
    """מרחק בקו אווירי במטרים."""
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest(lat, lon, k=3):
    scored = [(haversine(lat, lon, s[0], s[1]), s) for s in SHELTERS]
    scored.sort(key=lambda x: x[0])
    return scored[:k]


def fmt_dist(m):
    if m < 1000:
        return f"{round(m)} מ׳"
    return f"{m/1000:.1f} ק״מ"


def walk_time(m):
    minutes = round(m / 1000 / 5 * 60)  # ~5 קמ"ש
    if minutes < 1:
        return "פחות מדקת הליכה"
    if minutes < 60:
        return f"כ‑{minutes} דק׳ הליכה"
    return f"כ‑{minutes/60:.1f} שעות הליכה"


# ---------- מטפלים ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 שלח/י את המיקום שלי", request_location=True)]],
        resize_keyboard=True,
    )
    await update.message.reply_text(
        "🛡️ *מקלט קרוב*\n\n"
        "שלחו לי את המיקום שלכם ואחזיר את המקלט הציבורי הקרוב ביותר + קישור לניווט.\n\n"
        "לחצו על הכפתור למטה, או על 📎 ← *Location*.",
        parse_mode="Markdown",
        reply_markup=kb,
    )


async def on_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    lat, lon = loc.latitude, loc.longitude
    results = nearest(lat, lon, k=3)
    dist, s = results[0]
    s_lat, s_lon, s_type = s[0], s[1], (s[2] or "מקלט ציבורי")

    gmaps = f"https://www.google.com/maps/dir/?api=1&destination={s_lat},{s_lon}&travelmode=walking"
    waze = f"https://waze.com/ul?ll={s_lat},{s_lon}&navigate=yes"

    text = (
        f"🛡️ *המקלט הקרוב ביותר*\n"
        f"📏 {fmt_dist(dist)} ממך · {walk_time(dist)}\n"
        f"🏷️ {s_type}\n\n"
        f"💡 לחצו על *נווט בגוגל מפס* — הניווט יעבוד גם אם הורדתם מפה אופליין באזור."
    )
    buttons = [
        [InlineKeyboardButton("🗺️ נווט בגוגל מפס", url=gmaps),
         InlineKeyboardButton("🚗 נווט ב‑Waze", url=waze)],
    ]
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons)
    )
    # פין מיקום אמיתי על המפה של טלגרם
    await update.message.reply_location(latitude=s_lat, longitude=s_lon)

    # מקלטים נוספים בקרבת מקום
    if len(results) > 1:
        extra = "\n".join(
            f"• {(o[2] or 'מקלט')} — {fmt_dist(d)}" for d, o in results[1:]
        )
        await update.message.reply_text("מקלטים נוספים בקרבת מקום:\n" + extra)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "פשוט שלחו לי מיקום (📎 ← Location) ואחזיר את המקלט הקרוב ביותר.\n"
        "אפשר גם לשלוח מיקום בזמן אמת (Live Location)."
    )


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("חסר TELEGRAM_TOKEN. הריצי: export TELEGRAM_TOKEN='<הטוקן>'")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.LOCATION, on_location))
    print(f"הבוט רץ עם {len(SHELTERS):,} מקלטים. Ctrl+C לעצירה.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
