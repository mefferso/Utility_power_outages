"use strict";
const $ = id => document.getElementById(id);
const state = {manifest:null, snapshots:[], filtered:[]};
const fields = ["observed_at","source_as_of","county","state","utility","customers_out","cause","crew_status","started_at","lat","lon","source_url"];
function textCell(row, value) {const td=document.createElement("td"); td.textContent=value==null?"—":String(value);row.appendChild(td);}
function csvCell(value) {return '"' + String(value??"").replaceAll('"','""') + '"';}
function options(id, values) {
  const target=$(id), selected=target.value;
  target.replaceChildren(new Option(id==="county"?"All available":id==="utility"?"All utilities":"All causes",""));
  values.sort((a,b)=>a.localeCompare(b)).forEach(value=>target.add(new Option(value,value)));
  if(values.includes(selected))target.value=selected;
}
function filter() {
 const from=$("from").value,to=$("to").value,county=$("county").value,utility=$("utility").value,cause=$("cause").value;
 const query=$("query").value.trim().toLowerCase(),min=$("min").value===""?null:Number($("min").value);
 state.filtered=state.snapshots.filter(r=>{
  const date=r.observed_at?.slice(0,10)||"";
  if((from&&date<from)||(to&&date>to))return false;
  if(county&&r.fips!==county)return false;
  if(utility&&r.utility!==utility)return false;
  if(cause&&r.cause!==cause)return false;
  if(min!==null&&(!Number.isFinite(Number(r.customers_out))||Number(r.customers_out)<min))return false;
  if($("mode").value==="weather"&&!/tree|vegetation|wind|storm|weather|lightning|branch|limb/i.test(r.cause||""))return false;
  return !query||[r.county,r.state,r.utility,r.cause,r.crew_status,r.started_at].some(v=>String(v??"").toLowerCase().includes(query));
 });
 render();
}
function render() {
 $("count").textContent=state.filtered.length.toLocaleString();
 $("pairs").textContent=new Set(state.filtered.map(r=>r.fips+"|"+r.utility)).size.toLocaleString();
 const tbody=$("rows");tbody.replaceChildren();
 // Avoid locking the browser when large archives match: full results remain in CSV.
 for(const r of state.filtered.slice(0,1500)){
  const tr=document.createElement("tr");
  [r.observed_at,r.source_as_of,r.county+", "+r.state,r.utility,r.customers_out,r.cause,r.crew_status,r.started_at].forEach(v=>textCell(tr,v));
  const pos=document.createElement("td");
  if(Number.isFinite(Number(r.lat))&&Number.isFinite(Number(r.lon))&&r.lat!==null&&r.lon!==null){
   const a=document.createElement("a");a.href="https://www.openstreetmap.org/?mlat="+encodeURIComponent(r.lat)+"&mlon="+encodeURIComponent(r.lon)+"#map=12/"+encodeURIComponent(r.lat)+"/"+encodeURIComponent(r.lon);
   a.target="_blank";a.rel="noopener noreferrer";a.textContent=Number(r.lat).toFixed(3)+", "+Number(r.lon).toFixed(3);pos.appendChild(a);
  }else pos.textContent="—";tr.appendChild(pos);
  const source=document.createElement("td");const a=document.createElement("a");a.href=r.source_url;a.textContent="API";a.target="_blank";a.rel="noopener noreferrer";source.appendChild(a);tr.appendChild(source);
  tbody.appendChild(tr);
 }
 $("status").textContent=state.filtered.length>1500?"Showing first 1,500 of "+state.filtered.length.toLocaleString()+" matches; CSV includes all.":state.filtered.length+" matching observations.";
}
function exportCSV() {
 const lines=[fields.map(csvCell).join(","),...state.filtered.map(r=>fields.map(f=>csvCell(r[f])).join(","))];
 const url=URL.createObjectURL(new Blob([lines.join("\r\n")],{type:"text/csv;charset=utf-8"}));
 const a=document.createElement("a");a.href=url;a.download="utility-outages-"+new Date().toISOString().slice(0,10)+".csv";document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
}
async function load() {
 try {
 const response=await fetch("data/manifest.json",{cache:"no-store"});if(!response.ok)throw Error("Manifest HTTP "+response.status);
 state.manifest=await response.json();
 const months=state.manifest.months||[];$("months").textContent=months.length;
 $("status").textContent="Loading "+months.length+" archived month(s)…";
 // Load months individually; failed months show an explicit partial-data warning.
 let failed=[];
 for(const month of months){
  try {
   const res=await fetch("data/"+month+".json");if(!res.ok)throw Error("HTTP "+res.status);
   const body=await res.json();for(const snapshot of body.snapshots||[])state.snapshots.push(...(snapshot.incidents||[]));
  }catch(e){failed.push(month+": "+e.message);}
 }
 const distinct=(field)=>[...new Set(state.snapshots.map(r=>r[field]).filter(v=>v!=null&&v!==""))];
 const counties=[...new Map(state.snapshots.map(r=>[r.fips,[r.fips,r.county+", "+r.state]])).values()].sort((a,b)=>a[1].localeCompare(b[1]));
 for(const [fips,label] of counties)$("county").add(new Option(label,fips));
 options("utility",distinct("utility"));options("cause",distinct("cause"));
 filter();
 if(failed.length)$("status").textContent+=" WARNING: Unavailable archives: "+failed.join(", ");
 if(months.length===0)$("status").textContent="No archive yet. Enable the scheduled collector and run it once to begin.";
 }catch(error){$("status").textContent="Archive unavailable: "+error.message;}
}
$("search").addEventListener("click",filter);
$("export").addEventListener("click",exportCSV);
load();
