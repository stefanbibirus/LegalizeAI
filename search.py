# scrapers/search_legislatie.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def cauta_link_lege(pe_cuvinte: str) -> str:
    url = "https://legislatie.just.ro/Public/SearchDocument"
    payload = {
        "SearchWhat": pe_cuvinte,
        "SearchWhere": "0",
        "PageSize": "20"
    }

    try:
        resp = requests.post(url, data=payload)
        if resp.status_code != 200:
            return "❌ Eroare la căutare"

        soup = BeautifulSoup(resp.content, "html.parser")

        # DEBUG TEMPORAR
        with open("debug_search.html", "w", encoding="utf-8") as f:
            f.write(resp.text)

        # Căutăm TOATE linkurile care duc la detalii
        linkuri = soup.find_all("a", href=True)
        for link_tag in linkuri:
            href = link_tag["href"]
            text = link_tag.get_text(strip=True)

            # Filtrăm doar linkuri care par a fi legi relevante
            if "/Public/DetaliiDocument/" in href and "LEGE" in text.upper():
                return urljoin("https://legislatie.just.ro", href)

        return "❌ Nu am găsit nicio lege relevantă în rezultate"

    except Exception as e:
        return f"❌ Eroare la căutare: {e}"
