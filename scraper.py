# scraper.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

def extrage_text_structurat(element):
    """Extrage textul păstrând structura juridică (articole, alineate, litere)"""
    if not element:
        return ""
    
    # Elimină complet toate elementele nedorite ÎNAINTE de procesare
    for unwanted in element.select('script, style, nav, footer, .navbar, .menu, .navigation, #menu, .header, .breadcrumb'):
        unwanted.decompose()
    
    # Elimină div-urile cu clase specifice pentru navigare
    for unwanted in element.select('div[class*="nav"], div[id*="nav"], div[class*="menu"], div[id*="menu"]'):
        unwanted.decompose()
    
    # Găsește toate elementele text în ordine
    text_parts = []
    
    # Procesează fiecare element pentru a păstra structura
    for elem in element.descendants:
        if elem.name in ['br', 'p', 'div']:
            # Adaugă o linie nouă pentru separare
            if text_parts and not text_parts[-1].endswith('\n'):
                text_parts.append('\n')
        
        # Extrage textul actual
        if hasattr(elem, 'string') and elem.string:
            text = elem.string.strip()
            if text:
                # Filtrează textul nedorit (CSS, JS, navigare)
                cuvinte_nedorite = [
                    'javascript', 'function', 'var ', 'portal legislativ', 'meniu', 'navbar',
                    'acasă', 'despre proiect', 'facilități', 'legături utile', 'gdpr',
                    'window.location', 'jquery', '$', 'css', 'background-color', 'font-size',
                    'position:', 'margin:', 'padding:', 'width:', 'height:', 'color:'
                ]
                
                if any(unwanted_word in text.lower() for unwanted_word in cuvinte_nedorite):
                    continue
                
                # Verifică dacă este un număr de articol, alineat sau literă
                if re.match(r'^(Art\.|Articolul|ARTICOLUL)\s*\d+', text, re.IGNORECASE):
                    text_parts.append(f'\n\n{text}')
                elif re.match(r'^\(\d+\)', text):  # Alineate (1), (2), etc.
                    text_parts.append(f'\n  {text}')
                elif re.match(r'^[a-z]\)', text):  # Litere a), b), c), etc.
                    text_parts.append(f'\n    {text}')
                elif re.match(r'^\d+\.', text):  # Numere 1., 2., etc.
                    text_parts.append(f'\n  {text}')
                else:
                    # Text normal - verifică dacă pare a fi conținut juridic
                    if len(text) > 10 and not text.isdigit() and not text.startswith('#'):
                        if text_parts and not text_parts[-1].endswith(' '):
                            text_parts.append(f' {text}')
                        else:
                            text_parts.append(text)
    
    # Combină toate părțile
    full_text = ''.join(text_parts)
    
    # Curățare finală mult mai agresivă
    full_text = re.sub(r'\n\s*\n\s*\n', '\n\n', full_text)  # Max 2 linii goale consecutive
    full_text = re.sub(r'[ \t]+', ' ', full_text)  # Spații multiple -> un spațiu
    
    # Elimină liniile care par a fi cod HTML/CSS/JS
    lines = full_text.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        # Păstrează doar liniile care par a fi conținut juridic
        cuvinte_filtrare = ['meniu', 'portal', 'navbar', 'javascript', 'css', 'background', 'color:', 'font-', 'margin', 'padding', 'width:', 'height:']
        
        if (len(line) > 5 and 
            not line.startswith(('<', '/', '#', '.', '{', '}', 'var ', 'function', '$')) and
            not any(word in line.lower() for word in cuvinte_filtrare) and
            not re.match(r'^[^a-zA-Z]*$', line)):  # Nu doar caractere speciale
            clean_lines.append(line)
    
    return '\n'.join(clean_lines).strip()

def extrage_text_structurat_alternativ(soup_element):
    """Metodă alternativă pentru extragerea structurată"""
    html_content = str(soup_element)
    
    # Înlocuiește tag-urile HTML cu formatare text
    replacements = [
        (r'<br[^>]*>', '\n'),
        (r'<p[^>]*>', '\n'),
        (r'</p>', ''),
        (r'<div[^>]*>', '\n'),
        (r'</div>', ''),
        (r'<li[^>]*>', '\n• '),
        (r'</li>', ''),
        (r'<ol[^>]*>', '\n'),
        (r'</ol>', '\n'),
        (r'<ul[^>]*>', '\n'),
        (r'</ul>', '\n'),
        (r'<h[1-6][^>]*>', '\n\n'),
        (r'</h[1-6]>', '\n'),
        (r'<strong[^>]*>', '**'),
        (r'</strong>', '**'),
        (r'<b[^>]*>', '**'),
        (r'</b>', '**'),
        (r'<em[^>]*>', '*'),
        (r'</em>', '*'),
        (r'<i[^>]*>', '*'),
        (r'</i>', '*'),
    ]
    
    for pattern, replacement in replacements:
        html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)
    
    # Elimină tag-urile HTML rămase
    text = re.sub(r'<[^>]+>', '', html_content)
    
    # Curățare și formatare finală
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Identifică și formatează structurile juridice
        if re.match(r'^(Art\.|Articolul|ARTICOLUL)\s*\d+', line, re.IGNORECASE):
            formatted_lines.append(f'\n{line}')
        elif re.match(r'^\(\d+\)', line):  # Alineate
            formatted_lines.append(f'  {line}')
        elif re.match(r'^[a-z]\)', line):  # Litere
            formatted_lines.append(f'    {line}')
        elif re.match(r'^\d+\.', line):  # Numere
            formatted_lines.append(f'  {line}')
        else:
            formatted_lines.append(line)
    
    result = '\n'.join(formatted_lines)
    
    # Curățare finală
    result = re.sub(r'\n{3,}', '\n\n', result)  # Max 2 linii consecutive
    result = re.sub(r'[ \t]+', ' ', result)  # Spații multiple
    
    return result.strip()

