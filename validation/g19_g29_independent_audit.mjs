// Independent diagnostic replay; no production imports. Node.js 18+.
// Usage: node validation/g19_g29_independent_audit.mjs /path/to/input-directory
import fs from 'node:fs';
import path from 'node:path';
function audit(files) {
  function parse(s) {
    let rows=[], row=[], field="", quoted=false;
    for(let i=0;i<s.length;i++){const c=s[i];if(quoted){if(c==='"'){if(s[i+1]==='"'){field+='"';i++}else quoted=false}else field+=c}
      else if(c==='"'&&field==="")quoted=true;else if(c===','){row.push(field);field=""}else if(c==='\n'){row.push(field.replace(/\r$/,""));rows.push(row);row=[];field=""}else field+=c}
    if(field||row.length){row.push(field.replace(/\r$/,""));rows.push(row)}if(quoted)throw Error("Unclosed quote");
    const header=rows.shift();header[0]=header[0].replace(/^\uFEFF/,"");const index=Object.fromEntries(header.map((v,i)=>[v,i]));
    const required=["grid_id","area_km2","ntl_mean","centroid_lat","centroid_lon","dq_status","dq_observed_fraction","dq_negative_fraction","dq_mean_valid_months","dq_stat_missing"];
    if(required.some(k=>!(k in index)))throw Error("Missing required column");
    const xc=header.find(k=>k.startsWith("centroid_x_epsg")),yc=header.find(k=>k.startsWith("centroid_y_epsg"));
    if(!xc||!yc)throw Error("Missing projected coordinates");
    const num=(r,k)=>r[index[k]]===""?NaN:Number(r[index[k]]);
    const out=rows.filter(r=>r.some(v=>v!=="")).map(r=>{
      if(r.length!==header.length)throw Error("Malformed row "+r[4]);
      const v={id:num(r,"grid_id"),x:num(r,xc),y:num(r,yc),lat:num(r,"centroid_lat"),lon:num(r,"centroid_lon"),area:num(r,"area_km2"),ntl:num(r,"ntl_mean"),status:r[index.dq_status],obs:num(r,"dq_observed_fraction"),neg:num(r,"dq_negative_fraction"),months:num(r,"dq_mean_valid_months"),missing:r[index.dq_stat_missing].toLowerCase()==="true"};
      if(![v.id,v.x,v.y,v.area,v.ntl,v.lat,v.lon].every(Number.isFinite))throw Error("Invalid cell");
      return v});
    if(new Set(out.map(r=>r.id)).size!==out.length)throw Error("Duplicate grid_id");return out;
  }
  const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
  const sum=a=>a.reduce((s,v)=>s+v,0);
  const round=x=>Number.isFinite(x)?Number(x.toFixed(9)):null;
  const gini=a=>{const s=[...a].sort((a,b)=>a-b),tot=sum(s);return tot?2*s.reduce((t,x,i)=>t+(i+1)*x,0)/(s.length*tot)-(s.length+1)/s.length:0};
  function spatial(rows, minK=1, log=false) {
    if(!rows.length)return null;
    const value=rows.map(r=>log?Math.log(r.ntl):r.ntl), mu=mean(value),z=value.map(v=>v-mu),den=sum(z.map(v=>v*v));
    const xy=rows.map(r=>[Math.floor((r.x+1e-6)/500),Math.floor((r.y+1e-6)/500)]);
    const lookup=new Map();xy.forEach((v,i)=>{const k=v.join(",");if(lookup.has(k))throw Error("Duplicate lattice key");lookup.set(k,i)});
    let binary=0,weighted=0,edges=0,lag=[],focal=[],focalArea=0;
    xy.forEach(([x,y],i)=>{let k=0,t=0;for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++){if(!dx&&!dy)continue;const j=lookup.get([x+dx,y+dy].join(","));if(j!==undefined){t+=z[j];k++}}binary+=z[i]*t;edges+=k;if(k>=minK){focal.push(z[i]);lag.push(t/k);weighted+=z[i]*t/k;focalArea+=rows[i].area}});
    const n=rows.length,m=focal.length,mx=mean(focal),my=mean(lag),slope=sum(focal.map((x,i)=>(x-mx)*(lag[i]-my)))/sum(focal.map(x=>(x-mx)**2));
    return {members:n,focal:m,members_area_km2:round(sum(rows.map(r=>r.area))),focal_area_km2:round(focalArea),binary_global_I:round(n*binary/(edges*den)),row_standardized_global_I_with_islands:round(n*weighted/(m*den)),focal_scatter_ols_slope:round(slope),focal_to_members_area_ratio:round(focalArea/sum(rows.map(r=>r.area)))};
  }
  const parsed=Object.fromEntries(Object.entries(files).map(([k,v])=>[k,parse(v)]));
  const sites=Object.entries(parsed).map(([file,rows])=>{
    let status={};for(const r of rows)status[r.status]=(status[r.status]||0)+1;
    const core=rows.filter(r=>r.area>=.2475&&r.ntl>0);
    const latMin=Math.min(...rows.map(r=>r.lat)),latMax=Math.max(...rows.map(r=>r.lat));
    return {file,n:rows.length,status,zero_ntl:rows.filter(r=>r.ntl===0).length,negative_fraction_positive:rows.filter(r=>r.neg>0).length,low_months_lt3:rows.filter(r=>Number.isFinite(r.months)&&r.months<3).length,partial_support:rows.filter(r=>r.obs<1).length,unknown_support_fields:rows.filter(r=>!Number.isFinite(r.obs)||!Number.isFinite(r.months)).length,stat_missing:rows.filter(r=>r.missing).length,latitude_range:[latMin,latMax],cosine_weight_range_ratio:round(Math.cos(latMin*Math.PI/180)/Math.cos(latMax*Math.PI/180)-1),global_all_raw:spatial(rows),core_positive_raw_min1:spatial(core),core_positive_raw_min4:spatial(core,4),core_positive_log_min1:spatial(core,1,true)};
  });
  const keys=Object.keys(parsed).filter(k=>k.startsWith("qimen"));
  const pairs=[];for(let i=0;i<keys.length;i++)for(let j=i+1;j<keys.length;j++){
    const a=parsed[keys[i]],b=parsed[keys[j]],map=new Map(b.map(r=>[r.id,r]));let ids=0,coords=0,areas=0,support=0,entry=0,exit=0;
    for(const r of a){const t=map.get(r.id);if(!t)continue;ids++;coords+=r.x===t.x&&r.y===t.y&&r.lat===t.lat&&r.lon===t.lon;areas+=r.area===t.area;const ok=r.status==="observed"&&t.status==="observed"&&r.obs===1&&t.obs===1;support+=ok;if(ok){entry+=r.ntl===0&&t.ntl>0;exit+=r.ntl>0&&t.ntl===0}}
    pairs.push({from:keys[i],to:keys[j],matched_ids:ids,same_exported_centroids:coords,same_exported_areas:areas,both_full_support:support,observed_zero_to_positive:entry,observed_positive_to_zero:exit});
  }
  const full=[10,20,0,30], observed=[10,20,30], a=[10,0,0,5], b=[10,8,0,5], valid0=[true,false,true,true],valid1=[true,true,true,true];
  const legacyEntry=a.filter((x,i)=>x===0&&b[i]>0).length/a.filter(x=>x===0).length;
  const supportedEntry=a.filter((x,i)=>valid0[i]&&valid1[i]&&x===0&&b[i]>0).length/a.filter((x,i)=>valid0[i]&&valid1[i]&&x===0).length;
  let state=123456789;function rng(){state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296}
  function gridI(x,n){const m=mean(x),z=x.map(v=>v-m);let s=0,w=0;for(let i=0;i<n;i++)for(let j=0;j<n;j++)for(const [di,dj] of [[1,0],[-1,0],[0,1],[0,-1]]){const a=i+di,b=j+dj;if(a>=0&&a<n&&b>=0&&b<n){s+=z[i*n+j]*z[a*n+b];w++}}return x.length*s/(w*sum(z.map(v=>v*v)))}
  const aligned=[],shifted=[],n=24;
  for(let rep=0;rep<400;rep++){const x=Array.from({length:(n+1)**2},()=>rng());let a=[],b=[];for(let i=0;i<n;i++)for(let j=0;j<n;j++){const k=i*(n+1)+j;a.push(x[k]);b.push((x[k]+x[k+1]+x[k+n+1]+x[k+n+2])/4)}aligned.push(gridI(a,n));shifted.push(gridI(b,n))}
  const q=a=>{const s=[...a].sort((a,b)=>a-b);return {mean:round(mean(a)),p025:round(s[Math.floor(.025*s.length)]),p975:round(s[Math.floor(.975*s.length)])}};
  const sims=[-5,-4,-3,-2,-1,0,1,2,3],obs=2;
  return {base_sha:"a53d02222e4d4251e2043306fbe9804b4b6ca8ca",method:"Independent JavaScript calculations using exported cell CSV text; not execution of Python production or a new raster extraction. Inputs are owner-held. Exact source-file hashes not measured in connector text path.",field:{sites,qimen_pair_alignment:pairs},synthetic:{G19:{input_legacy:full,input_observed:observed,legacy_mean:mean(full),observed_mean:mean(observed),legacy_gini:round(gini(full)),observed_gini:round(gini(observed))},G26:{year0:a,year1:b,valid0,valid1,legacy_entry_fraction:legacyEntry,common_support_entry_fraction:supportedEntry},G22:{fine_hh_area:1,coarse_hh_area:4,any_overlap_block_fraction:1,actual_overlap_area_fraction:.25},G23:{design:"400 independent 25x25 uniform source rasters, 24x24 output, equal-area half-cell shift on both axes; four-neighbor binary Global Moran, no physical VIIRS PSF, no LISA or FDR inference",aligned:q(aligned),shifted:q(shifted),replicates:aligned.map((v,i)=>[i+1,round(v),round(shifted[i])])},G29:{observed:obs,simulated:sims,absolute_tail_p:(1+sims.filter(x=>Math.abs(x)>=Math.abs(obs)).length)/(sims.length+1),doubled_smaller_tail_p:Math.min(1,2*(1+Math.min(sims.filter(x=>x>=obs).length,sims.filter(x=>x<=obs).length))/(sims.length+1))}}};
}
const names=["qimen_NTL_2014_500m.csv","qimen_NTL_2016_500m.csv","qimen_NTL_2020_500m.csv","bao_an_NTL_2020_500m.csv","shanghai_NTL_2020_500m.csv"];
const dir=process.argv[2];if(!dir)throw Error('Provide owner-held CSV input directory');
console.log(JSON.stringify(audit(Object.fromEntries(names.map(n=>[n,fs.readFileSync(path.join(dir,n),'utf8')]))),null,2));
