import {latLngToCell, cellToBoundary, cellArea} from "https://esm.sh/h3-js@4.5.0";

const meta={
  "Rhodiola rosea":{region:"Alpine and subalpine habitats",compound:"Salidroside and rosavins"},
  "Withania somnifera":{region:"Dry and semi-arid habitats",compound:"Withanolides"},
  "Nardostachys jatamansi":{region:"Himalayan alpine habitats",compound:"Jatamansone and related sesquiterpenes"},
  "Hydrastis canadensis":{region:"Eastern North American forests",compound:"Berberine"},
};
const parts={
  "Root / rhizome":{factor:5,rate:.055,label:"Very high assumed impact",copy:"Removing underground organs can kill the individual or delay recovery."},
  "Bark":{factor:3,rate:.065,label:"High assumed impact",copy:"Bark removal can injure or girdle woody plants. Species and technique matter."},
  "Flower / fruit":{factor:1.7,rate:.09,label:"Moderate assumed impact",copy:"Removing reproductive parts can reduce seed production and future recruitment."},
  "Leaf":{factor:1,rate:.13,label:"Lower assumed impact",copy:"Leaf removal can be less damaging, though repeated defoliation still affects plant health."},
};
const $=id=>document.getElementById(id);
const state={map:null,layer:null,demo:[],cache:new Map(),features:[],summary:null};