def setup_session():
    """Configurează o sesiune robustă pentru requests"""
    session = requests.Session()
    
    # Headers pentru a părea ca un browser real
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Configurează retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def extrage_doar_continut_juridic(element):
    """Extrage DOAR conținutul juridic, eliminând tot HTML/CSS/JS"""
    if not element:
        return ""
    
    # Elimină complet toate elementele problematice
    for unwanted in element.select('script, style, nav, footer, header, .navbar, .nav, .menu, .navigation, .breadcrumb, .header, .footer'):
        unwanted.decompose()
    
    # Găsește toate elementele care conțin text juridic
    juridic_parts = []
    
    # Caută elemente cu clase juridice specifice
    juridic_elements = element.find_all(['div', 'p', 'span'], string=re.compile(r'(Art\.|Articolul|alin|\(\d+\)|[a-z]\))', re.IGNORECASE))
    
    if juridic_elements:
        # Dacă găsește elemente juridice, folosește o metodă mai țintită
        for elem in element.find_all(['div', 'p', 'span', 'td']):
            text = elem.get_text(strip=True)
            if text and este_continut_juridic(text):
                juridic_parts.append(text)
    else:
        # Fallback la metoda standard
        return extrage_text_structurat(element)
    
    # Combină și curăță
    full_text = '\n'.join(juridic_parts)
    
    # Curățare finală
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    full_text = re.sub(r'[ \t]+', ' ', full_text)
    
    return full_text.strip()

def este_continut_juridic(text):
    """Verifică dacă textul pare a fi conținut juridic relevant"""
    if len(text) < 10:
        return False
    
    # Cuvinte care indică conținut juridic
    cuvinte_juridice = [
        'art.', 'articolul', 'alineat', 'litera', 'punct', 'capitol', 'sectiune',
        'lege', 'ordonanta', 'hotarare', 'normativ', 'prevedere', 'dispozitie',
        'obligatie', 'drept', 'sanctiune', 'amenda', 'contraventie'
    ]
    
    # Cuvinte care indică conținut nedorit
    cuvinte_nedorite = [
        'meniu', 'portal', 'navbar', 'javascript', 'function', 'var ', 'css',
        'background', 'color:', 'font-', 'margin', 'padding', 'width:', 'height:',
        'acasă', 'despre', 'facilități', 'legături', 'gdpr', 'jquery', '$'
    ]
    
    text_lower = text.lower()
    
    # Verifică dacă conține cuvinte nedorite
    if any(cuvant in text_lower for cuvant in cuvinte_nedorite):
        return False
    
    # Verifică dacă conține cuvinte juridice SAU numerotare juridică
    has_juridic_words = any(cuvant in text_lower for cuvant in cuvinte_juridice)
    has_juridic_structure = bool(re.search(r'(art\.|articolul|\(\d+\)|[a-z]\)|\d+\.)', text_lower))
    
    return has_juridic_words or has_juridic_structure or len(text) > 50

