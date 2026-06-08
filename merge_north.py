#!/usr/bin/env python3
"""
מושך שכבות מקלטים עירוניות פתוחות (ArcGIS) וממזג לרשימה הקיימת בלי כפילויות.
דה-דופ: נקודה חדשה נדחית אם היא ברדיוס ~25מ' מנקודה קיימת/שכבר נוספה.
"""
import json, urllib.request, urllib.parse, math, ssl, sys

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

# (label, FeatureServer base URL). נגלה אוטומטית את שכבות הנקודות בכל שירות.
SOURCES = [
    ("עמק יזרעאל",      "https://services7.arcgis.com/1ptlMSlFOlAMxpnz/arcgis/rest/services/izr_shelters2023/FeatureServer"),
    ("עכו",            "https://services8.arcgis.com/GY0eO9hmNflcIYdR/arcgis/rest/services/%D7%9E%D7%A7%D7%9C%D7%98%D7%99%D7%9D_%D7%A6%D7%99%D7%91%D7%95%D7%A8%D7%99%D7%99%D7%9D/FeatureServer"),
    ("כפר קרע",        "https://services3.arcgis.com/3HnV0PmVX9ouSGr5/arcgis/rest/services/ShelterMap170625/FeatureServer"),
    ("עין השופט",      "https://services1.arcgis.com/3enY5rJCx4wfEJFc/arcgis/rest/services/%D7%9E%D7%A7%D7%9C%D7%98%D7%99%D7%9D/FeatureServer"),
    ("מקלטים פתוחים",  "https://services2.arcgis.com/cjDo9oPmimdHxumn/arcgis/rest/services/%D7%9E%D7%A4%D7%AA_%D7%9E%D7%A7%D7%9C%D7%98%D7%99%D7%9D_%D7%A4%D7%AA%D7%95%D7%97%D7%99%D7%9D_WFL1/FeatureServer"),
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent":"shelter-merge"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return json.load(r)

def point_layers(base):
    try:
        d = get(base + "?f=json")
    except Exception as e:
        return []
    out=[]
    for l in d.get("layers",[]):
        # query layer def for geometryType
        try:
            ld = get(f"{base}/{l['id']}?f=json")
            if ld.get("geometryType")=="esriGeometryPoint":
                out.append(l["id"])
        except Exception:
            pass
    return out

def fetch_points(base, lid):
    url = f"{base}/{lid}/query?" + urllib.parse.urlencode({
        "where":"1=1","outFields":"*","outSR":"4326","f":"geojson"})
    try:
        d = get(url)
    except Exception as e:
        return []
    pts=[]
    for f in d.get("features",[]):
        g=f.get("geometry") or {}
        if g.get("type")=="Point":
            lon,lat=g["coordinates"][:2]
            if lat and lon: pts.append((round(lat,5),round(lon,5)))
    return pts

# ----- load existing -----
existing = json.load(open("shelters.json", encoding="utf-8"))
print(f"קיים: {len(existing)}")

# spatial grid for ~25m dedup (0.00025 deg lat ~ 27m)
CELL=0.00025
def key(lat,lon): return (round(lat/CELL), round(lon/CELL))
def too_close(lat,lon, grid):
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for (la,lo) in grid.get((round(lat/CELL)+dx, round(lon/CELL)+dy), []):
                # ~25m check
                if abs(la-lat)<0.00023 and abs(lo-lon)<0.00027:
                    return True
    return False

grid={}
for s in existing:
    grid.setdefault(key(s[0],s[1]),[]).append((s[0],s[1]))

added=[]
for label, base in SOURCES:
    lids = point_layers(base)
    n_new=0; n_fetch=0
    for lid in lids:
        for lat,lon in fetch_points(base, lid):
            n_fetch+=1
            if 29.0<lat<33.5 and 34.0<lon<36.0 and not too_close(lat,lon,grid):
                added.append([lat,lon,f"מקלט ציבורי ({label})"])
                grid.setdefault(key(lat,lon),[]).append((lat,lon))
                n_new+=1
    print(f"  {label}: נמשכו {n_fetch}, נוספו {n_new}")

merged = existing + added
json.dump(merged, open("shelters.json","w",encoding="utf-8"), ensure_ascii=False, separators=(",",":"))
print(f"סהכ נוספו: {len(added)}  ->  רשימה חדשה: {len(merged)}")
