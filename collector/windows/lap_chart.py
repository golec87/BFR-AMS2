"""Per-driver completed-lap timing and offline position/lap-time chart for BFR."""
import csv
import html
import json
from pathlib import Path


def lap_updates(snapshot, previous):
    """Return completed laps when mLapsCompleted advances exactly once."""
    result = []
    participants = snapshot.get("participants", {}).get("mParticipantInfo", [])
    for p in participants:
        if not isinstance(p, dict):
            continue
        tag = str(p.get("mName") or "").strip()
        if not tag or "safety car" in tag.lower() or "safetycar" in str(p.get("mCarClassNames") or "").lower():
            continue
        lap = p.get("mLapsCompleted")
        last = p.get("mLastLapTimes")
        if not isinstance(lap, int) or lap < 1:
            continue
        old = previous.get(tag.lower())
        # Only one completed lap since previous poll; no fabricated laps.
        if old is not None and lap == old + 1 and isinstance(last, (float, int)) and last > 0:
            result.append({"driver": tag, "lap": lap, "lap_time_seconds": round(last, 3),
                           "position_at_detection": p.get("mRacePosition"),
                           "source": "CREST2 mLastLapTimes"})
        previous[tag.lower()] = lap
    return result


def write_lap_outputs(folder, laps, positions):
    folder = Path(folder)
    with (folder / "lap_times.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["driver", "lap", "lap_time_seconds",
                                               "position_at_detection", "source"])
        writer.writeheader()
        writer.writerows(laps)
    # Offline interactive SVG chart. Uses only locally embedded data.
    dataset = json.dumps({"laps": laps, "positions": positions}, ensure_ascii=False).replace("<", "\\u003c")
    page = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>BFR Lap Times + Race Positions</title>
<style>body{font:15px system-ui;background:#111827;color:#f3f4f6;margin:24px}
select{background:#1f2937;color:white;padding:8px;border:1px solid #6b7280}
svg{width:100%;max-width:1100px;background:#1f2937;border-radius:12px}
p{color:#d1d5db} .legend{display:flex;gap:20px}</style>
<h2>BFR — Lap times overlaid with race position</h2>
<p>Choose a driver. Blue = lap time (left axis, seconds). Orange = race position (right axis, P1 at top).
Position points use the recorded lap number; changes within a lap may overlap. Provisional telemetry, not official timing.</p>
<label>Driver: <select id="driver"></select></label><p id="summary"></p>
<svg id="chart" viewBox="0 0 1050 490" role="img" aria-label="Lap times and positions chart"></svg>
<p>Missing laps are not interpolated. Lap time is read when a driver's completed-lap count increments.
The displayed position is observed at the sample, not necessarily at the exact finish line.</p>
<script>
const data = __DATA__;
const sel=document.getElementById('driver'), svg=document.getElementById('chart');
const drivers=[...new Set([...data.laps.map(x=>x.driver),...Object.keys(data.positions)])].sort();
for(const name of drivers){const opt=document.createElement('option');opt.value=name;opt.textContent=name;sel.append(opt)}
function draw(){
 const name=sel.value, laps=data.laps.filter(x=>x.driver===name).sort((a,b)=>a.lap-b.lap);
 const hist=(data.positions[name]||{}).changes||[];
 const pos=hist.filter(x=>Number.isFinite(Number(x.lap)) && Number.isFinite(Number(x.position)));
 const all=[...laps.map(x=>Number(x.lap)),...pos.map(x=>Number(x.lap))];
 const maxLap=Math.max(1,...all), minLap=0;
 const times=laps.map(x=>x.lap_time_seconds);
 const minT=Math.floor(Math.min(60,...times)-3),maxT=Math.ceil(Math.max(65,...times)+3);
 const maxP=Math.max(2,...pos.map(x=>x.position));
 const X=l=>75+900*(l-minLap)/(maxLap-minLap);
 const Yt=t=>420-350*(t-minT)/(maxT-minT);
 const Yp=p=>70+350*(p-1)/(maxP-1);
 const ns='http://www.w3.org/2000/svg';svg.replaceChildren();
 function el(tag,attrs,text){let e=document.createElementNS(ns,tag);for(let k in attrs)e.setAttribute(k,attrs[k]);if(text!==undefined)e.textContent=text;svg.append(e);return e}
 for(let i=0;i<=5;i++){let y=70+i*70;el('line',{x1:75,y1:y,x2:975,y2:y,stroke:'#374151'});el('text',{x:12,y:y+4,fill:'#93c5fd','font-size':13},(maxT-(maxT-minT)*i/5).toFixed(1)+'s');el('text',{x:990,y:y+4,fill:'#fdba74','font-size':13},'P'+(1+(maxP-1)*i/5).toFixed(0))}
 for(let l=0;l<=maxLap;l++){if(l>25&&l%Math.ceil(maxLap/20))continue;el('text',{x:X(l),y:448,fill:'#d1d5db','text-anchor':'middle','font-size':12},String(l))}
 function line(points,color,fn){if(!points.length)return;el('polyline',{points:points.map(p=>X(Number(p.lap))+','+fn(p)).join(' '),fill:'none',stroke:color,'stroke-width':3});for(let p of points){let c=el('circle',{cx:X(Number(p.lap)),cy:fn(p),r:4,fill:color});let t=document.createElementNS(ns,'title');t.textContent='Lap '+p.lap+': '+(color==='#60a5fa'?p.lap_time_seconds+'s':'P'+p.position);c.append(t)}}
 line(laps,'#60a5fa',p=>Yt(p.lap_time_seconds));line(pos,'#fb923c',p=>Yp(p.position));
 el('text',{x:450,y:478,fill:'white'},'Completed lap');
 document.getElementById('summary').textContent=laps.length+' measured laps • '+pos.length+' position observations';
}
sel.addEventListener('change',draw);if(drivers.length)draw();
</script></html>""".replace("__DATA__", dataset)
    (folder / "lap_position_chart.html").write_text(page, encoding="utf-8")