def extrage_text_lege(url):
    print(f"➡️ Accesăm URL-ul legii: {url}")
    
    session = setup_session()
    
    try:
        # Timeout mai mare pentru site-uri guvernamentale lente
        response = session.get(url, timeout=30)
        print(f"✅ Cod răspuns pagină principală: {response.status_code}")
        
        if response.status_code != 200:
            return f"❌ Eroare la descărcarea paginii principale. Cod: {response.status_code}"
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Elimină COMPLET toate elementele nedorite din start
        for unwanted in soup.select('script, style, nav, footer, header, .navbar, .nav, .menu, .navigation, .breadcrumb, .header, .footer'):
            unwanted.decompose()
        
        # 1. Încearcă iframe
        iframe = soup.find("iframe", src=True)
        if iframe:
            iframe_url = urljoin(url, iframe["src"])
            print(f"➡️ Accesăm iframe: {iframe_url}")
            
            # Așteaptă puțin între requests
            time.sleep(1)
            
            try:
                iframe_resp = session.get(iframe_url, timeout=30)
                print(f"✅ Cod răspuns iframe: {iframe_resp.status_code}")
                
                if iframe_resp.status_code == 200:
                    iframe_soup = BeautifulSoup(iframe_resp.content, "html.parser")
                    
                    # Elimină elementele nedorite din iframe
                    for unwanted in iframe_soup.select('script, style, nav, footer, header, .navbar, .nav, .menu, .navigation'):
                        unwanted.decompose()
                    
                    # Încearcă să găsești zone specifice cu conținut juridic
                    content_selectors = [
                        'div[class*="content"]',
                        'div[class*="text"]',
                        'div[class*="document"]',
                        'div[class*="lege"]',
                        'div[class*="articol"]',
                        'div[id*="content"]',
                        'main',
                        'article'
                    ]
                    
                    for selector in content_selectors:
                        elements = iframe_soup.select(selector)
                        for element in elements:
                            text = extrage_doar_continut_juridic(element)
                            if text and len(text) > 200:  # Mărit minimul
                                print(f"✅ Text găsit cu selector: {selector}")
                                return text[:15000]  # Mărit limita pentru structură
                    
                    # Fallback la tot textul din iframe cu structură
                    text = extrage_doar_continut_juridic(iframe_soup)
                    if text and len(text) > 100:
                        return text[:15000]
                        
            except requests.exceptions.Timeout:
                print("⚠️ Timeout la iframe, continuăm cu pagina principală...")
            except Exception as e:
                print(f"⚠️ Eroare la iframe: {e}, continuăm cu pagina principală...")
        
        # 2. Dacă nu există iframe sau a eșuat, încearcă să extragi textul direct
        print("🔁 Căutăm text direct în HTML...")
        
        # Caută în zone specifice pentru legislația română
        content_selectors = [
            'div[class*="continut"]',
            'div[class*="content"]',
            'div[class*="text"]',
            'div[class*="document"]',
            'div[class*="detalii"]',
            'div[id*="continut"]',
            'div[id*="content"]',
            'main',
            'article',
            '.document-content',
            '.law-content'
        ]
        
        longest_text = ""
        best_selector = ""
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                content = extrage_doar_continut_juridic(element)
                if len(content) > len(longest_text):
                    longest_text = content
                    best_selector = selector
        
        if len(longest_text) > 200:
            print(f"✅ Text găsit cu selector: {best_selector}")
            return longest_text[:15000]
        
        # Ultimul fallback - toate div-urile cu structură
        potential_divs = soup.find_all("div")
        for div in potential_divs:
            content = extrage_doar_continut_juridic(div)
            if len(content) > len(longest_text):
                longest_text = content
        
        if len(longest_text) > 100:
            return longest_text[:15000]
        
        return "❌ Nu am găsit textul legii în pagină"
        
    except requests.exceptions.Timeout:
        return "❌ Timeout - site-ul nu răspunde la timp. Încearcă din nou în câteva minute."
    except requests.exceptions.ConnectionError:
        return "❌ Eroare de conexiune. Verifică conexiunea la internet."
    except requests.exceptions.RequestException as e:
        return f"❌ Eroare de rețea: {e}"
    except Exception as e:
        return f"❌ Eroare la extragerea textului legii: {e}"
    finally:
        session.close()

def extrage_text_lege_robust(url):
    """Versiune mai robustă cu mai multe încercări și structură păstrată"""
    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"🔄 Încercarea {attempt + 1}/{max_retries}")
        
        result = extrage_text_lege(url)
        
        if not result.startswith("❌"):
            # Verifică dacă rezultatul conține structură juridică
            if re.search(r'(Art\.|Articolul|\(\d+\)|[a-z]\))', result):
                print("✅ Structură juridică detectată!")
            return result
        
        if "Timeout" in result and attempt < max_retries - 1:
            wait_time = (attempt + 1) * 5
            print(f"⏳ Așteptăm {wait_time} secunde înainte de următoarea încercare...")
            time.sleep(wait_time)
            continue
        
        return result
    
    return "❌ Nu am reușit să extrag textul după multiple încercări"

def test_structura_juridica(text):
    """Testează dacă textul conține elemente de structură juridică"""
    stats = {
        'articole': len(re.findall(r'(Art\.|Articolul|ARTICOLUL)\s*\d+', text, re.IGNORECASE)),
        'alineate': len(re.findall(r'\(\d+\)', text)),
        'litere': len(re.findall(r'[a-z]\)', text)),
        'numere': len(re.findall(r'^\s*\d+\.', text, re.MULTILINE)),
        'lungime': len(text)
    }
    
    print(f"📊 Statistici structură juridică:")
    print(f"   • Articole găsite: {stats['articole']}")
    print(f"   • Alineate găsite: {stats['alineate']}")
    print(f"   • Litere găsite: {stats['litere']}")
    print(f"   • Numere găsite: {stats['numere']}")
    print(f"   • Lungime text: {stats['lungime']} caractere")
    
    return stats