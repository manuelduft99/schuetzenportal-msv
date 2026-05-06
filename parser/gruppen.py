import requests
from bs4 import BeautifulSoup
import re

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def lade_gruppenresultate(url: str, vereinsname: str):
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
    idx_gruppe = find_col(["gruppe"])
    idx_verein = find_col(["verein"])
    idx_total  = find_col(["total"])

    if None in (idx_rang, idx_gruppe, idx_verein, idx_total):
        return []

    resultate = []

    
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

    for tr in rows:
        tds = [td.text.strip() for td in tr.find_all("td")]
        if len(tds) <= max(idx_rang, idx_gruppe, idx_verein, idx_total):
            continue

        if normalize(vereinsname) not in normalize(tds[idx_verein]):
            continue

        resultate.append({
            "rang": tds[idx_rang],
            "gruppe": tds[idx_gruppe],
            "total": tds[idx_total],
        })

    return resultate