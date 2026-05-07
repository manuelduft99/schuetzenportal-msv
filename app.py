from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from parser.rangliste import (
    lade_vereinsresultate,
    lade_vereinskonkurrenz
)

import sqlite3
import json
import time

# --------------------------------------------------
# App & Templates
# --------------------------------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --------------------------------------------------
# Datenbank (SQLite Cache)
# --------------------------------------------------
DB_PATH = "cache.db"
CACHE_TTL = 1800  # 30 Minuten


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ranglisten (
            url TEXT PRIMARY KEY,
            daten_json TEXT,
            last_update INTEGER
        )
    """)
    conn.commit()
    conn.close()


init_db()


def get_rangliste(url: str):
    """Liefert Rangliste + Cache-Zeitpunkt (SQLite, 30‑Min‑TTL)"""
    now = int(time.time())

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT daten_json, last_update FROM ranglisten WHERE url = ?",
        (url,)
    )
    row = cur.fetchone()

    if row:
        daten_json, last_update = row
        if now - last_update < CACHE_TTL:
            conn.close()
            return json.loads(daten_json), last_update

    # Cache MISS → neu laden
    daten = lade_vereinsresultate(url, VEREINSNAMEN["einzel"])

    cur.execute("""
        INSERT OR REPLACE INTO ranglisten
        (url, daten_json, last_update)
        VALUES (?, ?, ?)
    """, (
        url,
        json.dumps(daten, ensure_ascii=False),
        now
    ))

    conn.commit()
    conn.close()
    return daten, now


def cache_age_text(timestamp: int) -> str:
    minutes = (int(time.time()) - timestamp) // 60
    if minutes <= 0:
        return "gerade eben aktualisiert"
    if minutes == 1:
        return "vor 1 Minute aktualisiert"
    return f"vor {minutes} Minuten aktualisiert"


# --------------------------------------------------
# Vereinsnamen (wie im Schützenportal)
# --------------------------------------------------
VEREINSNAMEN = {
    "verein": "Rufi-Maseltrangen Militärschützenverein",
    "einzel": "Rufi-Maseltrangen MSV",
}

# --------------------------------------------------
# Event & Stiche (DEINE Struktur)
# --------------------------------------------------
EVENT = "ESF2026"

G300_EINZELSTICHE = {
    "Vereinsstich": {
        "Sport":  {"mid": 5,  "eid": 6436},
        "Feld D": {"mid": 6,  "eid": 6437},
        "Feld E": {"mid": 7,  "eid": 6438},
    },
    "Kunst": {
        "Sport":  {"mid": 9,  "eid": 6439},
        "Feld D": {"mid": 10, "eid": 6440},
        "Feld E": {"mid": 11, "eid": 6441},
    },
    "Militär": {
        "Sport":  {"mid": 13, "eid": 6442},
        "Feld D": {"mid": 14, "eid": 6443},
        "Feld E": {"mid": 15, "eid": 6444},
    },
    "Auszahlung": {
        "Sport":  {"mid": 17, "eid": 6445},
        "Feld D": {"mid": 18, "eid": 6446},
        "Feld E": {"mid": 19, "eid": 6447},
    },
    "Serie": {
        "Sport":  {"mid": 21, "eid": 6448},
        "Feld D": {"mid": 22, "eid": 6449},
        "Feld E": {"mid": 23, "eid": 6450},
    },
    "Pizol": {
        "Sport":  {"mid": 25, "eid": 6451},
        "Feld D": {"mid": 26, "eid": 6452},
        "Feld E": {"mid": 27, "eid": 6453},
    },
    "Kranz": {
        "Sport":  {"mid": 29, "eid": 6454},
        "Feld D": {"mid": 30, "eid": 6455},
        "Feld E": {"mid": 31, "eid": 6456},
    },
    "Ehrengaben": {
        "Sport":  {"mid": 33, "eid": 6457},
        "Feld D": {"mid": 34, "eid": 6458},
        "Feld E": {"mid": 35, "eid": 6459},
    },
    "Veteran": {
        "Sport":  {"mid": 37, "eid": 6460},
        "Feld D": {"mid": 38, "eid": 6461},
        "Feld E": {"mid": 39, "eid": 6462},
    },
    "Nachwuchs": {
        "Sport":  {"mid": 41, "eid": 6463},
        "Feld E": {"mid": 42, "eid": 6464},
    },
    "Nachdoppel": {
        "Sport":  {"mid": 44, "eid": 6466},
        "Feld D": {"mid": 45, "eid": 6467},
        "Feld E": {"mid": 46, "eid": 6468},
    },

}
def build_stiche():
    stiche = {
        "Vereinskonkurrenz": {
            "typ": "verein",
            "url": (
                "https://resultat.schuetzenportal.ch/"
                "ClubConcurrence/ShowClubRanklist"
                f"?mid=58&cid=1416&evt={EVENT}"
            ),
        }
    }

    stiche["Gruppenwettkampf"] = {
    "typ": "gruppe",
    "kategorien": {
        "Sport": {
            "url": "https://resultat.schuetzenportal.ch/GroupCompetition/ShowGroupRanklist?mid=64&gid=488&evt=SGKSF2025"
        },
        "Feld D": {
            "url": "https://resultat.schuetzenportal.ch/GroupCompetition/ShowGroupRanklist?mid=65&gid=498&evt=SGKSF2025"
        },
        "Feld E": {
            "url": "https://resultat.schuetzenportal.ch/GroupCompetition/ShowGroupRanklist?mid=66&gid=499&evt=SGKSF2025"
        },
    }
}


    for stich_name, kategorien in G300_EINZELSTICHE.items():
        stiche[stich_name] = {
            "typ": "einzel",
            "kategorien": {}
        }

        for kat_name, ids in kategorien.items():
            stiche[stich_name]["kategorien"][kat_name] = {
                "url": (
                    "https://resultat.schuetzenportal.ch/"
                    "SingleRanklist/ShowCompetitionRanklist"
                    f"?mid={ids['mid']}&eid={ids['eid']}&evt={EVENT}"
                )
            }

    return stiche


STICHE = build_stiche()

# --------------------------------------------------
# Routen
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def startseite(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"stiche": STICHE}
    )


@app.get("/stich/{stich_name}", response_class=HTMLResponse)
def stich_detail(request: Request, stich_name: str):
    stich = STICHE.get(stich_name)
    if not stich:
        return HTMLResponse("Stich nicht gefunden", 404)

    if stich["typ"] == "verein":
        daten = lade_vereinskonkurrenz(
            stich["url"],
            VEREINSNAMEN["verein"]
        )
        return templates.TemplateResponse(
            request,
            "vereinskonkurrenz.html",
            {
                "stich": stich_name,
                "resultate": daten,
                "back_url": "/",
            }
        )

    return templates.TemplateResponse(
        request,
        "stich_auswahl.html",
        {
            "stich_name": stich_name,
            "kategorien": stich["kategorien"],
            "back_url": "/",
        }
    )

@app.get("/stich/{stich_name}/gesamt", response_class=HTMLResponse)
def stich_gesamt(request: Request, stich_name: str):
    stich = STICHE.get(stich_name)
    if not stich or stich["typ"] != "einzel":
        return HTMLResponse("Stich nicht gefunden", status_code=404)

    # Alle Resultate sammeln
    schiessen = []

    for kat_name, kat in stich["kategorien"].items():
        daten, _ = get_rangliste(kat["url"])
        for r in daten:
            schiessen.append({
                "vorname": r["vorname"],
                "nachname": r["nachname"],
                "total": r["total"],
                "feld": kat_name,
                "rang": r["rang"],
            })

    # Beste Leistung pro Schütze bestimmen
    beste = {}
    for r in schiessen:
        key = (r["vorname"], r["nachname"])
        if key not in beste or int(r["total"]) > int(beste[key]["total"]):
            beste[key] = r

    # Sortieren nach Total
    gesamt = sorted(
        beste.values(),
        key=lambda x: int(x["total"]),
        reverse=True
    )

    return templates.TemplateResponse(
        request,
        "stich_gesamt.html",
        {
            "stich": stich_name,
            "resultate": gesamt,
            "back_url": f"/stich/{stich_name}",
        }
    )
def berechne_gesamtwertung(stich_name: str):
    stich = STICHE.get(stich_name)
    if not stich or stich["typ"] != "einzel":
        return []

    sammel = []

    for kat_name, kat in stich["kategorien"].items():
        daten, _ = get_rangliste(kat["url"])
        for r in daten:
            sammel.append({
                "vorname": r["vorname"],
                "nachname": r["nachname"],
                "total": int(r["total"]),
            })

    beste = {}
    for r in sammel:
        key = (r["vorname"], r["nachname"])
        if key not in beste or r["total"] > beste[key]["total"]:
            beste[key] = r

    gesamt = sorted(
        beste.values(),
        key=lambda x: x["total"],
        reverse=True
    )

    return gesamt

@app.get("/stich/{stich_name}/{kategorie}", response_class=HTMLResponse)
def stich_kategorie(request: Request, stich_name: str, kategorie: str):
    stich = STICHE.get(stich_name)
    if not stich:
        return HTMLResponse("Stich nicht gefunden", 404)

    kat = stich["kategorien"].get(kategorie)
    if not kat:
        return HTMLResponse("Kategorie nicht gefunden", 404)

    daten, last_update = get_rangliste(kat["url"])

    return templates.TemplateResponse(
    request,
    "stich.html",
    {
        "stich": f"{stich_name} – {kategorie}",
        "resultate": daten,
        "back_url": f"/stich/{stich_name}",
        "cache_text": cache_age_text(last_update),
        "cache_url": kat["url"],
        "current_path": request.url.path,

        # ✅ NEU: Originalrangliste
        "original_url": kat["url"],
    }
)


@app.post("/cache/refresh")
def refresh_cache(
    url: str = Form(...),
    redirect_to: str = Form(...)
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM ranglisten WHERE url = ?", (url,))
    conn.commit()
    conn.close()

    return RedirectResponse(url=redirect_to, status_code=303)

@app.get("/schuetze/{stich}/{kategorie}/{vereinsrang}", response_class=HTMLResponse)
def schuetzenprofil(
    request: Request,
    stich: str,
    kategorie: str,
    vereinsrang: int
):
    # -------------------------------
    # 1) Referenz-Schütze bestimmen
    # -------------------------------
    stich_cfg = STICHE.get(stich)
    if not stich_cfg:
        return HTMLResponse("Stich nicht gefunden", 404)

    kat_cfg = stich_cfg["kategorien"].get(kategorie)
    if not kat_cfg:
        return HTMLResponse("Kategorie nicht gefunden", 404)

    ref_daten, _ = get_rangliste(kat_cfg["url"])
    if vereinsrang < 1 or vereinsrang > len(ref_daten):
        return HTMLResponse("Schütze nicht gefunden", 404)

    ref = ref_daten[vereinsrang - 1]
    ref_vorname = ref["vorname"]
    ref_nachname = ref["nachname"]

    # -------------------------------
    # 2) ALLE Ranglisten EINMAL laden
    # -------------------------------
    ranglisten = {}

    for stich_name, stich_data in STICHE.items():
        if stich_data["typ"] != "einzel":
            continue

        ranglisten[stich_name] = {}
        for kat_name, kat_data in stich_data["kategorien"].items():
            daten, _ = get_rangliste(kat_data["url"])
            ranglisten[stich_name][kat_name] = daten

    # -------------------------------
    # 3) Resultate des Schützen sammeln
    # -------------------------------
    alle_resultate = []

    for stich_name, kat_map in ranglisten.items():
        # ---- Gesamtwertung pro Stich ----
        beste = {}

        for kat_name, daten in kat_map.items():
            for r in daten:
                key = (r["vorname"], r["nachname"])
                total = int(r["total"])
                if key not in beste or total > beste[key]["total"]:
                    beste[key] = {
                        "vorname": r["vorname"],
                        "nachname": r["nachname"],
                        "total": total
                    }

        gesamt_liste = sorted(
            beste.values(),
            key=lambda x: x["total"],
            reverse=True
        )

        gesamt_rang = None
        for pos, r in enumerate(gesamt_liste, start=1):
            if r["vorname"] == ref_vorname and r["nachname"] == ref_nachname:
                gesamt_rang = pos
                break

        # ---- Einzelresultate dieses Stichs ----
        for kat_name, daten in kat_map.items():
            for r in daten:
                if (
                    r["vorname"] == ref_vorname
                    and r["nachname"] == ref_nachname
                ):
                    alle_resultate.append({
                        "stich": stich_name,
                        "kategorie": kat_name,
                        "gesamt_rang": gesamt_rang,
                        "rang": r.get("rang"),
                        "total": r.get("total"),
                    })

    # -------------------------------
    # 4) Rendern
    # -------------------------------
    return templates.TemplateResponse(
        request,
        "schuetze.html",
        {
            "vorname": ref_vorname,
            "nachname": ref_nachname,
            "resultate": alle_resultate,
            "back_url": f"/stich/{stich}/{kategorie}",
        }
    )

from parser.gruppen import lade_gruppenresultate

@app.get("/gruppe/{stich_name}", response_class=HTMLResponse)
def gruppenwettkampf(request: Request, stich_name: str):
    stich = STICHE.get(stich_name)
    if not stich:
        return HTMLResponse("Gruppenstich nicht gefunden", status_code=404)

    resultate = []

    for feld, cfg in stich["kategorien"].items():
        daten = lade_gruppenresultate(
            cfg["url"],
            VEREINSNAMEN["einzel"]
        )

        for r in daten:
            resultate.append({
                "feld": feld,
                "rang": r["rang"],
                "gruppe": r["gruppe"],
                "total": r["total"],
            })

    return templates.TemplateResponse(
        request,
        "gruppen.html",
        {
            "stich": stich_name,
            "resultate": resultate,
            "back_url": "/",
        }
    )