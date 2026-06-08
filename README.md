# 🛡️ מקלט קרוב — מציאת המקלט הקרוב ביותר

שני חלקים שעובדים מאותם נתונים (`shelters.json`, 10,212 מקלטים):

1. **אפליקציית וב אופליין** (`index.html`) — העוגן האמין. עובדת גם בלי אינטרנט.
2. **בוט טלגרם** (`bot.py`) — נוחות: שולחים מיקום, מקבלים מקלט + קישור.

> המרחק מחושב בקו אווירי (Haversine). הקישור לניווט נפתח בגוגל מפס/Waze.

---

## חלק 1 — האפליקציה האופליינית (מומלץ)

קובץ `index.html` עצמאי: כל המקלטים מוטמעים בתוכו, אז הוא עובד גם בלי שרת ובלי אינטרנט.
ה‑GPS של הטלפון מחשב את המקלט הקרוב מקומית. הקישור לגוגל מפס יודע לנווט אופליין אם הורדת מפה של האזור מראש.

### העלאה חינמית ל‑GitHub Pages (הכי פשוט, נותן HTTPS שצריך ל‑GPS ולהתקנה)
1. צרי repo חדש ב‑GitHub, למשל `shelter-finder`.
2. העלי את כל הקבצים מהתיקייה הזו (`index.html`, `manifest.json`, `sw.js`, `icon-192.png`, `icon-512.png`).
3. Settings → Pages → Branch: `main` / root → Save.
4. אחרי דקה תקבלי כתובת כמו `https://<user>.github.io/shelter-finder/`.

### התקנה כאפליקציה אמיתית (אייקון במסך הבית, עובד אופליין)
- **אייפון:** פותחים את הכתובת ב‑Safari → שיתוף → "הוסף למסך הבית".
- **אנדרואיד:** פותחים ב‑Chrome → תפריט → "התקן אפליקציה".

אחרי הטעינה הראשונה ה‑Service Worker שומר הכל — מכאן זה עובד גם במצב טיסה.

> שימוש מקומי מהיר ללא העלאה: בתיקייה הזו הריצי `python3 -m http.server 8000` ופתחי `http://localhost:8000`. (פתיחה ישירה של הקובץ ב‑`file://` תעבוד ברוב הדפדפנים אבל ה‑GPS לפעמים חסום שם — לכן עדיף localhost או HTTPS.)

---

## חלק 2 — בוט הטלגרם

### הקמה
```bash
pip3 install -r requirements.txt          # מתקין python-telegram-bot
```
1. בטלגרם, פתחי צ'אט עם **@BotFather** → `/newbot` → תני שם וקבלי **טוקן**.
2. הגדירי את הטוקן והריצי:
```bash
export TELEGRAM_TOKEN="123456:ABC-הטוקן-שלך"
python3 bot.py
```
3. בטלגרם, שלחי לבוט `/start` ואז שתפי מיקום (📎 ← Location). הבוט יחזיר את המקלט הקרוב + פין על המפה + כפתורי ניווט.

### הרצה תמידית (24/7)
המחשב חייב להיות דולק והבוט לרוץ כדי שהבוט יענה. לאחסון תמידי בחינם אפשר:
- **Railway / Render / Fly.io** — מעלים את התיקייה, מגדירים משתנה סביבה `TELEGRAM_TOKEN`, פקודת הרצה `python3 bot.py`.
- או שרת קטן / Raspberry Pi בבית.

> ⚠️ בוט טלגרם תמיד דורש אינטרנט (גם אצל המשתמש וגם בשרת). בחירום אמיתי הרשת עלולה להיות עמוסה — לכן האפליקציה האופליינית (חלק 1) היא הגיבוי האמין.

---

## עדכון נתוני המקלטים
אם מתקבל קובץ CSV מעודכן (עמודות `objectId,lat,lon,type`):
```bash
# 1. ממירים CSV ל-shelters.json
python3 - <<'PY'
import csv, json
out=[]
with open("מקלטים-shelters.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        try: lat=round(float(row["lat"]),5); lon=round(float(row["lon"]),5)
        except: continue
        out.append([lat,lon,(row.get("type") or "").strip()])
json.dump(out, open("shelters.json","w",encoding="utf-8"), ensure_ascii=False, separators=(",",":"))
print(len(out),"shelters")
PY
# 2. מטמיעים מחדש ל-index.html
python3 - <<'PY'
import json
data=open("shelters.json",encoding="utf-8").read()
cnt=len(json.loads(data))
html=open("index.template.html",encoding="utf-8").read()
open("index.html","w",encoding="utf-8").write(html.replace("%DATA%",data).replace("%COUNT%",f"{cnt:,}"))
PY
```
הבוט קורא את `shelters.json` ישירות — אין צורך בבנייה מחדש עבורו.

## קבצים
| קובץ | תפקיד |
|------|-------|
| `index.html` | האפליקציה האופליינית (עם הנתונים מוטמעים) |
| `index.template.html` | תבנית לבנייה מחדש בעת עדכון נתונים |
| `manifest.json`, `sw.js`, `icon-*.png` | תמיכת PWA / התקנה / אופליין |
| `bot.py` | בוט הטלגרם |
| `shelters.json` | נתוני המקלטים (משותף לבוט) |
| `requirements.txt` | תלויות הבוט |
