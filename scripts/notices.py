"""Operational notices and schedule holds, separate from official results."""
import json

def load_notices(root):
    path=root/'data/avisos.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def active_notices(config, season=None, division=None):
    return [n for n in config.get('avisos',[]) if n.get('activo')
            and (season is None or n['temporada']==season)
            and (division is None or division in n['divisiones'])]

def apply_schedule_hold(schedule, config):
    for hold in config.get('suspensiones',[]):
        if (schedule.get('temporada'),schedule.get('division')) != (hold['temporada'],hold['division']):
            continue
        dates={p['fecha'] for p in schedule['partidos']}
        # A newly issued schedule on different dates lifts this display hold.
        if dates.intersection(hold['fechas']):
            return {**schedule,'suspendida':True}
    return schedule
