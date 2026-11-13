import {data} from "../../lib/scoring";
export default function Calendar(){
 const completedRounds=new Set(data.results.map(result=>result.round));
 return <><div className="eyebrow">Season schedule</div><h1>Race calendar</h1><p>All event times are listed in Central Time. Rounds with recorded results are marked completed.</p>
 <div className="events">{data.rounds.map(r=>{
  const completed=completedRounds.has(r.round);
  return <div className="event" key={r.round}><div><span className="tag">ROUND {r.round}</span>{" "}<span className={completed?"race-status race-status-completed":"race-status"}>{completed?"✓ Completed":"Scheduled"}</span><h2 style={{margin:"12px 0 6px"}}>{r.event}</h2><strong>{r.track} · {r.class}</strong><small>{r.format} · {r.notes}</small></div><div className="date">{r.date}<div className="muted">{r.time}</div></div></div>;
 })}</div></>;
}
