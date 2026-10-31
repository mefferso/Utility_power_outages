"use strict";
let outageMap, outageLayer;
function createOutageMap() {
  if(!document.getElementById("outage-map") || !window.L)return;
  outageMap=L.map("outage-map",{preferCanvas:true}).setView([30.5,-90.4],8);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:18,attribution:'&copy; OpenStreetMap contributors'}).addTo(outageMap);
  outageLayer=L.layerGroup().addTo(outageMap);
}
function paintOutageMap(records) {
  if(!outageMap)return;
  outageLayer.clearLayers();
  const latestOnly=document.getElementById("map-latest").checked;
  let shown=records;
  if(latestOnly) {
    const latest=records.reduce((max,r)=>r.observed_at>max?r.observed_at:max,"");
    shown=records.filter(r=>r.observed_at===latest);
  }
  let markers=0;
  for(const r of shown) {
    if(r.lat==null||r.lon==null||!Number.isFinite(+r.lat)||!Number.isFinite(+r.lon)||Math.abs(+r.lat)>90||Math.abs(+r.lon)>180)continue;
    const count=Number(r.customers_out);
    const size=Number.isFinite(count)&&count>0?Math.min(17,4+Math.log10(count+1)*3):5;
    const marker=L.circleMarker([+r.lat,+r.lon],{radius:size,color:"#ffffff",weight:1,fillColor:/tree|wind|storm|vegetation|lightning|limb/i.test(r.cause||"")?"#edb74e":"#5bb7ec",fillOpacity:.8});
    const node=document.createElement("div");
    const lines=[["Observed UTC",r.observed_at],["Utility",r.utility],["Parish / county",r.county+", "+r.state],["Customers out",r.customers_out],["Reported cause",r.cause],["Crew status",r.crew_status],["Approx. location",(+r.lat).toFixed(3)+", "+(+r.lon).toFixed(3)]];
    for(const [k,v] of lines){const p=document.createElement("p");p.style.margin="4px";p.textContent=k+": "+(v??"Unknown");node.appendChild(p);}
    marker.bindPopup(node);marker.addTo(outageLayer);markers++;
  }
  document.getElementById("map-status").textContent=markers+" mapped observations"+(latestOnly?" (latest matching collection time)":" (all matching times)")+". Approximate locations; repeats may overlap.";
}
document.addEventListener("DOMContentLoaded",()=>{createOutageMap();document.getElementById("map-latest")?.addEventListener("change",()=>paintOutageMap(window.outageFiltered||[]));});
