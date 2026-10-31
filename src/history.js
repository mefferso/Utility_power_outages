"use strict";
let historicalRows = [];
let historicalCoverage = [];
const historic = id => document.getElementById(id);
const histValue = v => v == null ? "—" : Number(v).toLocaleString();
async function loadHistorical() {
  const status=historic("history-status");
  try {
    const response=await fetch("data/history.json",{cache:"no-store"});
    if(!response.ok)throw Error("No historical summary file yet (run the history workflow)");
    const data=await response.json();
    if(!Array.isArray(data.records))throw Error("Historical file schema unrecognized");
    historicalRows=data.records; historicalCoverage=data.counties||[];
    const failed=historicalCoverage.filter(c=>c.status!=="ok").length;
    status.textContent="Source retrieved "+(data.generated_at||"unknown time")+"; "+historicalRows.length+" monthly county records; "+failed+" source failures. Missing records are not zeros.";
    renderHistorical();
  } catch(e) {status.textContent="Historical summaries not yet available: "+e.message;}
}
function renderHistorical(){
 const year=Number(historic("history-year").value);
 const selected=historic("history-county").value;
 const rows=historicalRows.filter(r=>r.year===year&&(!selected||r.fips===selected));
 const table=historic("history-rows");table.replaceChildren();
 rows.sort((a,b)=>a.month-b.month||a.county.localeCompare(b.county));
 for(const r of rows) {
   const tr=document.createElement("tr");
   for(const v of [r.year+"-"+String(r.month).padStart(2,"0"),r.county+", "+r.state,r.source||"unknown",histValue(r.peak_customers_out),histValue(r.customer_minutes),histValue(r.event_count)]){
     const td=document.createElement("td");td.textContent=v;tr.appendChild(td);
   }
   table.appendChild(tr);
 }
 historic("history-count").textContent=rows.length+" monthly rows for "+year+". This is summary history, not an individual damage-event map.";
}
document.addEventListener("DOMContentLoaded",()=>{
 const select=historic("history-county");
 fetch("config/counties.json").then(r=>r.json()).then(counties=>{for(const c of counties)select.add(new Option(c.name+", "+c.state,c.fips));}).catch(()=>{});
 historic("history-year").addEventListener("change",renderHistorical);
 select.addEventListener("change",renderHistorical);
 loadHistorical();
});
