import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import import_pdfs as imp
from parse_horarios import parse, parse_f7_field
from notices import active_notices, apply_schedule_hold, load_notices

ROOT=Path(__file__).resolve().parents[1]

class TemporaryFieldsTests(unittest.TestCase):
    def test_new_pdfs_dates_fields_and_all_teams(self):
        expected={'1dvf7':('2026-11-29',{('Príncipes De Asturias','C2'),('Príncipes De Asturias','C3')}),
                  '2dvf7':('2026-11-28',{('Estadio Rafael Mendoza','C1'),('Estadio Rafael Mendoza','C2')})}
        for division,(date,fields) in expected.items():
            data=parse(ROOT/f'pdfs/2026-2027/HORARIOS_{division.upper()}_J06_20261124.pdf')
            self.assertEqual(data['fecha'],date)
            self.assertEqual(len(data['partidos']),6)
            self.assertTrue(data['descansa'])
            self.assertEqual({(p['campo'],p['pista']) for p in data['partidos']},fields)
            standings=imp.read(sorted((ROOT/f'data/2026-2027/{division}').glob('j*.json'))[-1])
            aliases=imp.read(ROOT/'data/alias.json')
            for p in data['partidos']:
                for side in ('local','visitante'):p[side+'_id']=aliases.get(p[side],p[side+'_id'])
            data['descansa_id']=aliases.get(data['descansa'],data['descansa_id'])
            imp.check_teams(data,{r['equipo_id'] for r in standings['clasificacion']})

    def test_existing_fields_and_unconfigured_courts(self):
        self.assertEqual(parse_f7_field('Campo: CAMPO PATRICIA CHAMORRO F7 C1 - Hierba Artificial'),('Patricia Chamorro','C1'))
        for text in ('Campo: CAMPO PATRICIA CHAMORRO F7 C3 - Hierba Artificial',
                     'Campo: ESTADIO RAFAEL MENDOZA F7 C9 - Hierba Artificial',
                     'Campo: CAMPO DESCONOCIDO F7 C1 - Hierba Artificial'):
            with self.assertRaises(ValueError):parse_f7_field(text)

    def test_notices_limited_to_affected_leagues(self):
        config=load_notices(ROOT)
        self.assertEqual(len(active_notices(config)),1)
        for division in ('1dvf7','2dvf7','f11'):self.assertEqual(len(active_notices(config,'2026-2027',division)),1)
        for division in ('3dvf7','4dvf7','fs','copa-f7'):self.assertFalse(active_notices(config,'2026-2027',division))
        self.assertFalse(active_notices(config,'2027-2028','f11'))
        inactive=copy.deepcopy(config);inactive['avisos'][0]['activo']=False
        self.assertFalse(active_notices(inactive))

    def test_suspension_uses_dates_not_guessed_round_and_is_non_mutating(self):
        config=load_notices(ROOT)
        schedule={'temporada':'2026-2027','division':'f11','jornada':7,'partidos':[{'fecha':'2026-11-28'},{'fecha':'2026-11-29'}]}
        before=copy.deepcopy(schedule)
        self.assertTrue(apply_schedule_hold(schedule,config)['suspendida'])
        self.assertEqual(schedule,before)
        schedule['division']='1dvf7'
        self.assertNotIn('suspendida',apply_schedule_hold(schedule,config))
        schedule['division']='f11';schedule['partidos']=[{'fecha':'2026-12-05'}]
        self.assertNotIn('suspendida',apply_schedule_hold(schedule,config))
        schedule['partidos']=[{'fecha':'2026-11-21'}]
        self.assertNotIn('suspendida',apply_schedule_hold(schedule,config))
