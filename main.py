# main.py

import openai
from scraper import extrage_text_lege as ext, test_structura_juridica as test
from search_google import cauta_lege_google, cauta_lege_multiple_engines as cauta_all, cauta_fallback 

try:
    from multi_site_extractor import MultiSiteLegalExtractor as Extractor
    MULTI = True
except ImportError:
    MULTI = False
    print("multi-site extractor lipsa")

openai.api_base = "http://localhost:11434/v1"
openai.api_key = "------------"

def ask_llm(ctx, q):
    try:
        cuv = ['garantie', 'produs', 'cumparator', 'consumator', 'firma', 'magazin', 'defect', 'stricat']
        e_consumator = any(c in q.lower() for c in cuv)

        if e_consumator:
            sys = "Esti expert in dreptul consumatorilor. Raspunde pe baza legii."
        else:
            sys = "Esti asistent juridic. Raspunde doar pe baza textului."

        r = openai.ChatCompletion.create(
            model="mistral",
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": f"{ctx}\n\nINTREBARE: {q}"}
            ],
            temperature=0.1,
            max_tokens=2500
        )
        return r['choices'][0]['message']['content']
    except Exception as e:
        return f"Eroare: {e}"

def banner():
    print("=" * 40)
    print("LEGALIZE AI")
    print("=" * 40)

def meniu():
    print("\nOptiuni:")
    print("1. Intrebare")
    print("2. Cautare multipla")
    print("3. Testeaza URL")
    print("4. Analiza structura")
    print("5. Site-uri")
    print("6. Iesire")

def intrebare():
    q = input("Intrebarea:\n> ").strip()
    if not q:
        print("Intrebare invalida")
        return

    print("Caut lege...")
    url = cauta_fallback(q)

    if not url.startswith("http"):
        print(url)
        return

    print("Extrag text...")
    txt = ext(url)
    if txt.startswith("Eroare") or not txt:
        print("Nu s-a extras nimic")
        return

    s = test(txt)
    if s['articole'] == 0:
        print("Structura slaba. Incerc altceva...")
        rez = cauta_all(q)
        if len(rez) > 1:
            txt2 = ext(rez[1]['url'])
            if not txt2.startswith("Eroare"):
                txt = txt2
                url = rez[1]['url']

    ans = ask_llm(txt, q)
    print("\nRaspuns:")
    print(ans)
    print("\nSursa:", url)

def cautare_multipla():
    if not MULTI:
        print("Modul lipsa")
        return

    q = input("Intrebarea:\n> ").strip()
    if not q:
        print("Intrebare invalida")
        return

    rez = cauta_all(q)
    if not rez:
        print("Nimic gasit")
        return

    for i, r in enumerate(rez[:5], 1):
        print(f"{i}. {r['site']} - {r['url'][:80]}")

    try:
        i = int(input("Alege: ")) - 1
        if 0 <= i < len(rez):
            url = rez[i]['url']
            url_direct(url)
    except:
        print("Input invalid")

def url_direct(url=None):
    if not url:
        url = input("URL:\n> ").strip()

    if not url.startswith("http"):
        print("URL invalid")
        return

    txt = ext(url)
    if txt.startswith("Eroare"):
        print("Eroare la extragere")
        return

    rasp = input("Pui intrebare? (da/nu): ").strip().lower()
    if rasp in ['da', 'd', 'y']:
        q = input("Intrebarea: ").strip()
        if q:
            ans = ask_llm(txt, q)
            print("\nRaspuns:")
            print(ans)
            print("\nSursa:", url)

def siteuri():
    print("Site-uri suportate:")
    print("- legislatie.just.ro")
    print("- lege5.ro")
    print("- anpc.ro")
    print("- cdep.ro")

def test_structura():
    url = input("URL:\n> ").strip()
    if not url.startswith("http"):
        print("URL invalid")
        return

    txt = ext(url)
    if txt.startswith("Eroare"):
        print("Eroare la extragere")
        return

    print("Text:")
    print(txt[:300])
    s = test(txt)
    print("Articole:", s['articole'])
    print("Alineate:", s['alineate'])
    print("Litere:", s['litere'])

def main():
    banner()
    while True:
        meniu()
        opt = input("Optiune: ").strip()
        if opt == "1":
            intrebare()
        elif opt == "2":
            cautare_multipla()
        elif opt == "3":
            url_direct()
        elif opt == "4":
            test_structura()
        elif opt == "5":
            siteuri()
        elif opt == "6":
            print("Bye")
            break
        else:
            print("Optiune invalida")

if __name__ == "__main__":
    main()
