"""Raster support, physical area and MAUP reference diagnostics.
Usage: python validation/g20_g23_raster_audit.py RASTER GEOJSON [--band 2] [--maup]
Requires numpy, geopandas, rasterio, shapely>=2.1, pyproj, scipy.
Uses owner-held source exports; not the application raster download path.
"""
import argparse, hashlib, json
from pathlib import Path
from contextlib import ExitStack
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import Window
from rasterio.merge import merge
import shapely as sh
from pyproj import Geod
from scipy.sparse import coo_matrix
from scipy.stats import spearmanr

GEOD=Geod(ellps='WGS84')

def area(g):
    if g.is_empty: return 0.
    if g.geom_type=='Polygon': return abs(GEOD.geometry_area_perimeter(sh.orient_polygons(g))[0])
    if hasattr(g,'geoms'): return sum(area(x) for x in g.geoms)
    return 0.

def summarize(x):
    x=np.asarray(x,float); x=x[np.isfinite(x)]
    return dict(n=len(x),mean=float(x.mean()),median=float(np.median(x)),p95=float(np.quantile(x,.95)),max=float(x.max())) if len(x) else {'n':0}

def file_sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def extract(geoms,src,band=1):
    v=src.read(band,masked=True).astype(float).filled(np.nan)
    v=np.maximum(v,0); t=src.transform
    if t.b or t.d or t.a<=0 or t.e>=0: raise ValueError('north-up raster required')
    rr,cc=np.indices(v.shape)
    px=sh.box(t.c+cc.ravel()*t.a,t.f+(rr.ravel()+1)*t.e,t.c+(cc.ravel()+1)*t.a,t.f+rr.ravel()*t.e)
    geoms=sh.buffer(sh.make_valid(np.asarray(geoms)),0)
    tree=sh.STRtree(px); a,b=tree.query(geoms,predicate='intersects')
    overlap=sh.intersection(geoms[a],px[b],grid_size=1e-11)
    angular=sh.area(overlap); keep=(angular>0)&np.isfinite(v.ravel()[b])
    a,b,overlap,angular=a[keep],b[keep],overlap[keep],angular[keep]
    phys=np.fromiter((area(g) for g in overlap),float,len(overlap))
    shape=(len(geoms),v.size)
    W=coo_matrix((angular,(a,b)),shape=shape).tocsr()
    P=coo_matrix((phys,(a,b)),shape=shape).tocsr()
    vals=np.nan_to_num(v.ravel())
    wa=np.asarray(W.sum(axis=1)).ravel(); pa=np.asarray(P.sum(axis=1)).ravel()
    def div(x,d): return np.divide(x,d,out=np.full(len(d),np.nan),where=d>0)
    return div(W@vals,wa),div(P@vals,pa),pa,W,v

