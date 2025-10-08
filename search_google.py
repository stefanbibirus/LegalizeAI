# scrapers/search_google.py

from googlesearch import search
import random
import time
import re

# Cuvinte cheie pentru domenii specifice
DOMENII_SPECIFICE = {
    'anpc.ro': [
        'garantie', 'garanție', 'produs', 'consumator', 'cumparator', 'cumpărător',
        'returnat', 'returnare', 'defect', 'stricat', 'reparatie', 'reparație',
        'schimb', 'bani inapoi', 'reclamatie', 'reclamație', 'vanzator', 'vânzător',
        'magazin', 'firma', 'service', 'calitate', 'conformitate', 'neconform'
    ],
    'cdep.ro': [
        'proiect lege', 'parlament', 'deputat', 'camera deputatilor', 'vot',
        'modificare lege', 'initiativa legislativa', 'propunere'
    ],
    'senat.ro': [
        'senat', 'senator', 'camera superioara', 'vot senat', 'aprobare senat'
    ],
    'inm-lex.ro': [
        'jurisprudenta', 'jurisprudență', 'decizie', 'sentinta', 'sentință',
        'instanta', 'instanță', 'judecator', 'judecător', 'tribunal', 'curte'
    ]
}

def detecteaza_domeniu_specific(intrebare: str) -> str:
    """Detectează domeniul juridic specific pe baza întrebării"""
    intrebare_lower = intrebare.lower()
    
    # Calculează scor pentru fiecare domeniu
    scoruri = {}
    
    for domeniu, cuvinte in DOMENII_SPECIFICE.items():
        scor = 0
        for cuvant in cuvinte:
            if cuvant in intrebare_lower:
                # Cuvinte mai lungi primesc scor mai mare
                scor += len(cuvant) * 0.5
                # Bonus pentru matches exacte
                if f' {cuvant} ' in f' {intrebare_lower} ':
                    scor += 2
        scoruri[domeniu] = scor
    
    # Returnează domeniul cu cel mai mare scor, sau None dacă scorul e prea mic
    cel_mai_bun = max(scoruri.items(), key=lambda x: x[1])
    if cel_mai_bun[1] > 3:  # Pragul minim de încredere
        return cel_mai_bun[0]
    
    return None

def cauta_lege_google(intrebare: str) -> str:
    """Caută legi pe multiple site-uri juridice românești cu prioritizare inteligentă"""
    
    # Detectează domeniul specific
    domeniu_prioritar = detecteaza_domeniu_specific(intrebare)
    
    # Site-uri juridice românești de încredere
    site_uri_juridice = [
        "legislatie.just.ro",
        "lege5.ro", 
        "anpc.ro",
        "cdep.ro",
        "senat.ro",
        "inm-lex.ro"
    ]
    
    # Reorganizează lista în funcție de domeniul detectat
    if domeniu_prioritar:
        print(f"🎯 Domeniu detectat: {domeniu_prioritar} - căutare prioritară")
        site_uri_juridice.remove(domeniu_prioritar)
        site_uri_juridice.insert(0, domeniu_prioritar)
    
    # Încearcă căutarea pe fiecare site
    for site in site_uri_juridice:
        try:
            # Construiește query-ul optimizat pentru fiecare tip de site
            if site == 'anpc.ro':
                query = f"protectia consumatorilor {intrebare} site:{site}"
            elif site == 'legislatie.just.ro':
                query = f"lege {intrebare} site:{site}"
            else:
                query = f"{intrebare} site:{site}"
            
            print(f"🔍 Căutare pe {site}...")
            
            # Căută pe site-ul curent
            rezultate = list(search(query, num_results=3))
            
            for rezultat in rezultate:
                # Verifică dacă e un link valid către un document juridic
                if verifica_link_juridic(rezultat, site):
                    print(f"✅ Găsit pe {site}: {rezultat}")
                    return rezultat
            
            # Pauză între căutări pentru a evita rate limiting
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"⚠️ Eroare căutare pe {site}: {e}")
            continue
    
    # Căutare generală dacă nu găsește pe site-uri specifice
    try:
        print("🔍 Căutare generală pe toate site-urile...")
        all_sites_query = f"{intrebare} " + " OR ".join([f"site:{site}" for site in site_uri_juridice])
        
        for rezultat in search(all_sites_query, num_results=10):
            for site in site_uri_juridice:
                if site in rezultat and verifica_link_juridic(rezultat, site):
                    print(f"✅ Găsit în căutarea generală: {rezultat}")
                    return rezultat
        
        return "❌ Nu am găsit nicio lege relevantă pe site-urile juridice românești"
        
    except Exception as e:
        return f"❌ Eroare la căutarea generală: {e}"

