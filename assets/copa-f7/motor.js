(function(root){
'use strict';
class CupEngine {
 constructor(data,seed=2026){this.data=data;this.seed=seed;this.teams=data.equipos;this.byName=Object.fromEntries(this.teams.map(t=>[t.nombre,t.id]));this.matches=[];this.randomState=seed>>>0;this.build();this.initialRandomState=this.randomState;}
 random(){this.randomState=(Math.imul(this.randomState,1664525)+1013904223)>>>0;return this.randomState/4294967296;}
 shuffle(values){const a=[...values];for(let i=a.length-1;i>0;i--){const j=Math.floor(this.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
 build(){
  const known=this.data.rondas[0].partidos.filter(m=>m.local&&m.visitante),used=new Set();
  known.forEach((m,i)=>{used.add(this.byName[m.local]);used.add(this.byName[m.visitante]);this.matches.push({id:'P'+(i+1),stage:0,home:{team:this.byName[m.local]},away:{team:this.byName[m.visitante]},score:null});});
  this.byes=this.teams.filter(t=>!used.has(t.id)).map(t=>t.id);
  let slots=this.shuffle([...this.matches.map(m=>({winner:m.id})),...this.byes.map(id=>({team:id}))]);
  if(slots.length!==32)throw Error('El cuadro de prueba requiere 32 plazas tras la previa');
  for(let stage=1;stage<6;stage++){
   const next=[];for(let i=0;i<slots.length;i+=2){const id='R'+stage+'-'+(i/2+1);this.matches.push({id,stage,home:slots[i],away:slots[i+1],score:null});next.push({winner:id});}slots=next;
  }
 }
 get(id){return this.matches.find(m=>m.id===id);}
 resolve(ref){return ref.team||this.winner(this.get(ref.winner));}
 winner(m){if(!m||!m.score)return null;const {h,a,ph,pa}=m.score;if(h===a)return ph>pa?this.resolve(m.home):this.resolve(m.away);return h>a?this.resolve(m.home):this.resolve(m.away);}
 participants(m){return [this.resolve(m.home),this.resolve(m.away)];}
 setScore(id,h,a,ph=null,pa=null){const m=this.get(id);if(!m)throw Error('Partido inexistente');const [home,away]=this.participants(m);if(!home||!away)throw Error('Faltan ganadores de la ronda anterior');
  if(![h,a].every(v=>Number.isInteger(v)&&v>=0&&v<=99))throw Error('Introduce marcadores enteros entre 0 y 99');
  if(h===a&&(![ph,pa].every(v=>Number.isInteger(v)&&v>=0&&v<=99)||ph===pa))throw Error('El empate necesita una tanda de penaltis con ganador');
  const before=new Map(this.matches.map(x=>[x.id,this.participants(x).join('|')]));
  m.score={h,a,ph:h===a?ph:null,pa:h===a?pa:null};
  for(const x of this.matches){if(x.id!==id&&before.get(x.id)!==this.participants(x).join('|'))x.score=null;}
 }
 simulate(stage=null){let count=0;for(const m of this.matches){if(m.score||(stage!==null&&m.stage!==stage))continue;if(this.participants(m).some(x=>!x))continue;const h=Math.floor(this.random()*6),a=Math.floor(this.random()*6);this.setScore(m.id,h,a,h===a?5:null,h===a?3:null);count++;}return count;}
 clear(){for(const m of this.matches)m.score=null;this.randomState=this.initialRandomState;}
 stats(id){const history=[];let played=0,wins=0,draws=0,losses=0,gf=0,ga=0,eliminated=false,stageReached=this.byes.includes(id)?1:0;
  for(const m of this.matches){const [h,a]=this.participants(m);if(h!==id&&a!==id)continue;stageReached=Math.max(stageReached,m.stage);if(!m.score)continue;const home=h===id,g=home?m.score.h:m.score.a,c=home?m.score.a:m.score.h;played++;gf+=g;ga+=c;if(g>c)wins++;else if(g<c)losses++;else draws++;const advanced=this.winner(m)===id;if(!advanced)eliminated=true;history.push({match:m.id,stage:m.stage,opponent:h===id?a:h,gf:g,ga:c,advanced,penalties:g===c,ph:home?m.score.ph:m.score.pa,pa:home?m.score.pa:m.score.ph});}
  const champion=this.winner(this.matches.at(-1))===id;return {played,wins,draws,losses,gf,ga,history,stageReached,eliminated,champion};
 }
 export(){return {version:1,seed:this.seed,randomState:this.randomState,scores:this.matches.filter(m=>m.score).map(m=>({id:m.id,...m.score}))};}
 static restore(data,state){if(state?.version!==1||!Number.isInteger(state.seed)||!Array.isArray(state.scores))throw Error('Simulación guardada no válida');const e=new CupEngine(data,state.seed);for(const m of e.matches){const s=state.scores.find(x=>x.id===m.id);if(s)e.setScore(m.id,s.h,s.a,s.ph,s.pa);}if(Number.isInteger(state.randomState))e.randomState=state.randomState>>>0;return e;}
}
root.CupEngine=CupEngine;if(typeof module!=='undefined')module.exports={CupEngine};
})(typeof window!=='undefined'?window:globalThis);