def aligned_tile_check(src):
    with ExitStack() as stack:
        ds=[]
        for x in [0,src.width//2]:
            for y in [0,src.height//2]:
                w=Window(x,y,src.width//2 if x==0 else src.width-x,src.height//2 if y==0 else src.height-y)
                p=src.profile.copy(); p.update(width=int(w.width),height=int(w.height),transform=src.window_transform(w))
                m=stack.enter_context(MemoryFile()); d=stack.enter_context(m.open(**p))
                d.write(src.read(window=w)); ds.append(d)
        arr,tr=merge(ds,method='first'); original=src.read()
        v=np.isfinite(original)&(original!=src.nodata)
        v2=np.isfinite(arr)&(arr!=src.nodata)
        return {'same_transform':tr==src.transform,'same_valid_mask':bool(np.array_equal(v,v2)),
                'valid_values':int(v.sum()),'valid_values_equal':bool(np.array_equal(original[v],arr[v])),
                'max_abs_valid_difference':float(np.max(abs(original[v]-arr[v]))),
                'raw_mismatch_nan_equal':int(np.count_nonzero(~((original==arr)|(np.isnan(original)&np.isnan(arr)))))}

def run(raster,geo,band,do_maup):
    g=gpd.read_file(geo).sort_values('grid_id').reset_index(drop=True); gs=g.geometry.to_numpy()
    epsg=int(next(c for c in g if c.startswith('centroid_x_epsg')).split('epsg')[1])
    u=g.to_crs(epsg); planar=u.area.to_numpy(); geoarea=np.array([area(x) for x in gs])
    with rasterio.open(raster) as src:
        a,p,support,W,v=extract(gs,src,band)
        both=np.isfinite(a)&np.isfinite(p); complete=both&(support/geoarea>=.999)
        delta=np.abs(a-p); cov=support/geoarea
        out={'input_sha256':{Path(raster).name:file_sha(raster),Path(geo).name:file_sha(geo)},
             'raster_shape':list(src.shape),'transform':list(src.transform)[:6],'band':band,'cells':len(g),
             'complete_support_ge_0_999':int(complete.sum()),'support_fraction':summarize(cov),
             'G11_utm_vs_geodesic_relative_abs':summarize(abs(planar/geoarea-1)),
             'G21_abs_mean_difference':summarize(delta[both]),'G21_complete_abs_difference':summarize(delta[complete]),
             'G21_spearman':float(spearmanr(a[both],p[both]).statistic),
             'G21_SOL_on_supported_area':{'angular':float(np.sum(a[both]*support[both]/1e6)),
                                         'physical':float(np.sum(p[both]*support[both]/1e6))}}
        if do_maup:
            out['G20_offline_aligned_tiles']=aligned_tile_check(src)
            # Union of exported polygons, not an independent administrative boundary.
            region=sh.union_all(u.geometry.to_numpy()); x0,y0,x1,y1=region.bounds
            def grid(size,offset):
                xs=np.arange(np.floor((x0-offset)/size)*size+offset,x1,size)
                ys=np.arange(np.floor((y0-offset)/size)*size+offset,y1,size)
                x,y=np.meshgrid(xs,ys); boxes=sh.box(x.ravel(),y.ravel(),x.ravel()+size,y.ravel()+size)
                cl=sh.intersection(boxes,region); ok=sh.area(cl)>1e-4
                return cl[ok],x.ravel()[ok],y.ravel()[ok]
            ma=[]
            for size in [1000,1500,2000]:
                for off in [0,size/2]:
                    cl,x,y=grid(size,off)
                    wgs=gpd.GeoSeries(cl,crs=epsg).to_crs(4326).to_numpy()
                    ca,cp,cs,_,_=extract(wgs,src,band); valid=np.isfinite(cp)
                    row={'size':size,'offset_xy':off,'cells':len(cl),'supported':int(valid.sum()),
                         'physical_SOL':float(np.nansum(cp*cs/1e6)),'physical_mean':float(np.nansum(cp*cs)/cs.sum())}
                    if off==0:
                        ix=np.floor(u.geometry.centroid.x.to_numpy()/size).astype(int)
                        iy=np.floor(u.geometry.centroid.y.to_numpy()/size).astype(int)
                        keys={(int(round(xx/size)),int(round(yy/size))):i for i,(xx,yy) in enumerate(zip(x,y))}
                        agg=np.zeros(len(cl)); den=np.zeros(len(cl))
                        for j in range(len(g)):
                            k=keys.get((ix[j],iy[j]))
                            if k is not None and np.isfinite(p[j]):
                                agg[k]+=p[j]*support[j]; den[k]+=support[j]
                        pred=np.divide(agg,den,out=np.full(len(cl),np.nan),where=den>0)
                        ok=valid&np.isfinite(pred)
                        row['aligned_direct_vs_support_weighted_fine_abs']=summarize(abs(cp[ok]-pred[ok]))
                        row['aligned_support_area_relative_abs']=summarize(abs(cs[ok]-den[ok])/cs[ok])
                        row['aggregated_supported']=int((den>0).sum())
                    ma.append(row)
            out['G22_direct_grids']=ma
            core=(planar>=.99*500**2)&complete; idx=np.flatnonzero(core)
            mat=W[idx]; denom=np.asarray(mat.sum(axis=1)).ravel(); mat=mat.multiply(1/denom[:,None]).tocsr()
            cx=np.floor(u.geometry.centroid.x.to_numpy()[idx]/500).astype(int)
            cy=np.floor(u.geometry.centroid.y.to_numpy()[idx]/500).astype(int)
            key={(x,y):i for i,(x,y) in enumerate(zip(cx,cy))}
            edges=[(i,key[(x+dx,y+dy)]) for i,(x,y) in enumerate(zip(cx,cy))
                   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)] if (x+dx,y+dy) in key]
            ii,jj=np.array(edges).T
            shared=np.asarray(mat[ii].multiply(mat[jj]).sum(axis=1)).ravel()
            diag=np.asarray(mat.multiply(mat).sum(axis=1)).ravel(); corr=shared/np.sqrt(diag[ii]*diag[jj])
            rng=np.random.default_rng(20261125); sims=[]
            for rep in range(400):
                cell=mat@rng.normal(size=v.size); z=cell-cell.mean()
                sims.append(len(z)/len(ii)*np.sum(z[ii]*z[jj])/np.sum(z*z))
            out['G23_actual_support_null']={'cells':len(idx),'directed_rook_edges':len(ii),
                'share_edges_with_common_pixel':float((shared>0).mean()),'expected_pairwise_corr':summarize(corr),
                'moran_mean':float(np.mean(sims)),'moran_p025_p975':np.quantile(sims,[.025,.975]).tolist(),'replicates':sims}
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('raster'); p.add_argument('geojson')
    p.add_argument('--band',type=int,default=1); p.add_argument('--maup',action='store_true')
    a=p.parse_args(); print(json.dumps(run(a.raster,a.geojson,a.band,a.maup),indent=2))
