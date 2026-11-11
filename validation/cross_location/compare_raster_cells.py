#!/usr/bin/env python3
"""Independent VIIRS raster-to-polygon benchmark for a spatial-app export.

Inputs: exact GADM GeoJSON, Earth Engine annual median raster and spatial-app CSV.
No imports from the spatial-app implementation; reconstructs its clipped UTM lattice.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from rasterio.transform import array_bounds
from rasterio.windows import from_bounds
from shapely.geometry import box


def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def grid_from_boundary(path, size_m):
    boundary=gpd.read_file(path).to_crs('EPSG:4326')
    if boundary.empty:
        raise ValueError('Empty boundary')
    west,south,east,north=boundary.total_bounds
    # spatial-app uses midpoint of the source bounding box, not feature centroid.
    lon=(west+east)/2;lat=(south+north)/2
    zone=min(60,max(1,math.floor((lon+180)/6)+1))
    epsg=(32600 if lat>=0 else 32700)+zone
    utm=boundary.to_crs(epsg=epsg)
    xmin,ymin,xmax,ymax=utm.total_bounds
    x0=math.floor(xmin/size_m)*size_m-size_m
    y0=math.floor(ymin/size_m)*size_m-size_m
    xs=np.arange(x0,xmax+2*size_m,size_m)
    ys=np.arange(y0,ymax+2*size_m,size_m)
    xx,yy=np.meshgrid(xs,ys)
    polygons=shapely.box(xx.ravel(),yy.ravel(),xx.ravel()+size_m,yy.ravel()+size_m)
    grid=gpd.GeoDataFrame(geometry=polygons,crs=f'EPSG:{epsg}')
    grid=gpd.clip(grid,utm,keep_geom_type=True).reset_index(drop=True)
    grid=grid[~grid.geometry.is_empty&grid.geometry.notna()].reset_index(drop=True)
    grid['area_km2']=grid.geometry.area/1e6
    grid=grid[grid.area_km2>0].reset_index(drop=True)
    grid.insert(0,'grid_id',np.arange(len(grid),dtype=np.int64))
    return grid,epsg,len(xx.ravel())


def independent_zonal(grid,raster):
    polygons=grid.to_crs('EPSG:4326').geometry
    means=np.full(len(grid),np.nan)
    with rasterio.open(raster) as ds:
        if ds.crs.to_epsg()!=4326:
            raise ValueError('Reference TIFF must be EPSG:4326; received '+str(ds.crs))
        arr=ds.read(1,masked=True)
        pixels={}
        def pixel(r,c):
            if (r,c) not in pixels:
                pix_tf=ds.transform*rasterio.Affine.translation(c,r)
                l,b,rr,t=array_bounds(1,1,pix_tf)
                pixels[r,c]=box(l,b,rr,t)
            return pixels[r,c]
        for i,geom in enumerate(polygons):
            win=from_bounds(*geom.bounds,transform=ds.transform)
            c0=max(0,math.floor(win.col_off)-1)
            c1=min(ds.width,math.ceil(win.col_off+win.width)+1)
            r0=max(0,math.floor(win.row_off)-1)
            r1=min(ds.height,math.ceil(win.row_off+win.height)+1)
            total=0.0;weight=0.0
            for row in range(r0,r1):
                for col in range(c0,c1):
                    val=arr[row,col]
                    if np.ma.is_masked(val) or not np.isfinite(val):
                        continue
                    pix=pixel(row,col)
                    if not geom.intersects(pix):continue
                    area=geom.intersection(pix).area
                    if area>0:
                        total+=max(float(val),0.0)*area
                        weight+=area
            if weight>0:
                means[i]=total/weight
    return means


def run(args):
    app=pd.read_csv(args.csv)
    required={'grid_id','area_km2','ntl_mean'}
    if not required.issubset(app.columns):
        raise ValueError(f'App CSV lacks columns: {required-set(app.columns)}')
    if app.grid_id.duplicated().any():raise ValueError('Duplicate grid_id')
    grid,epsg,bbox_size=grid_from_boundary(args.boundary,args.cell_size)
    if len(grid)!=len(app):
        raise ValueError(f'Grid count mismatch: reconstructed={len(grid)}, app={len(app)}; verify boundary and cell size')
    joined=grid[['grid_id','area_km2']].merge(app[['grid_id','area_km2','ntl_mean']],on='grid_id',how='outer',suffixes=('_reference','_app'),validate='one_to_one')
    if joined.isna().any().any():raise ValueError('Unmatched grid IDs or missing area/NTL values')
    area_errors=(joined.area_km2_reference-joined.area_km2_app).abs()
    if area_errors.max()>5e-5:
        raise ValueError(f'Grid geometry/ordering mismatch (max area diff {area_errors.max()})')
    reference=independent_zonal(grid,args.raster)
    out=joined.copy()
    out['ntl_reference']=reference
    out['error']=out.ntl_reference-out.ntl_mean
    out['abs_error']=out.error.abs()
    out['is_edge_masked']=(out.area_km2_reference<0.99*(args.cell_size/1000)**2)
    out.to_csv(args.out_csv,index=False)
    valid=np.isfinite(reference)&np.isfinite(out.ntl_mean.to_numpy())
    errors=out.abs_error.to_numpy()
    pass_cells=int((valid&(errors<=args.tolerance+1e-9)).sum())
    n_valid=int(valid.sum())
    metrics={
        'grid_count':len(grid),'bounding_grid_cells':bbox_size,'epsg_utm':epsg,
        'grid_area_km2':float(grid.area_km2.sum()),'edge_masked':int(out.is_edge_masked.sum()),
        'n_comparable':n_valid,'pass_cells':pass_cells,'n_fail_or_missing':len(grid)-pass_cells,
        'tolerance':args.tolerance,'mae':float(np.nanmean(errors)),
        'max_abs_error':float(np.nanmax(errors)),
        'pearson':float(np.corrcoef(out.ntl_mean[valid],reference[valid])[0,1]) if n_valid>2 else None,
        'inputs_sha256':{k:sha256(getattr(args,k)) for k in ('boundary','raster','csv')},
        'passed':pass_cells==len(grid),
        'note':'Raster benchmark only; does not independently test Local Moran, FDR, GHSL, or economic validity.'}
    Path(args.out_json).write_text(json.dumps(metrics,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(metrics,indent=2,ensure_ascii=False))
    return 0 if metrics['passed'] else 2

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--boundary',required=True,type=Path)
    ap.add_argument('--raster',required=True,type=Path)
    ap.add_argument('--csv',required=True,type=Path)
    ap.add_argument('--cell-size',type=int,default=500)
    ap.add_argument('--tolerance',type=float,default=0.00005)
    ap.add_argument('--out-csv',type=Path,default=Path('cell_comparison.csv'))
    ap.add_argument('--out-json',type=Path,default=Path('validation_metrics.json'))
    raise SystemExit(run(ap.parse_args()))