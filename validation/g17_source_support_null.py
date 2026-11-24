"""Source-independence null on a complete 8x8 window.
Cell permutation and source-aware reference test distinct null hypotheses.
Usage: python validation/g17_source_support_null.py RASTER GEOJSON
"""
import sys,json
import numpy as np
import geopandas as gpd
import rasterio
from g20_g23_raster_audit import extract, area, file_sha

def run(raster,geo):
    g=gpd.read_file(geo).sort_values('grid_id').reset_index(drop=True)
    u=g.to_crs(32650); gs=g.geometry.to_numpy()
    with rasterio.open(raster) as src:
        a,p,s,W,v=extract(gs,src)
    ga=np.array([area(x) for x in gs])
    eligible=(u.area.to_numpy()>=.99*500**2)&np.isfinite(a)&(s/ga>=.999)
    cx=np.floor(u.geometry.centroid.x.to_numpy()/500).astype(int)
    cy=np.floor(u.geometry.centroid.y.to_numpy()/500).astype(int)
    key={(cx[i],cy[i]):i for i in np.flatnonzero(eligible)}
    origin=next((x,y) for x,y in sorted(key) if all((x+dx,y+dy) in key for dx in range(8) for dy in range(8)))
    idx=np.array([key[(origin[0]+x,origin[1]+y)] for x in range(8) for y in range(8)])
    W=W[idx]; used=np.unique(W.indices); W=W[:,used]
    W=W.multiply(1/np.asarray(W.sum(axis=1)).ravel()[:,None]).tocsr()
    nb=[np.array([a*8+b for a in range(max(0,x-1),min(8,x+2)) for b in range(max(0,y-1),min(8,y+2)) if (a,b)!=(x,y)]) for x in range(8) for y in range(8)]
    rng=np.random.default_rng(171723); R=999; B=400
    def draw(n):
        data=(W@rng.normal(size=(W.shape[1],n))).T
        z=data-data.mean(axis=1,keepdims=True); z/=z.std(axis=1,ddof=1,keepdims=True)
        I=np.column_stack([z[:,i]*z[:,nbs].mean(axis=1) for i,nbs in enumerate(nb)])
        return z,I
    _,ref=draw(R); z,obs=draw(B)
    psrc=np.minimum(1,2*(1+np.minimum((ref[None,:,:]>=obs[:,None,:]-1e-12).sum(axis=1),
                                      (ref[None,:,:]<=obs[:,None,:]+1e-12).sum(axis=1)))/(R+1))
    pcell=np.empty_like(obs)
    for i,nbs in enumerate(nb):
        pool=np.delete(np.arange(64),i)
        # Uniform draws without replacement; common random numbers across test fields.
        picks=np.array([rng.choice(pool,len(nbs),replace=False) for _ in range(R)])
        sim=z[:,i,None]*z[:,picks].mean(axis=2)
        pcell[:,i]=np.minimum(1,2*(1+np.minimum((sim>=obs[:,i,None]-1e-12).sum(axis=1),
                                              (sim<=obs[:,i,None]+1e-12).sum(axis=1)))/(R+1))
    def counts(p,kind):
        if kind=='raw': return (p<=.05).sum(axis=1)
        sortedp=np.sort(p,axis=1); thresholds=np.arange(1,65)*.05/64
        if kind=='BY': thresholds/=np.sum(1/np.arange(1,65))
        return np.max(np.where(sortedp<=thresholds,np.arange(1,65),0),axis=1)
    out={}
    for name,p in [('cell_permutation',pcell),('source_reference',psrc)]:
        out[name]={'marginal_p_le_0_05':float((p<=.05).mean()),'policies':{}}
        for policy in ('raw','BH','BY'):
            k=counts(p,policy)
            out[name]['policies'][policy]={'any_rejection_count':int((k>0).sum()),
                'any_rejection_fraction':float((k>0).mean()),'mean_rejections':float(k.mean())}
    return {'source_sha256':{raster:file_sha(raster),geo:file_sha(geo)},'grid_origin_ix_iy':list(map(int,origin)),
            'grid_ids':g.grid_id.iloc[idx].astype(int).tolist(),'source_pixels':W.shape[1],
            'reference_draws':R,'test_draws':B,'seed':171723,'results':out,
            'limit':'Conditional cell permutation tests random placement of cell values, not source independence. Shared references make empirical rates conditional on the reference. One compact window, no field FDR guarantee.'}

if __name__=='__main__': print(json.dumps(run(*sys.argv[1:]),indent=2))
