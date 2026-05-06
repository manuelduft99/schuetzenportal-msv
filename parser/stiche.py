import requests
from bs4 import BeautifulSoup

EVENT = "SGKSF2025"

BASE_URL = "https://resultat.schuetzenportal.ch"

def lade_stiche():
    """
    Findet automatisch alle Stich-Ranglisten des Anlasses.
    """
    url = f"{BASE_URL}/?evt={EVENT}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    stiche = {}

    # Alle Links im Menü durchsuchen
    for a in soup.find_all("a", href=True):
        href = a["href"]
        name = a.text.strip()

        if "Ranklist" not in href:
            continue

        if not name:
            continue

        # Absolute URL bauen
        if href.startswith("/"):
            href = BASE_URL + href

        # Vereinstyp erkennen
        if "ClubConcurrence" in href:
            stich_typ = "verein"
        else:
            stich_typ = "einzel"

        stiche[name] = {
            "typ": stich_typ,
            "url": href
        }

    return stiche