def verifica_link_juridic(url: str, site: str) -> bool:
    """Verifică dacă URL-ul pare să fie către un document juridic valid"""
    
    # Cuvinte cheie care indică documente juridice
    cuvinte_juridice = [
        "lege", "ordonanta", "hotarare", "decizie", "ordin",
        "regulament", "normativ", "cod", "constitutie",
        "DetaliiDocument", "legislatie", "document"
    ]
    
    # Site-uri specifice au pattern-uri diferite
    if site == "legislatie.just.ro":
        return "DetaliiDocument" in url or "PublicareDocument" in url
    
    elif site == "lege5.ro":
        return any(keyword in url.lower() for keyword in ["gratuit/", "lege", "ordonanta", "hotarare"])
    
    elif site == "anpc.ro":
        return any(keyword in url.lower() for keyword in ["legislatie", "normativ", "regulament"])
    
    elif site == "cdep.ro":
        return any(keyword in url.lower() for keyword in ["pls/", "legis/", "lege"])
    
    elif site == "senat.ro":
        return any(keyword in url.lower() for keyword in ["legis/", "lege", "proiect"])
    
    # Verificare generală pentru alte site-uri
    return any(keyword in url.lower() for keyword in cuvinte_juridice)

def cauta_lege_multiple_engines(intrebare: str) -> list:
    """Caută pe multiple motoare și returnează o listă de rezultate cu prioritizare inteligentă"""
    rezultate = []
    
    # Detectează domeniul specific
    domeniu_prioritar = detecteaza_domeniu_specific(intrebare)
    
    site_uri = ["legislatie.just.ro", "lege5.ro", "anpc.ro", "cdep.ro"]
    
    # Reorganizează în funcție de domeniu
    if domeniu_prioritar and domeniu_prioritar in site_uri:
        site_uri.remove(domeniu_prioritar)
        site_uri.insert(0, domeniu_prioritar)
    
    for site in site_uri:
        try:
            # Query optimizat pentru fiecare site
            if site == 'anpc.ro':
                query = f"protectia consumatorilor garantie {intrebare} site:{site}"
            elif site == 'legislatie.just.ro':
                query = f"lege {intrebare} site:{site}"
            else:
                query = f"{intrebare} site:{site}"
            
            rezultate_site = list(search(query, num_results=2))
            
            for url in rezultate_site:
                if verifica_link_juridic(url, site):
                    relevanta = calculeaza_relevanta(url, intrebare)
                    
                    # Bonus pentru domeniul prioritar
                    if site == domeniu_prioritar:
                        relevanta += 3.0
                    
                    rezultate.append({
                        'url': url,
                        'site': site,
                        'relevanta': relevanta
                    })
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"⚠️ Eroare pe {site}: {e}")
            continue
    
    # Sortează după relevanță
    rezultate.sort(key=lambda x: x['relevanta'], reverse=True)
    
    return rezultate

