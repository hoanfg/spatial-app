// Deterministic SVG figures from retained evidence, no additional dependencies.
// node validation/generate_validation_figures.mjs [--verify]
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const inputs={
  "g4": "g04_ntl_potential/summary.json",
  "g5": "g05_ntl_center/summary.json",
  "g6": "g06_pareto_tail/summary.json",
  "g17": "g17_spatial_fdr/summary.json",
  "g18": "g18_zero_support/summary.json",
  "csv": "g19_g29_independent_audit.json",
  "raster": "g20_g23_g17_raster_summary.json",
  "est": "g24_g25_g27_estimand_reference.json",
  "boot": "g28_block_coverage_reference.json",
  "a02": "audit-2026-11-15/verified_summary.json"
};
function generate(d){
 const C=["#226a9b","#168077","#b56e16","#7755a2"],ink="#182d3c",muted="#536674",grid="#d7e2e9",files={};
 const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
 const N=(v,p=3)=>Number(v).toFixed(p), f=v=>{if(!Number.isFinite(v))throw Error("Nonfinite geometry: "+v);return +v.toFixed(5)};
 const T=(x,y,s,size=15,anchor="start",color=ink,bold=false)=>`<text x="${f(x)}" y="${f(y)}" font-size="${size}" text-anchor="${anchor}" fill="${color}" font-weight="${bold?600:400}">${esc(s)}</text>`;
 const L=(x,y,x2,y2,c=grid,w=1,dash="")=>`<line x1="${f(x)}" y1="${f(y)}" x2="${f(x2)}" y2="${f(y2)}" stroke="${c}" stroke-width="${w}" ${dash?'stroke-dasharray="'+dash+'"':""}/>`;
 const R=(x,y,w,h,c,stroke="none",rx=3)=>`<rect x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" rx="${rx}" fill="${c}" stroke="${stroke}"/>`;
 const dot=(x,y,i)=>i%3===0?`<circle cx="${f(x)}" cy="${f(y)}" r="5" fill="${C[i]}" stroke="white"/>`:i%3===1?R(x-4.5,y-4.5,9,9,C[i],"white",0):`<path d="M${f(x)},${f(y-6)} L${f(x+5)},${f(y+5)} L${f(x-5)},${f(y+5)} Z" fill="${C[i]}" stroke="white"/>`;
 function save(id,title,sub,body,h,note){
 const s=`<svg xmlns="http://www.w3.org/2000/svg" width="840" height="${h}" viewBox="0 0 840 ${h}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(sub+". "+note)}</desc><rect width="840" height="${h}" fill="white" rx="10"/><g font-family="Arial, Helvetica, sans-serif">${T(26,34,title,23,"start",ink,true)}${T(26,58,sub,14,"start",muted)}${L(26,73,814,73)}${body}${L(26,h-40,814,h-40)}${T(26,h-17,note,12,"start",muted)}</g></svg>\n`;
 if(/NaN|Infinity|undefined/.test(s))throw Error(id+" invalid");files[id+".svg"]=s;}
 function bars(id,title,sub,rows,labels,o={}){
 const {min=0,max=1,left=210,digits=3,suffix="",note="",ticks=5}=o;
 const top=labels.length>1?113:94,gh=labels.length*25+20,bot=top+rows.length*gh,right=735,X=v=>left+(v-min)/(max-min)*(right-left),z=X(Math.max(min,0));let s="";
 if(labels.length>1)labels.forEach((v,i)=>{let x=26+i*780/labels.length;s+=R(x,84,13,13,C[i])+T(x+19,95,v,13)});
 for(let i=0;i<=ticks;i++){let v=min+(max-min)*i/ticks; s+=L(X(v),top-7,X(v),bot-9)+T(X(v),bot+11,N(v,digits===0?0:Math.min(digits,3)),12,"middle",muted)}
 s+=L(z,top-7,z,bot-9,"#8c9ca7");
 rows.forEach((r,i)=>{let y=top+i*gh;s+=T(left-12,y+labels.length*12,r[0],14,"end");r[1].forEach((v,j)=>{let x=X(v);s+=R(Math.min(z,x),y+j*25,Math.max(.5,Math.abs(x-z)),19,C[labels.length===1?i%4:j])+T(v<0?x-7:x+7,y+j*25+15,N(v,digits)+suffix,13,v<0?"end":"start",ink,true)})});
 save(id,title,sub,s,bot+66,note);
 }
 function line(id,title,sub,xs,series,o={}){
 const {min=0,max=1,ticks=5,digits=2,xlabel="",note="",ref=null,refLabel="",pct=false}=o;const left=90,right=785,top=105,bot=340,xx=v=>left+(v-xs[0])/(xs.at(-1)-xs[0])*(right-left),yy=v=>bot-(v-min)/(max-min)*(bot-top);let s="";
 for(let i=0;i<=ticks;i++){let v=min+(max-min)*i/ticks;s+=L(left,yy(v),right,yy(v))+T(left-10,yy(v)+4,N(v,digits)+(pct?"%":""),12,"end",muted)}
 s+=L(left,top,left,bot,"#8c9ca7")+L(left,bot,right,bot,"#8c9ca7");
 xs.forEach(v=>s+=T(xx(v),bot+22,v,13,"middle",muted));s+=T((left+right)/2,bot+44,xlabel,14,"middle");
 if(ref!==null)s+=L(left,yy(ref),right,yy(ref),"#607381",1.5,"5 4")+T(right-4,yy(ref)-8,refLabel,12,"end",muted);
 series.forEach((a,i)=>{s+=`<polyline points="${a[1].map((v,j)=>f(xx(xs[j]))+","+f(yy(v))).join(" ")}" fill="none" stroke="${C[i]}" stroke-width="2.5" ${i%2?'stroke-dasharray="7 4"':""}/>`;a[1].forEach((v,j)=>s+=dot(xx(xs[j]),yy(v),i));let lx=32+i*780/series.length;s+=dot(lx,407,i)+T(lx+12,411,a[0],13)});
 save(id,title,sub,s,463,note);
 }
 function box(x,y,w,h,title,lines,i=0){return R(x,y,w,h,"#f4f8fb",C[i],7)+T(x+13,y+25,title,17,"start",C[i],true)+lines.map((s,j)=>T(x+13,y+49+j*23,s,14)).join("")}
 function arrow(x,y,x2,y2){let a=Math.atan2(y2-y,x2-x);return L(x,y,x2,y2,muted,1.6)+L(x2-9*Math.cos(a-.5),y2-9*Math.sin(a-.5),x2,y2,muted,1.6)+L(x2-9*Math.cos(a+.5),y2-9*Math.sin(a+.5),x2,y2,muted,1.6)}
 let r=d.g4.sensitivity.filter(x=>x.source==="synthetic"&&x.radius_steps===5&&x.tau_per_km===.5);
 bars("g04_construct","G04 | Construct sensitivity","Synthetic job surface; radius 5 cells, tau = 0.5/km",r.map(x=>[{"light_aligned":"Aligned light","bright_nonjob_artifact":"Unrelated bright source","shuffled_placebo":"Shuffled light"}[x.scenario],[x.rank_corr_vs_constructed_jobs]]),["Spearman"],{min:-.4,max:1,ticks:7,left:245,note:"Spearman vs constructed job potential; not independent economic validation."});
 r=d.g4.sensitivity.filter(x=>x.source==="baoan_real_ntl");line("g04_kernel","G04 | Top-decile overlap","Bao'an 2020 observed NTL; baseline potential as reference",[3,5,8],[.25,.5,1].map(t=>["tau = "+t+"/km",[3,5,8].map(k=>r.find(x=>x.radius_steps===k&&x.tau_per_km===t).top_decile_jaccard_vs_baseline)]),{xlabel:"Radius (500 m grid steps)",note:"Jaccard overlap of the highest-ranked 10%; not market-access accuracy."});
 r=d.g5.center_comparisons;line("g05_center","G05 | Center-selection error","Known synthetic generator center; unrelated light artifact",[0,60,170],[["production_lisa_selected","LISA-selected"],["ntl_weighted_centroid","NTL centroid"],["brightest_ntl_cell","Brightest cell"],["geometry_only_centroid","Geometry centroid"]].map(([k,l])=>[l,["baseline","nonjob_light_60","nonjob_light_170"].map(sc=>r.find(x=>x.scenario===sc&&x.center_method===k).center_distance_to_reference_km)]),{max:8,ticks:4,digits:1,xlabel:"Artifact intensity (synthetic units)",note:"Vertical axis: distance to the known synthetic center (km), not an observed CBD."});
 r=d.g6.cases;line("g06_pareto","G06 | Conditional Pareto tail fit","Fixed cutoffs; 399 refitted iid Pareto bootstrap replicates",[5,10,15,20],[["iid_pareto","Synthetic Pareto"],["iid_lognormal","Synthetic lognormal"],["iid_exponential","Synthetic exponential"],["baoan_2020_ntl","Bao'an NTL"]].map(([k,l])=>[l,[.05,.1,.15,.2].map(f=>r.find(x=>x.source===k&&x.tail_fraction===f).refit_bootstrap_ks_p)]),{ref:.05,refLabel:"p = 0.05",xlabel:"Fixed upper-tail fraction (%)",note:"Vertical axis: refit-bootstrap p; conditional iid test, not spatial-tail calibration."});
 r=d.g17.results.filter(x=>x.study==="gaussian_valid_p"&&x.scenario==="global_null");bars("g17_fdr","G17 | All-null empirical FDR","Known Gaussian nulls; 400 simulations per configuration",r.map(x=>[x.weights+" / rho "+x.rho,[100*x.methods.bh.empirical_fdr,100*x.methods.by.empirical_fdr]]),["BH","BY"],{max:8,ticks:4,digits:2,suffix:"%",note:"Nominal alpha = 5%; finite simulations, not field FDR guarantees."});
 r=d.raster.G17;bars("g17_source_null","G17 | Source-null p-value calibration","Bao'an 8 x 8 geometry; 999 reference draws, 400 test fields",[["Marginal p <= .05",[100*r.cell_permutation.marginal_p_le_005,100*r.source_reference.marginal_p_le_005]],["BH any rejection",[100*r.cell_permutation.any_rejection_counts.BH/r.test_draws,100*r.source_reference.any_rejection_counts.BH/r.test_draws]]],["Cell permutation","Source reference"],{max:12,ticks:6,digits:2,suffix:"%",note:"Distinct reference hypotheses; percentages evaluated under the simulated source null."});
 bars("g18_support","G18 | Zero-support sensitivity","Synthetic 12 x 12 grid; Queen, 999 permutations, BH alpha = .05",["positive_only","observed_zeros","naive_missing_as_zero"].map((k,i)=>{let a=d.g18.runs[k+"__bh_fdr"];return [["Positive only","Observed zeros","Missing as zero"][i],[a.hh_cells,a.ll_cells]]}),["HH cells","LL cells"],{max:28,ticks:4,digits:0,note:"One synthetic field; the last policy admits 10 unobserved cells."});
 bars("g10_support","G10/G18 | Reported observation support","Five exported datasets; no verified incomplete-support case",d.csv.field.sites.map(x=>[x.file.replace("_NTL_"," ").replace("_500m.csv","").replace("bao_an","Bao'an").replace("qimen","Qimen").replace("shanghai","Shanghai"),[x.n,x.status.observed]]),["Records","Observed records"],{max:10000,ticks:5,digits:0,note:"Finite reference cf_cvg pixels are positive; AOI masking is not missingness."});
 r=d.csv.synthetic.G19;save("g19_missing","G19 | Zero-fill changes the population","Equal-area cells; the third location is unobserved",box(30,95,360,116,"Legacy zero-fill",[r.input_legacy.join(" | "),"Mean = "+N(r.legacy_mean,0)+"   Gini = "+N(r.legacy_gini,6)])+box(450,95,360,116,"Observed only",[r.input_observed.join(" | "),"Mean = "+N(r.observed_mean,0)+"   Gini = "+N(r.observed_gini,6)],1)+arrow(394,151,446,151)+T(420,243,"An unknown value is not a measured zero.",16,"middle",ink,true),302,"Synthetic counterexample; the true regional mean is unknown.");
 r=d.raster.G20.baoan_offline_aligned_four_tiles;let s="";for(let i=0;i<4;i++)s+=R(38+i%2*76,100+Math.floor(i/2)*60,72,56,"#dceaf4",C[0],1)+T(74+i%2*76,132+Math.floor(i/2)*60,"Tile "+(i+1),13,"middle");s+=arrow(200,160,274,160)+R(285,100,148,116,"#dceaf4",C[0],1)+T(359,155,"Mosaic",16,"middle",ink,true)+T(359,176,r.shape.slice(1).join(" x ")+" pixels",13,"middle")+box(474,94,336,135,"Offline comparison",[r.valid_values.toLocaleString("en-US")+" finite pixels compared","Maximum difference = "+r.max_abs_valid_difference,"Transform and finite mask: identical"],1);save("g20_tiles","G20 | Aligned tile mosaic","Schematic of integer windows from one Bao'an 2020 reference raster",s,283,"Aligned offline split only; independent Earth Engine downloads remain untested.");
 r=d.csv.synthetic.G26;save("g26_temporal","G26 | Missingness and false entry","Synthetic two-period example; one baseline cell is unobserved",box(30,95,360,135,"Legacy: "+N(r.legacy_entry_fraction*100,0)+"% entry",["t0: "+r.year0.join(" | "),"t1: "+r.year1.join(" | "),"1 of 2 baseline zeros becomes positive"],2)+box(450,95,360,135,"Common support: "+N(r.common_support_entry_fraction*100,0)+"% entry",["t0: "+r.year0.map((v,i)=>r.valid0[i]?v:"NA").join(" | "),"t1: "+r.year1.join(" | "),"0 of 1 observed baseline zero enters"],1)+arrow(394,158,446,158)+T(420,254,"The missing location is excluded from the paired domain.",14,"middle"),310,"Illustrative entry-rate denominator; not measured economic transition.");
 r=d.raster.G11_G21;bars("g11_area","G11 | UTM area sensitivity","Exported polygons compared with WGS84 ellipsoidal areas",["baoan","qimen"].map(k=>[k==="baoan"?"Bao'an":"Qimen",[100*r[k].mean_abs_utm_geodesic_rel,100*r[k].max_abs_utm_geodesic_rel]]),["Mean relative error","Maximum relative error"],{max:.24,ticks:4,digits:3,suffix:"%",note:"Local absolute relative area discrepancy; not a global tolerance."});
 bars("g21_weighting","G21 | Physical intersection weighting","Mean absolute NTL difference between angular and physical weighting",["baoan","qimen"].map(k=>[k==="baoan"?"Bao'an 2020":"Qimen 2016",[r[k].mean_abs_radiance_difference*1e6]]),["Difference"],{max:12,ticks:6,digits:3,note:"Horizontal axis: absolute radiance difference x 10^6; reference rasters only."});
 bars("g22_maup","G22/A07 | Direct vs aggregated NTL","Aligned coarse grids; Bao'an reference raster",d.raster.G22.rows.filter(x=>x[1]===0).map(x=>[x[0]+" m",[x[6]*1e6,x[7]*1e6]]),["Mean abs. difference","Maximum abs. difference"],{max:650,ticks:5,digits:1,note:"Horizontal axis: absolute radiance difference x 10^6; not HH stability."});
 r=d.csv.synthetic.G23;let g=d.raster.G23,vals=[["Ideal aligned",r.aligned.mean,r.aligned.p025,r.aligned.p975],["Bao'an geometry",g.mean_global_moran,...g.empirical_p025_p975],["Ideal half-cell shift",r.shifted.mean,r.shifted.p025,r.shifted.p975]],X=v=>245+(v+.1)/.75*520;s="";for(let i=0;i<=7;i++){let v=-.1+i*.1;s+=L(X(v),94,X(v),251)+T(X(v),270,N(v,1),12,"middle",muted)}s+=L(X(0),94,X(0),251,muted,1,"4 4");vals.forEach(([l,v,lo,hi],i)=>{let y=121+i*54;s+=T(231,y+5,l,15,"end")+L(X(lo),y,X(hi),y,C[i],3)+L(X(lo),y-7,X(lo),y+7,C[i])+L(X(hi),y-7,X(hi),y+7,C[i])+dot(X(v),y,i)+T(X(v),y-13,N(v,3),13,"middle",ink,true)});save("g23_shared","G23 | Shared-pixel induced Moran","400 source-independent simulated fields per configuration",s,316,"Points: mean Global Moran; whiskers: empirical 2.5th-97.5th percentiles, not field CIs.");
 let est=d.est.sites;bars("g24_moran","G24 | Three Moran-related estimands","2020 CSV reference; Queen, minK = 4; raw and log NTL",est.flatMap(site=>site.settings.filter(x=>x.minK===4).map(x=>[(site.name.startsWith("shanghai")?"Shanghai":"Bao'an")+(x.log?" / log":" / raw"),[x.mean_local_I,x.matched_zero_row_global_I,x.slope_ui_rounded]])),["Mean Local I","Global I (zero rows)","Focal slope"],{max:1.05,ticks:5,note:"Global diagnostic zeroes untested rows; independent reference, not production UI."});
 let q=est.find(x=>x.name.startsWith("bao")).settings.find(x=>x.minK===4&&x.log),hh=q.HH_BH;s=R(30,94,780,162,"#eef5fa",C[0],8)+T(46,117,"Members: "+N(q.members_area,3)+" km²",16,"start",C[0],true)+R(45,131,750,110,"#e5f4f0",C[1],6)+T(61,154,"Focal: "+N(q.focal_area,3)+" km²",16,"start",C[1],true)+R(62,167,265,57,"#f7e9d6",C[2],5)+T(75,190,"HH: "+N(hh.area,3)+" km²",16,"start",C[2],true)+T(75,210,hh.n.toLocaleString("en-US")+" HH cells",13)+T(30,283,"HH / members",15,"start",muted)+T(30,315,N(hh.share_members*100,4)+"%",28,"start",ink,true)+T(447,283,"HH / focal",15,"start",muted)+T(447,315,N(hh.share_focal*100,4)+"%",28,"start",ink,true);save("g25_denominator","G25 | HH area and denominator","Bao'an 2020, log NTL, Queen, minK = 4, BH; reference labels",s,371,"Nested boxes are schematic, not area-proportional; same HH numerator.");
 let pc=d.est.panel_counterexample;s=box(32,92,350,111,"Record A",[pc.first.year+" | "+pc.first.cell_size_m+" m",pc.first.p_cfg_perms+" permutations | Raw NTL"])+box(458,92,350,111,"Record B",[pc.second.year+" | "+pc.second.cell_size_m+" m",pc.second.p_cfg_perms+" permutations | Log NTL"],1)+L(207,203,207,221,muted)+L(633,203,633,221,muted)+L(207,221,633,221,muted)+arrow(420,221,420,242)+box(200,248,440,91,"Same region-year-grid key",["B replaces A despite different method settings"],2);save("g27_panel","G27 | Panel key collision","Controlled records; identical spatial and temporal key",s,389,"Illustrative reconstruction of the replacement rule, not a live Streamlit regression.");
 let boot=d.boot.rows;for(const [k,id,title,max,ref] of [["coverage","g28_coverage","G28 | Empirical bootstrap coverage",100,95],["mean_width","g28_width","G28 | Mean bootstrap interval width",.45,null]])line(id,title,"20 x 20 Gaussian grid; 120 fields per scenario; 200 resamples",[1,2,4,5],[0,1,2].map(sig=>["Kernel SD = "+sig+" cells",[1,2,4,5].map(b=>boot.find(x=>x.sigma===sig&&x.block===b)[k]*(k==="coverage"?100:1))]),{max,ticks:k==="coverage"?4:5,digits:k==="coverage"?0:2,pct:k==="coverage",ref,refLabel:"95% nominal",xlabel:"Block side (cells)",note:k==="coverage"?"Known Gaussian target; finite simulation, not guaranteed field coverage.":"Width alone does not indicate inferential accuracy; compare with coverage."});
 r=d.csv.synthetic.G29;X=v=>70+(v+5)/8*690;s=L(70,178,760,178,"#889aa7");for(let v=-5;v<=3;v++)s+=L(X(v),178,X(v),185,"#889aa7")+T(X(v),201,v,13,"middle");r.simulated.forEach(v=>s+=`<circle cx="${f(X(v))}" cy="156" r="8" fill="${Math.abs(v)>=Math.abs(r.observed)?C[0]:"#a8b5bf"}"/>`);s+=L(X(r.observed),107,X(r.observed),178,C[2],2,"4 3")+T(X(r.observed),98,"Observed I = "+r.observed,14,"middle",C[2],true)+T(32,244,"Absolute tail p = "+N(r.absolute_tail_p,1),21,"start",ink,true)+T(454,244,"Doubled smaller tail p = "+N(r.doubled_smaller_tail_p,1),20,"start",ink,true);save("g29_tails","G29 | P-value tail convention","Nine asymmetric reference statistics; inclusive tails, +1 correction",s,296,"Blue points meet the absolute-tail rule; arithmetic counterexample.");
 r=d.a02;save("a02_observed","A02 | Archived Bao'an observation metadata","Field CSV integrity check; no genuinely unobserved row",box(32,95,370,110,"Observed records",[r.observed_rows.toLocaleString("en-US")+" / "+r.rows.toLocaleString("en-US")+" rows",r.unique_grid_ids.toLocaleString("en-US")+" unique grid IDs"])+box(438,95,370,110,"Valid months (cell mean)",["Min "+r.mean_valid_months.min+" | Max "+r.mean_valid_months.max,"Overall mean "+N(r.mean_valid_months.mean,4)],1),263,"Archived CSV check only; does not verify missing-observation cases.");
 return files;
}
const data=Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,JSON.parse(fs.readFileSync(path.join(root,'evidence',v),'utf8'))]));
const figs=generate(data);
function tailAndPowerFigures(g6,csv,g17){
 const ink="#182d3c",muted="#536674",blue="#226a9b",green="#168077",amber="#b56e16",grid="#d7e2e9",out={};
 const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");const f=(x,p=3)=>Number(x).toFixed(p);
 const T=(x,y,s,size=15,anchor="start",color=ink,bold=false)=>`<text x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}" fill="${color}" font-weight="${bold?600:400}">${esc(s)}</text>`;
 const L=(x,y,x2,y2,c=grid,w=1,dash="")=>`<line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" ${dash?'stroke-dasharray="'+dash+'"':""}/>`;
 const D=(x,y,c,r=4)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="${c}" stroke="white" stroke-width=".7"/>`;
 function save(id,title,sub,h,body,note){let v=`<svg xmlns="http://www.w3.org/2000/svg" width="840" height="${h}" viewBox="0 0 840 ${h}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(sub+". "+note)}</desc><rect width="840" height="${h}" rx="10" fill="white"/><g font-family="Arial, Helvetica, sans-serif">${T(26,34,title,23,"start",ink,true)}${T(26,58,sub,14,"start",muted)}${L(26,73,814,73)}${body}${L(26,h-40,814,h-40)}${T(26,h-17,note,12,"start",muted)}</g></svg>\n`;if(/NaN|Infinity|undefined/.test(v))throw Error(id+" invalid");out[id+".svg"]=v;}
 const cs=g6.cases.find(x=>x.source==="baoan_2020_ntl"&&x.tail_fraction===.1);
 const rows=csv.trim().split(/\r?\n/);if(rows[0]!=="grid_id,is_full_core,included_positive_core,ntl_mean_original,positive_core_descending_rank")throw Error("Unexpected CCDF source schema");
 const a=rows.slice(1).map(l=>l.split(",")).filter(v=>v[2]==="1").map(v=>({x:+v[3],rank:+v[4]})).sort((a,b)=>a.rank-b.rank);if(a.length!==cs.n_positive||a.some((v,i)=>v.rank!==i+1))throw Error("CCDF source ranks mismatch");
 const tail=a.slice(0,cs.k_tail),u=cs.u_threshold,k=tail.length;if(tail.some(v=>v.x<u))throw Error("Tail below cutoff");
 const xmax=Math.log10(tail[0].x/u),ymin=Math.floor(Math.log10(Math.min(1/k,10**(-cs.alpha_hill*xmax))));
 const xx=v=>85+Math.log10(v)*680/xmax,yy=v=>330-(Math.log10(v)-ymin)*228/(0-ymin);let s="";
 for(let i=ymin;i<=0;i++){s+=L(85,yy(10**i),765,yy(10**i))+T(74,yy(10**i)+4,i===0?"1":"10^"+i,12,"end",muted)}
 for(const t of [1,1.5,2,3,4].filter(t=>Math.log10(t)<=xmax)){s+=L(xx(t),102,xx(t),330)+T(xx(t),350,t,12,"middle",muted)}
 s+=L(85,102,85,330,muted)+L(85,330,765,330,muted)+T(85,91,"Tail survival probability (log scale)",13,"start",muted);
 // Inclusive empirical survival at each distinct tail value; only display points are thinned.
 const tied=[];for(let i=0;i<tail.length;){let j=i+1;while(j<tail.length&&tail[j].x===tail[i].x)j++;tied.push({x:tail[i].x/u,p:j/k});i=j}
 const stride=Math.max(1,Math.floor(tied.length/120));const pts=tied.filter((v,i)=>i===0||i===tied.length-1||i%stride===0);
 let fit=[];for(let i=0;i<=100;i++){let t=xmax*i/100,p=10**(-cs.alpha_hill*t);fit.push(`${85+t*680/xmax},${yy(p)}`)}
 s+=`<polyline points="${fit.join(" ")}" stroke="${amber}" stroke-width="2.3" stroke-dasharray="6 3" fill="none"/>`;pts.forEach(v=>s+=D(xx(v.x),yy(v.p),blue,2.8));
 s+=T(425,374,"NTL / fixed cutoff (log scale)",14,"middle")+D(115,402,blue)+T(129,407,"Empirical tail (thinned for display)",13)+L(470,402,503,402,amber,2.3,"6 3")+T(513,407,"Fitted Pareto",13);
 save("g06_ccdf","G06 | Bao'an conditional tail CCDF","Upper 10% of positive core NTL; k = "+k+", Hill alpha = "+f(cs.alpha_hill),463,s,"Observed tail vs fitted iid Pareto; fixed cutoff, not spatial-distribution validation.");
 const powers=g17.results.filter(x=>x.study==="gaussian_valid_p"&&x.scenario==="fixed_3x3_mean_shift");if(powers.length!==8)throw Error("G17 power rows missing");
 const left=200,right=752,top=112,gh=46,bot=top+gh*powers.length,X=v=>left+v/.6*(right-left);
 s=D(35,91,blue)+T(47,95,"BH",13)+`<rect x="115" y="87" width="8" height="8" fill="${green}"/>`+T(130,95,"BY",13)+T(242,95,"Whiskers: reported Monte Carlo 95% intervals",12,"start",muted);
 for(let i=0;i<=6;i++){let v=i/10;s+=L(X(v),top-7,X(v),bot-8)+T(X(v),bot+11,f(v,1),12,"middle",muted)}
 powers.forEach((r,i)=>{let y=top+i*gh;s+=T(left-12,y+20,r.weights+" / rho "+r.rho,14,"end");["bh","by"].forEach((key,j)=>{const a=r.methods[key],c=j?green:blue,yp=y+8+j*18,[lo,hi]=a.power_mc_ci95_normal,v=a.injection_power;s+=L(X(lo),yp,X(hi),yp,c,2.5)+L(X(lo),yp-4,X(lo),yp+4,c)+L(X(hi),yp-4,X(hi),yp+4,c)+(j?`<rect x="${X(v)-3.7}" y="${yp-3.7}" width="7.4" height="7.4" fill="${c}" stroke="white"/>`:D(X(v),yp,c,4))+T(X(hi)+7,yp+4,f(v),12,"start",ink,true)})});
 save("g17_power","G17 | Detection power under planted signals","Nine injected Gaussian signals; 400 simulations per configuration",bot+66,s,"Power = fraction of injected cells detected; uncertainty is Monte Carlo, not field inference.");
 return out;
}
Object.assign(figs,tailAndPowerFigures(data.g6,fs.readFileSync(path.join(root,'evidence','g06_pareto_tail','baoan_tail_observations.csv'),'utf8'),data.g17));

