(function(){
'use strict';
const page=document.querySelector('.team-page[data-cup-team]');if(!page)return;
const team=window.COPA_DATA.equipos.find(t=>t.id===page.dataset.cupTeam);if(!team)return;
const nav=page.querySelector('.competition-switch'),content=document.createElement('div');content.id='competitionContent';content.setAttribute('role','tabpanel');
while(nav.nextSibling)content.appendChild(nav.nextSibling);page.appendChild(content);
nav.querySelectorAll('[data-competition]').forEach(b=>{b.id='tab-'+b.dataset.competition;b.setAttribute('aria-controls','competitionContent');});
const original=content.innerHTML,heroTemplate=content.querySelector('.team-hero').cloneNode(true),divisionText=heroTemplate.querySelector('.team-division').textContent;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=s=>s?s.split('-').reverse().join('/'):'Sin publicar';
const data=window.COPA_DATA,teamName=id=>data.equipos.find(t=>t.id===id)?.nombre||'Por determinar';
const stages=data.rondas.map(r=>r.nombre),stageDates=data.rondas.map(r=>r.fecha);
let simulation=new URL(location.href).searchParams.get('simulacion')==='1';
function loadEngine(){try{const saved=localStorage.getItem('pinto-copa-simulacion-v1');return saved?window.CupEngine.restore(data,JSON.parse(saved)):new window.CupEngine(data);}catch{return new window.CupEngine(data);}}
function chips(items){const labels={G:'Victoria',P:'Derrota',E:'Empate','?':'Programado'};return items.map(c=>`<span class="chip ${c==='?'?'pending':c}" title="${labels[c]}" aria-label="${labels[c]}">${c}</span>`).join('');}
function shortVenue(value){return String(value||'').replace(/^(?:CAMPO|ESTADIO)\s+/i,'').replace(/\s+F7\b/gi,'').replace(/\s*-\s*Hierba Artificial\s*$/i,'').trim();}
function fixture(label,match,empty){if(!match)return `<article class="fixture-card"><h2>${label}</h2><p class="fixture-empty">${empty}</p></article>`;
 return `<article class="fixture-card"><h2>${label}</h2><p class="fixture-league">Copa F7 · ${esc(match.stageName)}${simulation?' · Simulado':''}</p><div class="fixture-content"><div class="fixture-time"><span>${date(match.date)}</span>${match.time?`<span>${esc(match.time)}</span>`:''}</div><div class="fixture-teams"><div><span>${esc(match.home)}</span><strong>${match.h??''}</strong></div><div><span>${esc(match.away)}</span><strong>${match.a??''}</strong></div></div></div>${match.penalties?`<p class="fixture-venue">Penaltis ${match.fixturePh??match.ph}–${match.fixturePa??match.pa}</p>`:''}</article>`;
}
function stat(label,v){return `<div class="team-stat"><span>${esc(label)}</span><strong>${esc(v)}</strong></div>`;}
function cup(){const engine=loadEngine(),stats=simulation?engine.stats(team.id):{played:0,wins:0,draws:0,losses:0,gf:0,ga:0,history:[],stageReached:0};
 let next=null,history=[],previous=null;
 if(simulation){history=stats.history.map(h=>{const m=engine.get(h.match),[home,away]=engine.participants(m);return {...h,date:stageDates[h.stage],stageName:stages[h.stage],rival:teamName(h.opponent),home:teamName(home),away:teamName(away),h:m.score.h,a:m.score.a,fixturePh:m.score.ph,fixturePa:m.score.pa,isHome:home===team.id};});previous=history.at(-1)||null;
  const upcoming=engine.matches.find(m=>!m.score&&engine.participants(m).includes(team.id));if(upcoming){const [h,a]=engine.participants(upcoming);next={stageName:stages[upcoming.stage],date:stageDates[upcoming.stage],home:teamName(h),away:teamName(a)};}
 }else{const first=data.rondas[0].partidos.find(m=>m.local===team.nombre||m.visitante===team.nombre);if(first){next={stageName:'Ronda previa',date:first.fecha||stageDates[0],time:first.hora,field:first.campo,home:first.local,away:first.visitante};}}
 const hero=heroTemplate.cloneNode(true);hero.querySelector('.team-division').textContent='Copa F7 · '+(simulation?'Simulación local':'Calendario oficial');
 hero.querySelector('.team-form').innerHTML=history.length?chips([...history].reverse().slice(0,5).map(h=>h.gf>h.ga?'G':h.gf<h.ga?'P':'E')):'<span class="muted">Sin partidos de Copa disputados</span>';
 hero.querySelector('.team-form').setAttribute('aria-label','Últimos cinco resultados de Copa');
 hero.querySelector('.team-fixtures').innerHTML=fixture('Último partido',previous,'Todavía no hay resultados de Copa.')+fixture('Próximo partido',next,simulation?'Sin próximos encuentros en esta simulación.':'Cruce pendiente de asignación oficial.');
 const status=!simulation?'Pendiente':stats.champion?'Campeón':stats.eliminated?'Eliminado':'En competición';
 let rows=history.map(h=>`<tr><td>${esc(h.stageName)}</td><td>${date(h.date)}</td><td class="l">${esc(h.rival)}</td><td class="muted">${h.isHome?'L':'V'}</td><td>${chips([h.gf>h.ga?'G':h.gf<h.ga?'P':'E'])} <strong class="team-score">${h.gf}–${h.ga}</strong>${h.penalties?`<br><small>Penaltis ${h.ph}–${h.pa}</small>`:''}<br><small>${h.advanced?'Clasificado':'Eliminado'} · Simulado</small></td></tr>`).join('');
 if(!rows&&next)rows=`<tr><td>${esc(next.stageName)}</td><td>${date(next.date)}</td><td class="l">${esc(next.home===team.nombre?next.away:next.home)}</td><td class="muted">${next.home===team.nombre?'L':'V'}</td><td>${chips(['?'])} <span class="muted">Programado</span></td></tr>`;
 if(!rows)rows='<tr><td colspan="5" class="muted">No hay partidos de Copa asignados.</td></tr>';
 content.replaceChildren();
 const crumb=document.createElement('nav');crumb.className='breadcrumbs';crumb.setAttribute('aria-label','Ruta de navegación');crumb.innerHTML='<ol><li><a href="../../../index.html">Inicio</a></li><li><a href="../../../index.html#f7">Fútbol 7</a></li><li><a href="../../copa-f7/index.html">Copa F7</a></li><li><span aria-current="page">'+esc(team.nombre)+'</span></li></ol>';content.append(crumb,hero);
 content.insertAdjacentHTML('beforeend',`<section class="team-panel team-stats" aria-label="Estadísticas del equipo"><h2>Estadísticas</h2><div class="team-stat-grid">${stat('Ronda',!simulation&&!next?'Por confirmar':stages[stats.stageReached]||'Por confirmar')}${stat('Partidos',stats.played)}${stat('Goles a favor',stats.gf)}${stat('Goles en contra',stats.ga)}${stat('Estado',status)}${stat('Ganados',stats.wins)}${stat('Empatados',stats.draws)}${stat('Perdidos',stats.losses)}</div></section><section class="team-panel team-history"><h2>Partidos</h2><div class="scroll"><table><thead><tr><th>Ronda</th><th>Fecha</th><th class="l">Rival</th><th>Local/Visitante</th><th>Resultado</th></tr></thead><tbody>${rows}</tbody></table></div></section><section class="cup-view-options"><p><strong>${simulation?'Resultados de prueba · Sin validez oficial':'Copa oficial · Sin resultados publicados'}</strong></p><label><input id="showCupSimulation" type="checkbox" ${simulation?'checked':''}> Ver resultados de la simulación local</label><a href="../../copa-f7/index.html${simulation?'?simulacion=1':''}">Ver cuadro y simulador de Copa</a></section>`);
 content.querySelector('#showCupSimulation').onchange=e=>{simulation=e.target.checked;switchTo('copa',true);};
}
function switchTo(which,push){const cupView=which==='copa';content.classList.toggle('cup-data',cupView);content.setAttribute('aria-labelledby','tab-'+which);nav.querySelectorAll('[data-competition]').forEach(b=>{b.setAttribute('aria-selected',String(b.dataset.competition===which));b.setAttribute('tabindex',b.dataset.competition===which?'0':'-1');});if(cupView)cup();else content.innerHTML=original;
 if(push){const u=new URL(location.href);u.searchParams.set('competicion',which);if(cupView&&simulation)u.searchParams.set('simulacion','1');else u.searchParams.delete('simulacion');history.pushState(null,'',u);}}
nav.addEventListener('click',e=>{const b=e.target.closest('[data-competition]');if(b)switchTo(b.dataset.competition,true);});
nav.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const choice=e.key==='ArrowLeft'||e.key==='Home'?'liga':'copa';switchTo(choice,true);nav.querySelector(`[data-competition="${choice}"]`).focus();});
window.addEventListener('popstate',()=>{simulation=new URL(location.href).searchParams.get('simulacion')==='1';switchTo(new URL(location.href).searchParams.get('competicion')==='copa'?'copa':'liga',false);});
switchTo(new URL(location.href).searchParams.get('competicion')==='copa'?'copa':'liga',false);
})();
