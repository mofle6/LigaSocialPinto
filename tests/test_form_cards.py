from copy import deepcopy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_site import add_rest_form, env, team_history


class FormTests(unittest.TestCase):
    def rounds(self):
        result = {}
        for n, (a,b,state) in enumerate([(2,0,'jugado'),(0,1,'jugado'),(1,1,'jugado'),(None,None,'suspendido'),(None,None,'aplazado'),(None,None,'sin_resultado')], 1):
            result[n] = {'jornada': n, 'fecha': '2026-11-09', 'descansa_id': None,
                'clasificacion': [{'equipo_id':'home','ultimos':[]},{'equipo_id':'away','ultimos':[]}],
                'partidos':[{'local_id':'home','visitante_id':'away','local':'Home','visitante':'Away','local_corto':'Home','visitante_corto':'Away','goles_local':a,'goles_visitante':b,'estado':state}]}
        return result

    def test_five_entries_include_all_pending_states(self):
        rounds = self.rounds()
        add_rest_form(rounds)
        self.assertEqual(rounds[6]['clasificacion'][0]['ultimos'], ['?', 'A', 'S', 'E', 'P'])
        self.assertEqual(rounds[6]['clasificacion'][1]['ultimos'], ['?', 'A', 'S', 'E', 'G'])
        self.assertEqual(rounds[3]['clasificacion'][0]['ultimos'], ['E','P','G'])
        self.assertTrue(all(len(r['ultimos']) <= 5 for j in rounds.values() for r in j['clasificacion']))

    def test_rest_uses_a_slot_and_resolved_score_replaces_pending(self):
        rounds = self.rounds()
        rounds[5]['descansa_id'] = 'home'
        rounds[5]['partidos'] = []
        add_rest_form(rounds)
        self.assertEqual(rounds[6]['clasificacion'][0]['ultimos'], ['?', 'D', 'S', 'E', 'P'])
        rounds[6]['partidos'][0].update(goles_local=2,goles_visitante=1,estado='jugado')
        add_rest_form(rounds)
        self.assertEqual(rounds[6]['clasificacion'][0]['ultimos'], ['G','D','S','E','P'])

    def test_full_history_remains_and_unplayed_is_not_last_played(self):
        rounds = self.rounds()
        add_rest_form(rounds)
        hist = team_history(rounds, 'home')
        self.assertEqual(len(hist), 6)
        self.assertEqual([h['n'] for h in hist if h['res']], [1,2,3])
        page = env.get_template('equipo.html').render(nombre='Home', div={'nombre':'Liga'}, row=None, hist=hist, upcoming=None, extra={}, root='')
        for label in ('Aplazado','Suspendido','Pendiente de resultado'):
            self.assertIn(f'aria-label="{label}"', page)
        self.assertIn('chip A', page)
        self.assertIn('chip S', page)
        self.assertIn('chip pending', page)
        self.assertNotIn('al  ·', page)

    def test_chip_labels_and_css_do_not_rely_only_on_color(self):
        module = env.get_template('_macros.html').module
        rendered = str(module.chips(['G','E','P','D','A','S','?']))
        self.assertEqual(rendered.count('aria-label='), 7)
        self.assertIn('title="Suspendido"', rendered)
        css = env.get_template('base.html').render()
        self.assertIn('.chip.A,.chip.S,.chip.pending{background:#1d4ed8;color:#fff}', css)


if __name__ == '__main__':
    unittest.main()
