"""Importación aislada de horarios de Copa. Nunca escribe datos de Liga."""
import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
ROUNDS = {'RONDAPREVIA': 0, 'DIECISEISAVOS': 1, 'OCTAVOS': 2, 'CUARTOS': 3, 'SEMIFINALES': 4, 'FINAL': 5}
NAME = re.compile(r'HORARIOS_COPAF7_('+'|'.join(ROUNDS)+r')_(\d{8})(?:_v(\d{2}))?\.pdf$')

def normalize(s):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD',s.upper()) if not unicodedata.combining(c)).split())

def parse_pdf(path, data, stage):
    known={normalize(t['nombre']):t['nombre'] for t in data['equipos']}
    matches=[]
    with pdfplumber.open(path) as pdf:
        full='\n'.join(p.extract_text() or '' for p in pdf.pages)
        if data['temporada'] not in full or 'COPA' not in full or 'F7' not in full:
            raise ValueError('Competición o temporada incorrecta')
        if normalize(data['rondas'][stage]['nombre']) not in normalize(full):
            raise ValueError('La ronda del documento no coincide con el nombre del archivo')
        for page in pdf.pages:
            words=page.extract_words()
            for date in [w for w in words if re.fullmatch(r'\d{2}-\d{2}-\d{4}',w['text'])]:
                y=date['top']; block=[w for w in words if y-12<=w['top']<=y+30]
                left=' '.join(w['text'] for w in block if w['x0']<page.width*.44 and w['top']<y+9)
                right=' '.join(w['text'] for w in block if w['x0']>page.width*.56 and w['top']<y+9)
                home=known.get(normalize(left));away=known.get(normalize(right))
                if not home or not away or home==away:raise ValueError(f'Equipo no reconocido: {left} / {right}')
                times=[w['text'] for w in block if re.fullmatch(r'\d{2}:\d{2}',w['text'])]
                field=' '.join(w['text'] for w in block if w['top']>y+17)
                if len(times)!=1 or not field.startswith('Campo:'):raise ValueError('Hora o campo incompletos')
                datetime.strptime(times[0],'%H:%M')
                matches.append(dict(local=home,visitante=away,fecha=datetime.strptime(date['text'],'%d-%m-%Y').date().isoformat(),hora=times[0],campo=field.removeprefix('Campo:').strip()))
    if not matches:raise ValueError('PDF vacío o formato no reconocido')
    teams=[m[k] for m in matches for k in ('local','visitante')]
    if len(set(teams))!=len(teams):raise ValueError('Un equipo aparece dos veces en la ronda')
    expected=data['rondas'][stage].get('numero_partidos')
    if stage==0:expected=len([m for m in data['rondas'][0]['partidos'] if m.get('local') and m.get('visitante')])
    if expected and len(matches)!=expected:raise ValueError(f'PDF incompleto: {len(matches)} de {expected} partidos')
    return matches

def build(folder, base):
    result=copy.deepcopy(base); groups={};manifest=[]
    for path in sorted(folder.rglob('*.pdf')):
        m=NAME.fullmatch(path.name)
        if not m:raise ValueError(f'Nombre inválido: {path.name}')
        rnd,stamp,version=m.groups();datetime.strptime(stamp,'%Y%m%d')
        groups.setdefault(ROUNDS[rnd],[]).append(((stamp,int(version or 1)),path))
    for stage,versions in groups.items():
        versions.sort(key=lambda x:x[0]); latest=versions[-1][0]
        previous=NAME.fullmatch(result['rondas'][stage].get('fuente_horarios',''))
        if previous and latest<(previous[2],int(previous[3] or 1)):
            raise ValueError('Se rechaza volver a una versión de horarios anterior')
        candidates=[p for v,p in versions if v==latest]
        hashes={hashlib.sha256(p.read_bytes()).hexdigest() for p in candidates}
        if len(hashes)!=1:raise ValueError('Versiones con misma fecha y revisión pero distinto contenido')
        stored_hash=result['rondas'][stage].get('horarios_sha256')
        if previous and latest==(previous[2],int(previous[3] or 1)) and stored_hash and stored_hash not in hashes:
            raise ValueError('El contenido de una revisión ya importada ha cambiado: sube una revisión nueva')
        path=candidates[0];parsed=parse_pdf(path,result,stage)
        rnd=result['rondas'][stage];old=rnd.get('partidos',[])
        old_by_pair={(m.get('local'),m.get('visitante')):m for m in old if m.get('local') and m.get('visitante')}
        if old_by_pair and set(old_by_pair)!={(m['local'],m['visitante']) for m in parsed}:
            raise ValueError('Los cruces han cambiado: se requiere revisión antes de sustituirlos')
        updated=[]
        for i,m in enumerate(parsed):
            entry=copy.deepcopy(old_by_pair.get((m['local'],m['visitante']),{}))
            entry.setdefault('id',f'{rnd["id"]}-{i+1:02}')
            entry.update(m);entry.setdefault('estado','programado')
            entry.setdefault('goles_local',None);entry.setdefault('goles_visitante',None)
            updated.append(entry)
        # Preserve unknown bracket slots without inventing teams or results.
        rnd['partidos']=updated+[m for m in old if not m.get('local') or not m.get('visitante')]
        rnd['fuente_horarios']=path.name
        rnd['horarios_sha256']=next(iter(hashes))
        manifest.append({'ronda':rnd['id'],'archivo':path.name,'sha256':next(iter(hashes)),'partidos':len(parsed)})
    return result,manifest

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    opts=parser.parse_args()
    staged=[]
    for target in sorted((ROOT/'data/copa').glob('*/competicion.json')):
        base=json.loads(target.read_text(encoding='utf-8'))
        folder=ROOT/'pdfs-copa'/target.parent.name/'horarios'
        data,manifest=build(folder,base)
        staged.append((target,data,manifest))
    # Validate every season before replacing any Copa data.
    if not opts.check:
        for target,data,manifest in staged:
            temp=target.with_suffix('.tmp')
            temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            temp.replace(target)
    print('Copa validada:',sum(len(m) for _,_,m in staged),'rondas; datos de Liga intactos.')

if __name__=='__main__': main()
