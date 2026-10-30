import data from "../data/championship.json";
export type BonusKey = "beatAverage" | "beatHigher" | "ahead3AI" | "ahead5AI" | "fastestLap" | "mostGained" | "cleanRace" | "beatLeader";
export type Result = { driver:string; round:number; qualifying:number|null; race1:number|null; race2:number|null; bonuses:Partial<Record<BonusKey,boolean>> };
const racePoints=[25,22,20,18,16,14];
const qualPoints=[3,2,1];
export const rules={racePoints,qualPoints,bonusCap:10,countBest:8,finaleMultiplier:1.5};
export function score(result:Result) {
 const qual=result.qualifying == null ? 0 : (qualPoints[result.qualifying-1]??0);
 const raceBase=[result.race1,result.race2].reduce<number>((total,pos)=>total+(pos == null ? 0 : racePoints[pos-1]??0),0);
 const b=result.bonuses??{};
 const bonusRaw=(b.beatAverage?3:0)+(b.beatHigher?2:0)+(b.ahead5AI?2:b.ahead3AI?1:0)+(b.fastestLap?2:0)+(b.mostGained?2:0)+(b.cleanRace?2:0)+(b.beatLeader?3:0);
 const bonus=result.round===10?bonusRaw:Math.min(10,bonusRaw);
 const race=raceBase*(result.round===10?1.5:1);
 return {qual,race,bonus,bonusRaw,total:qual+race+bonus};
}
export function standings(results:Result[]=data.results as Result[]) {
 return data.drivers.map(driver=>{
  const entries=results.filter(r=>r.driver===driver);
  const scores=entries.map(r=>score(r).total);
  const points=[...scores].sort((a,b)=>b-a).slice(0,8).reduce((a,b)=>a+b,0);
  return {driver,points,rounds:entries.length,wins:entries.reduce((n,r)=>n+(r.race1===1?1:0)+(r.race2===1?1:0),0),poles:entries.filter(r=>r.qualifying===1).length,podiums:entries.reduce((n,r)=>n+([r.race1,r.race2].filter(p=>p!==null&&p<=3).length),0)};
 }).sort((a,b)=>b.points-a.points||b.wins-a.wins||a.driver.localeCompare(b.driver));
}
export {data};
