/* GrooveScape original Jarreth-inspired generator. No third-party code copied.
 * Pitch-only mutation at 0..50; pitch + gate/rhythm mutation at 51..100.
 * Deterministic seed, independent gate and pitch state, 16 steps.
 */
(function(root){
'use strict';
const SCALES={minor:[0,2,3,5,7,8,10],major:[0,2,4,5,7,9,11],dorian:[0,2,3,5,7,9,10],pentatonic:[0,3,5,7,10]};
function randomFrom(seed){let state=(Number(seed)>>>0)||1;return()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;};}
function generate(opts={},previous=null){
 const steps=16,random=randomFrom(opts.seed||2026),scale=SCALES[opts.scale]||SCALES.minor;
 const mutation=Math.max(0,Math.min(100,Number(opts.mutation)||0));
 const pitchChance=mutation<=50?mutation/50:1;
 const rhythmChance=mutation<=50?0:(mutation-50)/50;
 const density=Math.max(0,Math.min(100,Number(opts.density??65)))/100;
 const variation=Math.max(0,Math.min(100,Number(opts.variation??35)))/100;
 const octaves=Math.max(1,Math.min(4,Number(opts.range)||2));
 const key=((Number(opts.key)||0)%12+12)%12;
 const base=Array.isArray(previous)&&previous.length===steps?previous:null;
 let degree=2;
 return Array.from({length:steps},(_,step)=>{
   const old=base?base[step]:null;
   const gate=base&&random()>=rhythmChance?(old!==null):random()<density;
   if(!gate)return null;
   if(base&&old!==null&&random()>=pitchChance)return old;
   const delta=random()<variation?Math.floor(random()*7)-3:Math.floor(random()*3)-1;
   degree=Math.max(0,Math.min(scale.length*octaves-1,degree+delta));
   return 60+key+scale[degree%scale.length]+12*Math.floor(degree/scale.length);
 });
}
const api={generate,SCALES};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.GrooveScapeJarreth=api;
})(typeof globalThis!=='undefined'?globalThis:this);