function parseCSV(text){
  const [head,...lines]=text.trim().split(/\r?\n/);const keys=head.split(",");
  return lines.map(line=>{const cols=line.split(",");return Object.fromEntries(keys.map((k,i)=>[k,cols[i]]));});
}
function escapeHTML(value){return String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function demoAggregate(species,resolution){
  const selected=state.demo.filter(r=>r.species===species);const groups=new Map();
  for(const record of selected){
    const cell=latLngToCell(Number(record.lat),Number(record.lon),resolution);
    if(!groups.has(cell))groups.set(cell,{cell,count:0,years:[],uncertainty:0});
    const g=groups.get(cell);g.count++;
    if(record.year)g.years.push(Number(record.year));
    if(record.coordinateUncertaintyInMeters)g.uncertainty++;
  }
  const features=[...groups.values()].map(g=>{
    const ring=cellToBoundary(g.cell).map(([lat,lon])=>[lon,lat]);ring.push(ring[0]);
    return {type:"Feature",geometry:{type:"Polygon",coordinates:[ring]},properties:{h3_cell:g.cell,record_count:g.count,year_min:g.years.length?Math.min(...g.years):null,year_max:g.years.length?Math.max(...g.years):null,uncertainty_metadata_count:g.uncertainty,cell_area_km2:Number(cellArea(g.cell,"km2").toFixed(2))}};
  });
  const count=selected.length,uncertainty=selected.filter(r=>r.coordinateUncertaintyInMeters).length;
  return {features,summary:{species,source:"Synthetic demo fixture",record_count:count,cell_count:features.length,resolution,uncertainty_metadata_share:count?uncertainty/count:null}};
}
async function loadData(){
  const species=$("species").value,resolution=Number($("resolution").value),limit=Number($("limit").value),live=$("source").value==="live";
  $("resolution-value").textContent=`H3 resolution ${resolution}`;$("summary-resolution").textContent=resolution;
  $("limit-value").textContent=limit;$("limit").disabled=!live;
  setStatus(live?"Fetching from GBIF…":"Synthetic records loaded",live);
  try{
    let result;
    if(live){
      const cacheKey=`${species}|${resolution}|${limit}`;
      if(state.cache.has(cacheKey))result=state.cache.get(cacheKey);
      else{
        const query=new URLSearchParams({species,resolution:String(resolution),limit:String(limit)});
        const response=await fetch(`/api/occurrences?${query}`,{cache:"no-store"});
        const payload=await response.json();if(!response.ok)throw new Error(payload.error||`Request failed (${response.status})`);
        result={features:payload.features,summary:payload.summary};state.cache.set(cacheKey,result);
      }
    }else result=demoAggregate(species,resolution);
    state.features=result.features;state.summary=result.summary;renderSummary(species,result.features,result.summary,live);
    const notice=$("notice");notice.className="notice hidden";notice.textContent="";
    setStatus(live?"Live GBIF data aggregated":"Synthetic records loaded",live);
  }catch(error){
    $("notice").className="notice error";$("notice").textContent=live?`${error.message} The synthetic demo remains available from the sidebar.`:`Could not load the demo fixture: ${error.message}`;
    setStatus("Data unavailable",false);
  }
}
function setStatus(text,live){$("status-text").textContent=text;$("source-pill").textContent=live?"LIVE GBIF":"DEMO DATA";}
function renderSummary(species,features,summary,live){
  const count=summary.record_count||0,cellCount=features.length;
  $("record-count").textContent=count.toLocaleString();$("source-label").textContent=summary.source;
  $("cell-count").textContent=cellCount.toLocaleString();
  const area=features.reduce((sum,f)=>sum+(f.properties.cell_area_km2||0),0);
  $("cell-foot").textContent=`Resolution ${summary.resolution} · ~${Math.round(area).toLocaleString()} km² of cell area`;
  $("quality-value").textContent=summary.uncertainty_metadata_share==null?"—":`${Math.round(summary.uncertainty_metadata_share*100)}%`;
  $("species-title").textContent=species;$("species-region").textContent=meta[species].region;
  $("compound-name").textContent=meta[species].compound;
  $("year-range").textContent=yearRange(features);$("summary-resolution").textContent=summary.resolution;
  $("source-pill").textContent=live?"LIVE GBIF":"DEMO DATA";
  $("footer-source").textContent=live?"GBIF public occurrence search API · live records aggregated server-side":"Synthetic fixture bundled with this prototype";
  renderCells(features);renderMap(features);
}
function yearRange(features){
  const values=features.flatMap(f=>[f.properties.year_min,f.properties.year_max]).filter(Number.isFinite);
  return values.length?`${Math.min(...values)}–${Math.max(...values)}`:"Not recorded";
}
function renderCells(features){
  const sorted=[...features].sort((a,b)=>b.properties.record_count-a.properties.record_count).slice(0,6);
  $("top-cells").innerHTML=sorted.map(f=>`<li><b>${escapeHTML(f.properties.h3_cell)}</b><br>${f.properties.record_count} record${f.properties.record_count===1?"":"s"} · ${f.properties.year_min??"?"}–${f.properties.year_max??"?"}</li>`).join("")||"<li>No aggregate cells</li>";
}
function renderMap(features){
  if(!state.map){state.map=L.map("map",{scrollWheelZoom:false,zoomControl:true}).setView([35,10],2);L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',maxZoom:19,subdomains:"abcd"}).addTo(state.map);}
  if(state.layer)state.map.removeLayer(state.layer);
  const max=Math.max(1,...features.map(f=>f.properties.record_count));
  const layer=L.featureGroup();
  features.forEach(feature=>{
    const p=feature.properties,ratio=p.record_count/max;
    const fill=ratio>.75?"#23583e":ratio>.4?"#47805c":"#91b388";
    const boundary=feature.geometry.coordinates[0].map(([lon,lat])=>[lat,lon]);
    const polygon=L.polygon(boundary,{color:"#f8f8f1",weight:1.1,fillColor:fill,fillOpacity:.83});
    polygon.bindPopup(`<div class="hex-popup"><b>${escapeHTML(p.h3_cell)}</b><br>${p.record_count} occurrence record${p.record_count===1?"":"s"}<br>Years ${p.year_min??"not recorded"}–${p.year_max??"not recorded"}</div>`);
    polygon.addTo(layer);
  });
  layer.addTo(state.map);state.layer=layer;
  if(features.length)state.map.fitBounds(layer.getBounds().pad(.12),{maxZoom:5});else state.map.setView([35,10],2);
  setTimeout(()=>state.map.invalidateSize(),80);
}
function drawScenario(){
  const part=$("part").value,pressure=Number($("pressure").value),rain=Number($("rainfall").value),info=parts[part];
  $("pressure-value").textContent=`${pressure}%`;$("rainfall-value").textContent=rain===0?"Baseline":`${rain>0?"+":""}${rain}%`;
  $("part-impact").textContent=info.label;$("part-copy").textContent=info.copy;
  const net=Math.max(-.25,Math.min(.20,info.rate*(1+rain/100)-pressure/100*info.factor));
  const values=Array.from({length:11},(_,year)=>100*Math.pow(1+net,year));
  const W=720,H=300,Lm=48,Rm=14,Tm=16,Bm=34,plotW=W-Lm-Rm,plotH=H-Tm-Bm;
  const min=Math.min(0,...values),max=Math.max(100,...values),span=Math.max(1,max-min);
  const x=i=>Lm+(i/10)*plotW,y=v=>Tm+((max-v)/span)*plotH;
  const points=values.map((v,i)=>`${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const yTicks=Array.from({length:4},(_,i)=>min+span*i/3);
  const grid=yTicks.map(v=>`<line x1="${Lm}" y1="${y(v)}" x2="${W-Rm}" y2="${y(v)}" stroke="#e5eae2"/><text x="${Lm-9}" y="${y(v)+3}" text-anchor="end" fill="#829087" font-size="9">${Math.round(v)}</text>`).join("");
  const xTicks=[0,2,4,6,8,10].map(i=>`<text x="${x(i)}" y="${H-8}" text-anchor="middle" fill="#829087" font-size="9">${i}</text>`).join("");
  $("recovery-chart").innerHTML=`${grid}${xTicks}<polyline points="${points}" fill="none" stroke="#3e7252" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>${values.map((v,i)=>`<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="#3e7252"/>`).join("")}<text x="${W-Rm}" y="${Math.max(13,y(values[10])-9)}" text-anchor="end" fill="#183a2f" font-size="10" font-weight="700">${values[10].toFixed(0)}</text>`;
  $("scenario-caption").textContent=`Illustrative only · assumed annual net change ${net>=0?"+":""}${(net*100).toFixed(1)}% · no species-specific demographic data`;
}
function attach(){
  ["species","source","resolution","limit"].forEach(id=>$(id).addEventListener("change",loadData));
  ["part","pressure","rainfall"].forEach(id=>$(id).addEventListener("input",drawScenario));
  document.querySelectorAll(".tab").forEach(button=>button.addEventListener("click",()=>{
    document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t===button));
    document.querySelectorAll(".tab-panel").forEach(panel=>{const active=panel.id===`panel-${button.dataset.tab}`;panel.hidden=!active;panel.classList.toggle("active",active);});
    if(button.dataset.tab==="harvest")drawScenario();
  }));
}
async function boot(){
  attach();drawScenario();
  try{const response=await fetch("/occurrences-demo.csv");if(!response.ok)throw new Error("Demo records unavailable");state.demo=parseCSV(await response.text());await loadData();}
  catch(error){$("notice").className="notice error";$("notice").textContent=error.message;setStatus("Demo data unavailable",false);}
}
boot();

