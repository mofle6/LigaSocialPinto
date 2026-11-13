"""Apply the shared identity to freshly generated data; no preview snapshots."""
import copy, hashlib, html, json, os, re, shutil
from jinja2 import Environment, FileSystemLoader, select_autoescape

LABELS={'1dvf7':'Primera F7 · Oro','2dvf7':'Segunda F7 · Plata','3dvf7':'Tercera F7 · Bronce','4dvf7':'Cuarta F7 · Zinc','f11':'Primera F11','fs':'Fútbol Sala'}

def crumbs(home,code,label=None,team=False):
    sport='Fútbol Sala' if code=='fs' else 'Fútbol 11' if code=='f11' else 'Fútbol 7'
    anchor=code if code in ('fs','f11') else 'f7'
    items=[f'<a href="{home}">Inicio</a>',f'<a href="{home}#{anchor}">{sport}</a>']
    if label:items.extend([f'<a href="{"../" if team else ""}index.html">{LABELS[code]}</a>',f'<span aria-current="page">{html.escape(label)}</span>'])
    else:items.append(f'<span aria-current="page">{LABELS[code]}</span>')
    return '<nav class="breadcrumbs" aria-label="Ruta de navegación"><ol>'+''.join('<li>'+s+'</li>' for s in items)+'</ol></nav>'

def integrate(root,out,seasons,index,history_for,upcoming_for,prepare,aliases,display_names):
    cup_ids={}
    for source in sorted((root/'data/copa').glob('*/competicion.json')):
        season=source.parent.name;data=json.loads(source.read_text(encoding='utf-8'))
        for team in data['equipos']:
            found=[]
            for code,division in seasons.get(season,{}).items():
                if code in ('f11','fs'):continue
                rounds=division['jornadas'];last=rounds[max(rounds)]
                row=next((r for r in last['clasificacion'] if r['equipo']==team['nombre']),None)
                if row:
                    schedules=[prepare(json.loads(p.read_text(encoding='utf-8')),aliases,display_names) for p in (root/'data'/season/code/'proximas').glob('j*.json')]
                    future=[s for s in schedules if s['jornada']>last['jornada']]
                    upcoming=min(future,key=lambda s:s['jornada']) if future else None
                    team['league']={'division':code,'round':last['jornada'],'row':copy.deepcopy(row),'history':history_for(rounds,row['equipo_id']),'next':upcoming_for(upcoming,row['equipo_id'])}
                    cup_ids[(season,code,row['equipo_id'])]=team['id'];found.append(code)
            if len(found)!=1:raise ValueError(f'Equipo de Copa sin vínculo único a Liga: {team["nombre"]}')
        destination=out/season/'copa-f7';shutil.copytree(root/'assets/copa-f7',destination,dirs_exist_ok=True)
        (destination/'datos.js').write_text('window.COPA_DATA = '+json.dumps(data,ensure_ascii=False)+';\n',encoding='utf-8')
    for page in out.rglob('*.html'):
        parts=page.relative_to(out).parts
        if len(parts)<3 or parts[1] not in LABELS:continue
        season,code=parts[:2];text=page.read_text(encoding='utf-8');team='equipos' in parts
        home=os.path.relpath(out/'index.html',page.parent).replace('\\','/')
        title=re.search(r'<h1[^>]*>(.*?)</h1>',text,re.S)
        label=html.unescape(re.sub('<[^>]+>','',title[1])) if title else None
        breadcrumb=crumbs(home,code,label if page.name!='index.html' else None,team)
        text=re.sub(r'<p class="crumbs">.*?</p>',lambda _:breadcrumb,text,count=1,flags=re.S)
        tid=cup_ids.get((season,code,page.stem)) if team else None
        if tid:
            switch='<nav class="competition-switch" role="tablist" aria-label="Competición de la ficha"><button type="button" role="tab" data-competition="liga" aria-selected="true">Liga</button><button type="button" role="tab" data-competition="copa" aria-selected="false" tabindex="-1">Copa</button></nav>'
            text=text.replace('<div class="team-page">',f'<div class="team-page" data-cup-team="{tid}">'+switch,1)
            text=text.replace('</body>','<script src="../../copa-f7/datos.js"></script><script src="../../copa-f7/motor.js"></script><script src="../../../assets/ficha-equipo.js"></script></body>')
        version=hashlib.sha256((root/'assets/ficha-equipo.js').read_bytes()).hexdigest()[:12]
        text=text.replace('assets/ficha-equipo.js"',f'assets/ficha-equipo.js?v={version}"')
        page.write_text(text,encoding='utf-8')
    env=Environment(loader=FileSystemLoader(root/'templates'),autoescape=select_autoescape(['html']))
    env.filters['fecha']=lambda iso:'/'.join(reversed(iso.split('-'))) if iso else ''
    (out/'index.html').write_text(env.get_template('index.html').render(items=index,cup_seasons={k[0] for k in cup_ids},root='./'),encoding='utf-8')