function archivedFigures(report,g5,ind){
 const ink="#182d3c",muted="#536674",blue="#226a9b",green="#168077",amber="#b56e16",purple="#7755a2",grid="#d7e2e9",out={};
 const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
 const f=(x,p=3)=>Number(x).toFixed(p),number=s=>Number(s.replace(/,/g,""));
 const T=(x,y,s,size=15,color=ink,bold=false,anchor="start")=>`<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${bold?600:400}" text-anchor="${anchor}">${esc(s)}</text>`;
 const R=(x,y,w,h,c,stroke="none",extra="")=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="2" fill="${c}" stroke="${stroke}" ${extra}/>`;
 const L=(x,y,x2,y2,c=grid,w=1,dash="")=>`<line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" ${dash?'stroke-dasharray="'+dash+'"':""}/>`;
 const D=(x,y,c,r=5)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="${c}" stroke="white"/>`;
 function save(id,title,sub,h,body,note){
  let v=`<svg xmlns="http://www.w3.org/2000/svg" width="840" height="${h}" viewBox="0 0 840 ${h}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(sub+". "+note)}</desc><rect width="840" height="${h}" rx="10" fill="white"/><g font-family="Arial, Helvetica, sans-serif">${T(26,34,title,23,ink,true)}${T(26,58,sub,14,muted)}${L(26,73,814,73)}${body}${L(26,h-40,814,h-40)}${T(26,h-17,note,12,muted)}</g></svg>\n`;
  if(/NaN|Infinity|undefined/.test(v))throw Error(id+" invalid: "+v.match(/.{0,50}(NaN|Infinity|undefined).{0,50}/)?.[0]);out[id+".svg"]=v;
 }
 function match(rx){let m=report.match(rx);if(!m)throw Error("Missing report evidence "+rx);return m;}
 let m=match(/All ([\d,]+) full cells met the CSV bound\. Among clipped cells, ([\d,]+)\/([\d,]+) met (0\.\d+)/);
 const full=number(m[1]),clipPass=number(m[2]),clipN=number(m[3]),total=full+clipN,w=730*full/total;
 let s=T(40,109,total.toLocaleString("en-US")+" cell comparisons",18,ink,true)+R(40,124,w,40,blue)+R(40+w,124,730-w,40,green)+T(40+w/2,149,full.toLocaleString("en-US")+" full cells",15,"white",true,"middle")+T(40+w+(730-w)/2,149,clipN.toLocaleString("en-US"),14,"white",true,"middle");
 s+=T(40,209,"Full cells within tolerance")+T(40,241,full.toLocaleString("en-US")+" / "+full.toLocaleString("en-US"),25,blue,true)+T(420,209,"Clipped cells within tolerance")+T(420,241,clipPass.toLocaleString("en-US")+" / "+clipN.toLocaleString("en-US"),25,green,true)+T(420,267,(clipN-clipPass)+" clipped cell exceeds "+m[4],14,amber,true);
 save("v11_cross_location","V11 | Three-location VIIRS agreement","Shanghai, Bao'an and Qimen; same exported app polygons",320,s,"Tolerance "+m[4]+" reflects CSV rounding, not sensor error; archived validation.");
 m=match(/Yanqing reports ([\d,]+)\/([\d,]+) matching final LISA classes/);const same=number(m[1]),n=number(m[2]),w2=750*same/n;
 s=T(40,109,"Final LISA class comparison",16,ink,true)+R(40,128,w2,32,blue)+R(40+w2,128,750-w2,32,amber)+T(40,205,same.toLocaleString("en-US")+" matching",23,blue,true)+T(450,205,(n-same).toLocaleString("en-US")+" differing",23,amber,true)+T(40,236,f(100*same/n,2)+"% agreement across "+n.toLocaleString("en-US")+" cells");
 save("a03_yanqing","A03 | Independent LISA classification","Yanqing field comparison; rounded NTL and independent seed",285,s,"Class disagreement is not automatically an arithmetic failure or a sensor error.");
 const gl=report.split("\n").find(l=>l.includes("| A04.")&&l.includes("Exact hand cases"));if(!gl)throw Error("Missing A04 evidence");
 const cases=[...gl.matchAll(/`\[([0-9,]+)\]` gives ([\d.]+)/g)].map(v=>[v[1],Number(v[2])]);if(cases.length!==3)throw Error("Unexpected Gini hand-case count");
 s="";cases.forEach(([label,v],i)=>{let y=102+i*45;s+=T(205,y+17,"["+label+"]",15,ink,false,"end")+R(222,y,Math.max(1,540*v/.6),24,[blue,green,amber][i])+T(229+540*v/.6,y+17,f(v,2),15,ink,true)});
 save("a04_gini","A04 | Gini hand-case oracles","Finite nonnegative arrays; archived numerical checks",285,s,"Empty and all-zero arrays return zero; invalid negative/nonfinite inputs raise an error.");
 m=match(/\| Spearman rho \| ([-\d.]+) \| ([-\d.]+) \|[\r\n]+\| Block-bootstrap 95% interval \| \[([-\d.]+), ([-\d.]+)\] \| \[([-\d.]+), ([-\d.]+)\] \|/);
 const vals=[["Built surface",+m[1],+m[3],+m[4]],["Population",+m[2],+m[5],+m[6]]],x=v=>210+(v+.3)/.65*550;s="";
 for(let i=0;i<=6;i++){let v=-.3+i*.1;s+=L(x(v),95,x(v),224)+T(x(v),245,f(v,1),12,muted,false,"middle")}
 s+=L(x(0),95,x(0),224,muted,1.5,"4 4");vals.forEach(([label,v,lo,hi],i)=>{let y=130+i*63,c=[blue,green][i];s+=T(195,y+5,label,15,ink,false,"end")+L(x(lo),y,x(hi),y,c,3)+L(x(lo),y-6,x(lo),y+6,c)+L(x(hi),y-6,x(hi),y+6,c)+D(x(v),y,c)+T(x(v),y-12,f(v),14,ink,true,"middle")});
 save("a08_ghsl","A08/A09 | GHSL agreement in Shanghai","715 eligible core cells; archived Spearman and block-bootstrap intervals",292,s,"Both archived intervals contain zero; association is inconclusive, not economic validation.");
 const real=g5.center_comparisons.filter(v=>v.source==="baoan_2020_ntl");s="";
 real.forEach((v,i)=>{let y=99+i*44,label={archived_ntl_selected:"Archived NTL center",geometry_only_centroid:"Geometry centroid",ntl_weighted_centroid:"NTL-weighted centroid",brightest_ntl_cell:"Brightest cell"}[v.center_method];if(!label)throw Error("Unknown center method");s+=T(230,y+17,label,15,ink,false,"end")+R(244,y,510*v.gradient_r2/.5,24,[blue,green,amber,purple][i])+T(251+510*v.gradient_r2/.5,y+17,f(v.gradient_r2),14,ink,true)});
 save("g05_gradient","G05 | Gradient fit depends on center","Bao'an 2020; same observed NTL and eligible core cells",328,s,"Horizontal bar: weighted gradient R²; no independent economic center benchmark.");
 s="";for(let i=0;i<2;i++){let x0=120+i*370;for(let row=0;row<3;row++)for(let col=0;col<3;col++)s+=R(x0+col*48,102+row*48,48,48,(row+col)%2?"#e8eff5":"#dce9f2","#8da9bc");let shift=i?24:0;for(let row=0;row<2;row++)for(let col=0;col<2;col++)s+=R(x0+col*48+shift,102+row*48+shift,48,48,"none",amber,'stroke-width="2" stroke-dasharray="6 3"');s+=T(x0+72,270,i?"Half-cell shift":"Aligned cells",15,ink,true,"middle")}
 save("g23_support_geometry","G23 | Shared raster support","Schematic: source pixel grid (solid) and analysis cells (dashed)",323,s,"Shifted neighboring cells share source pixels; no measured map or sensor PSF is depicted.");
 const ma=ind.synthetic.G22;s="";for(let i=0;i<4;i++)s+=R(55+i%2*66,104+Math.floor(i/2)*66,66,66,i===0?amber:"#e6edf2","#a6b9c6");s+=R(55,104,132,132,"none",blue,'stroke-width="3"')+T(121,258,"One of four fine cells is HH",13,ink,false,"middle")+T(265,134,"Coarse block with any fine HH overlap",16)+T(265,165,f(100*ma.any_overlap_block_fraction,0)+"%",27,blue,true)+T(265,203,"Actual intersecting HH area",16)+T(265,234,f(100*ma.actual_overlap_area_fraction,0)+"%",27,amber,true);
 save("g22_overlap","G22 | Block intersection vs area overlap","Synthetic coarse block with four equal-area fine cells",306,s,"The block-any-overlap fraction is not the actual overlapping HH area fraction.");
 return out;
}
Object.assign(figs,archivedFigures(fs.readFileSync(path.join(root,'evidence','README.md'),'utf8'),data.g5,data.csv));

const out=path.join(root,'figures');
if(!process.argv.includes('--verify'))fs.mkdirSync(out,{recursive:true});
for(const [name,svg] of Object.entries(figs)){const p=path.join(out,name);if(process.argv.includes('--verify')){if(fs.readFileSync(p,'utf8')!==svg)throw Error('Figure mismatch: '+name)}else fs.writeFileSync(p,svg);}
console.log('Verified/generated '+Object.keys(figs).length+' figures.');
