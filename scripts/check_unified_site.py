"""Validate production routes, league tables and Copa separation after building."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parent.parent
SITE=ROOT/'site'
class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for key in ('href','src'):
            if a.get(key):self.links.append(a[key])

def main():
    pages={}
    for p in SITE.rglob('*.html'):
        text=p.read_text(encoding='utf-8');parser=Page();parser.feed(text);pages[p.resolve()]=parser
        for phrase in ('Vista de pruebas','Entorno de pruebas independiente','copia de consulta del','Laboratorio Pinto'):
            assert phrase not in text,(p,phrase)
        assert 'Web independiente, sin ánimo de lucro' in text,p
        if re.search(r'<th>#</th>',text):
            assert text.count('class="zone-promotion"')==3,p
            assert text.count('class="zone-relegation"')==3,p
    for p,parser in pages.items():
        for link in parser.links:
            url=urlsplit(link)
            if url.scheme or url.netloc:continue
            dest=(p.parent/unquote(url.path)).resolve() if url.path else p
            assert dest.is_relative_to(SITE.resolve()),(p,link)
            assert dest.exists(),(p,link)
            if url.fragment and dest in pages:assert unquote(url.fragment) in pages[dest].ids,(p,link)
    print(f'Producción: {len(pages)} páginas, rutas y avisos verificados.')

if __name__=='__main__':main()