def calculeaza_relevanta(url: str, intrebare: str) -> float:
    """Calculează scorul de relevanță al unui URL pentru întrebare"""
    scor = 0.0
    
    # Cuvinte cheie din întrebare
    cuvinte_intrebare = intrebare.lower().split()
    
    # Verifică dacă cuvintele din întrebare apar în URL
    for cuvant in cuvinte_intrebare:
        if len(cuvant) > 3 and cuvant in url.lower():
            scor += 1.0
    
    # Bonus pentru site-uri de încredere
    if "legislatie.just.ro" in url:
        scor += 2.0
    elif "lege5.ro" in url:
        scor += 1.5
    elif "anpc.ro" in url:
        scor += 1.8  # Mărit pentru protecția consumatorilor
    
    # Bonus pentru tipuri specifice de documente
    if "lege" in url.lower():
        scor += 1.0
    elif "ordonanta" in url.lower():
        scor += 0.8
    elif "hotarare" in url.lower():
        scor += 0.6
    
    # Bonus special pentru cuvinte legate de protecția consumatorilor
    cuvinte_consumatori = ['garantie', 'garanție', 'consumator', 'produs', 'cumparator', 'protectia-consumatorilor']
    for cuvant in cuvinte_consumatori:
        if cuvant in url.lower():
            scor += 2.0
            
    # Bonus pentru cuvinte din întrebare care apar în URL
    for cuvant in ['garantie', 'garanție', 'produs', 'firma', 'responsabilitate']:
        if cuvant in intrebare.lower() and cuvant in url.lower():
            scor += 1.5
    
    return scor

def cauta_cu_fallback(intrebare: str) -> str:
    """Căutare cu fallback pe multiple strategii"""
    
    # Strategia 1: Căutare specifică pe fiecare site
    rezultat = cauta_lege_google(intrebare)
    if not rezultat.startswith("❌"):
        return rezultat
    
    print("🔄 Încerc strategii alternative...")
    
    # Strategia 2: Pentru protecția consumatorilor, caută direct legile cunoscute
    if any(cuvant in intrebare.lower() for cuvant in ['garantie', 'garanție', 'produs', 'consumator', 'cumparator']):
        print("🎯 Încerc să găsesc legile specifice pentru protecția consumatorilor...")
        
        # Termeni specifici pentru protecția consumatorilor
        termeni_consumatori = [
            "Ordonanta 21 1992 protectia consumatorilor site:legislatie.just.ro",
            "Legea 449 2003 vanzarea bunurilor de consum site:legislatie.just.ro",
            "protectia consumatorilor garantie site:legislatie.just.ro",
            "conformitatea bunurilor de consum site:lege5.ro",
            "garantie legala produs site:lege5.ro"
        ]
        
        for termen in termeni_consumatori:
            try:
                print(f"🔍 Caut: {termen.split('site:')[0]}")
                for rezultat in search(termen, num_results=3):
                    site_din_url = next((site for site in ['legislatie.just.ro', 'lege5.ro', 'anpc.ro'] if site in rezultat), None)
                    if site_din_url and verifica_link_juridic(rezultat, site_din_url):
                        print(f"✅ Găsit lege specifică: {rezultat}")
                        return rezultat
                time.sleep(2)
            except Exception:
                continue
    
    # Strategia 3: Căutare cu termeni modificați
    termeni_alternativi = [
        f"legislatie {intrebare}",
        f"lege {intrebare}",
        f"normativ {intrebare}",
        f"{intrebare} romania"
    ]
    
    for termen in termeni_alternativi:
        try:
            for rezultat in search(f"{termen} site:legislatie.just.ro OR site:lege5.ro", num_results=3):
                if verifica_link_juridic(rezultat, "legislatie.just.ro") or verifica_link_juridic(rezultat, "lege5.ro"):
                    print(f"✅ Găsit cu termen alternativ: {rezultat}")
                    return rezultat
            time.sleep(2)
        except Exception:
            continue
    
    return "❌ Nu am găsit nicio lege relevantă după toate încercările"

# Pentru compatibilitate cu codul existent
def cauta_lege_google_original(intrebare: str) -> str:
    """Versiunea originală pentru legislatie.just.ro"""
    query = f"{intrebare} site:legislatie.just.ro"
    
    try:
        for rezultat in search(query, num_results=5):
            if "DetaliiDocument" in rezultat:
                return rezultat
        return "❌ Nu am găsit nicio lege relevantă pe legislatie.just.ro"
    except Exception as e:
        return f"❌ Eroare la căutare: {e}"