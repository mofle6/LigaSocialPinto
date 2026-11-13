'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {CupEngine}=require('../assets/copa-f7/motor.js');const context={window:{}};vm.runInNewContext(fs.readFileSync(__dirname+'/../site/2026-2027/copa-f7/datos.js','utf8'),context);const data=JSON.parse(JSON.stringify(context.window.COPA_DATA)),snapshot=JSON.stringify(data);
const e=new CupEngine(data,2026);assert.equal(e.matches.length,50);assert.equal(e.byes.length,13);assert.equal(e.matches.filter(m=>m.stage===0).length,19);
assert.throws(()=>e.setScore('R1-1',2,1),/Faltan/);
assert.throws(()=>e.setScore('P1',1,1),/penaltis/);assert.throws(()=>e.setScore('P1',-1,0),/enteros/);
e.setScore('P1',2,2,5,4);assert.equal(e.winner(e.get('P1')),e.resolve(e.get('P1').home));const t=e.resolve(e.get('P1').home),s=e.stats(t);assert.equal(s.draws,1);assert.equal(s.gf,2);assert.equal(s.ga,2);assert.equal(s.eliminated,false);
e.simulate();assert.equal(e.matches.filter(m=>m.score).length,50);assert.ok(e.winner(e.matches.at(-1)));assert.equal(e.teams.filter(t=>e.stats(t.id).champion).length,1);assert.equal(e.teams.filter(t=>e.stats(t.id).eliminated).length,50);
const saved=e.export(),restored=CupEngine.restore(data,saved);assert.equal(restored.winner(restored.matches.at(-1)),e.winner(e.matches.at(-1)));
const old=e.winner(e.get('P1'));e.setScore('P1',0,2);assert.notEqual(e.winner(e.get('P1')),old);assert.equal(e.winner(e.matches.at(-1)),null);assert.ok(e.matches.filter(m=>m.score).length<50);e.simulate();assert.ok(e.winner(e.matches.at(-1)));
assert.equal(JSON.stringify(data),snapshot,'No se deben alterar Liga o datos oficiales');e.clear();assert.equal(e.matches.filter(m=>m.score).length,0);assert.equal(JSON.stringify(data),snapshot);
for(let seed=1;seed<=30;seed++){const x=new CupEngine(data,seed);x.simulate();assert.equal(x.matches.filter(m=>m.score).length,50);assert.equal(x.teams.filter(t=>x.stats(t.id).champion).length,1);assert.equal(x.teams.reduce((n,t)=>n+x.stats(t.id).played,0),100);}
console.log('Pruebas correctas: cuadro de 51 equipos, 50 partidos, penaltis, correcciones en cascada, persistencia y aislamiento; 30 simulaciones completas.');
