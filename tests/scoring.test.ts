import test from "node:test";
import assert from "node:assert/strict";
import { score, standings, rules, data, type Result } from "../lib/scoring";

const make=(overrides:Partial<Result>={}):Result=>({driver:"Dom",round:1,qualifying:null,race1:null,race2:null,bonuses:{},...overrides});
test("five active drivers and Ovi excluded",()=>{assert.equal(data.drivers.length,5);assert.ok(!data.drivers.includes("Ovi"));assert.ok(!data.results.some(r=>r.driver==="Ovi"));});
test("qualifying and race position point tables",()=>{for(let i=1;i<=6;i++){assert.equal(score(make({race1:i})).race,rules.racePoints[i-1]);}for(let i=1;i<=3;i++){assert.equal(score(make({qualifying:i})).qual,rules.qualPoints[i-1]);}assert.equal(score(make({qualifying:4,race1:7})).total,0);});
test("empty result scores zero",()=>assert.equal(score(make({})).total,0));
test("five AI replaces three AI, not stacked",()=>assert.equal(score(make({bonuses:{ahead3AI:true,ahead5AI:true}})).bonus,2));
test("bonus cap applies to normal rounds",()=>{const b={beatAverage:true,beatHigher:true,ahead5AI:true,fastestLap:true,mostGained:true,cleanRace:true,beatLeader:true};const scored=score(make({bonuses:b}));assert.equal(scored.bonusRaw,16);assert.equal(scored.bonus,10);});
test("finale multiplier affects only race points; finale bonus uncapped",()=>{const b={beatAverage:true,beatHigher:true,ahead5AI:true,fastestLap:true,mostGained:true,cleanRace:true,beatLeader:true};const scored=score(make({round:10,qualifying:1,race1:1,race2:2,bonuses:b}));assert.equal(scored.qual,3);assert.equal(scored.race,70.5);assert.equal(scored.bonus,16);assert.equal(scored.total,89.5);});
test("best eight of ten round totals count",()=>{const results=Array.from({length:10},(_,i)=>make({round:i+1,qualifying:null,race1:i<2?6:1}));const dom=standings(results).find(d=>d.driver==="Dom");assert.equal(dom?.points,7*25+37.5);});
test("snapshot totals match workbook",()=>{const table=standings();assert.deepEqual(table.map(d=>[d.driver,d.points]),[["Marcin",82],["Dom",75],["Michal",59],["Craig",44],["Kyle",26]]);});
