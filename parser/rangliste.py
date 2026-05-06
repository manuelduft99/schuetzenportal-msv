import requests
from bs4 import BeautifulSoup
import re

# -------------------------------------------------
# Hilfsfunktion: Text normalisieren (für Vereinsvergleich)
# -------------------------------------------------
def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


# =================================================
# EINZELRANGLISTE (z. B. Vereinsstich / Kunststich)
# =================================================
def lade_vereinsresultate(url: str, vereinsname: str):
    """
    Liest eine Einzelrangliste aus dem Schützenportal.
    Erwartet explizite Spalten: Nachname, Vorname, Verein, Rang, Total.
    """

    r = requests.get(url, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    headers = [th.text.strip().lower() for th in table.find_all("th")]

    def find_col(keys):
        for i, h in enumerate(headers):
            for k in keys:
                if k in h:
                    return i
        return None

    idx_rang     = find_col(["rang"])
    idx_nachname = find_col(["nachname"])
    idx_vorname  = find_col(["vorname"])
    idx_verein   = find_col(["verein"])
    idx_total    = find_col(["total"])

    if None in (idx_rang, idx_nachname, idx_vorname, idx_verein, idx_total):
        return []

    resultate = []

    rows = table.find("tbody").find_all("tr")
    for tr in rows:
        tds = [td.text.strip() for td in tr.find_all("td")]

        if len(tds) <= max(idx_rang, idx_nachname, idx_vorname, idx_verein, idx_total):
            continue

        # ✅ Filter auf Verein (nur Vereinsspalte!)
        if normalize(vereinsname) not in normalize(tds[idx_verein]):
            continue

        nachname = tds[idx_nachname]
        vorname  = tds[idx_vorname]

        resultate.append({
            "rang": tds[idx_rang],
            "vorname": vorname,
            "nachname": nachname,
            "name": f"{vorname} {nachname}".strip(),
            "total": tds[idx_total],
        })

    return resultate


# =================================================
# VEREINSKONKURRENZ
# =================================================
def lade_vereinskonkurrenz(url: str, vereinsname: str):
    """
    Liest die Vereinskonkurrenz.
    Erwartet genau EIN Ergebnis für den eigenen Verein.
    """

    r = requests.get(url, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    headers = [th.text.strip().lower() for th in table.find_all("th")]

    def find_col(keys):
        for i, h in enumerate(headers):
            for k in keys:
                if k in h:
                    return i
        return None

    idx_rang   = find_col(["rang"])
    idx_verein = find_col(["verein"])
    idx_total  = find_col(["total"])

    if None in (idx_rang, idx_verein, idx_total):
        return []

    rows = table.find("tbody").find_all("tr")
    for tr in rows:
        tds = [td.text.strip() for td in tr.find_all("td")]

        if len(tds) <= max(idx_rang, idx_verein, idx_total):
            continue

        if normalize(vereinsname) in normalize(tds[idx_verein]):
            # ✅ Genau EIN Verein → sofort zurückgeben
            return [{
                "rang": tds[idx_rang],
                "verein": tds[idx_verein],
                "total": tds[idx_total],
            }]

    return []