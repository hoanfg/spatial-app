import streamlit as st
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
import os
import branca.colormap as cm
import ee
from rasterstats import zonal_stats
import tempfile
import json

# ==========================================
# 1. UI CONFIGURATION & AUTHENTICATION
# ==========================================
st.set_page_config(page_title="Spatial Econometrics Grid", layout="wide")
st.title("Spatial Grid Infrastructure & NTL Extractor")

@st.cache_resource
def init_gee():
    """Initialize Google Earth Engine using Streamlit Secrets"""
    try:
        service_account = st.secrets["gcp_service_account"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(dict(service_account), tmp)
            tmp_path = tmp.name
            
        credentials = ee.ServiceAccountCredentials(service_account["client_email"], tmp_path)
        ee.Initialize(credentials)
        os.remove(tmp_path)
        return True
    except Exception as e:
        st.error(f"GEE Authentication Error: Please configure Streamlit Secrets. Details: {e}")
        return False

# ==========================================
# 2. DATA LOADING (STATIC BOUNDARIES)
# ==========================================
file_path = "data/gadm41_VNM_1.shp"

if not os.path.exists(file_path):
    st.error(f"Shapefile not found at {file_path}. Ensure the 'data' directory contains all GADM files (.shp, .shx, .dbf, .prj).")
    st.stop()

@st.cache_data
def load_boundaries():
    return gpd.read_file(file_path)

with st.spinner("Loading administrative boundaries..."):
    df_boundaries = load_boundaries()

# ==========================================
# 3. SIDEBAR PARAMETERS & PIPELINE ROUTING
# ==========================================
with st.sidebar:
    st.header("1. Spatial Parameters")
    list_provinces = df_boundaries['NAME_1'].sort_values().unique()
    selected_prov = st.selectbox("Select Province/City", list_provinces)
    cell_size = st.slider("Grid Resolution (meters)", min_value=1000, max_value=5000, value=2000, step=1000)
    
    st.markdown("---")
    st.header("2. Raster Data Source")
    data_source = st.radio(
        "Select Nighttime Lights (NTL) Source:", 
        ["Mock Data (UI Testing)", "Local GeoTIFF Upload (Fallback)", "Google Earth Engine (Cloud API)"]
    )
    
    uploaded_tif = None
    if data_source == "Local GeoTIFF Upload (Fallback)":
        uploaded_tif = st.file_uploader("Upload VIIRS/DMSP GeoTIFF (< 50MB)", type=['tif', 'tiff'])
        if uploaded_tif:
            st.success("GeoTIFF loaded into temporary memory.")
            
    run_btn = st.button("Execute Pipeline")

# Session state to prevent Folium reruns
if run_btn:
    st.session_state['is_executed'] = True
    st.session_state['prov'] = selected_prov
    st.session_state['size'] = cell_size
    st.session_state['source'] = data_source

# ==========================================
# 4. CORE PIPELINE EXECUTION
# ==========================================
if st.session_state.get('is_executed', False):
    
    prov = st.session_state['prov']
    size = st.session_state['size']
    source = st.session_state['source']
    
    with st.spinner(f"Executing Spatial Operations for {prov}..."):
        
        # --- PHASE 1: SPATIAL GRID GENERATION ---
        # Reproject to UTM Zone 48N (EPSG:32648) for accurate metric calculations
        boundary = df_boundaries[df_boundaries['NAME_1'] == prov]
        boundary_utm = boundary.to_crs(epsg=32648)
        
        minx, miny, maxx, maxy = boundary_utm.total_bounds
        x_coords = np.arange(minx, maxx, size)
        y_coords = np.arange(miny, maxy, size)
        
        grid_cells = [Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)]) 
                      for x in x_coords for y in y_coords]
                
        raw_grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs=boundary_utm.crs)
        
        # Clip grid and calculate physical area
        clipped_grid = gpd.clip(raw_grid, boundary_utm)
        clipped_grid['area_km2'] = clipped_grid.geometry.area / 1e6
        
        # Identify MAUP Border Cells (< 95% of standard area)
        standard_area = (size / 1000) ** 2
        clipped_grid['cell_type'] = np.where(clipped_grid['area_km2'] < (standard_area * 0.95), 'Border', 'Standard (Core)')
        
        # Reproject to WGS84 (EPSG:4326) for Web Mapping and Satellite Overlay
        grid_wgs84 = clipped_grid.to_crs(epsg=4326)
        
        # --- PHASE 2: ZONAL STATISTICS & RASTER EXTRACTION ---
        
        # Route A: Distance-Decay Mock Data
        if source == "Mock Data (UI Testing)":
            prov_centroid = clipped_grid.geometry.centroid.iloc[0]
            clipped_grid['dist'] = clipped_grid.geometry.centroid.distance(prov_centroid)
            max_dist = clipped_grid['dist'].max()
            
            np.random.seed(42)
            noise = np.random.normal(0, 5, len(clipped_grid))
            
            grid_wgs84['ntl_mean'] = (100 * (1 - (clipped_grid['dist'] / max_dist)) + noise).clip(0, 100).round(2)

        # Route B: Local GeoTIFF Processing (rasterstats)
        elif source == "Local GeoTIFF Upload (Fallback)":
            if uploaded_tif is None:
                st.error("Pipeline Halted: Missing GeoTIFF file.")
                st.stop()
                
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp_tif:
                tmp_tif.write(uploaded_tif.getvalue())
                tmp_tif_path = tmp_tif.name
            
            stats = zonal_stats(
                grid_wgs84, 
                tmp_tif_path, 
                stats="mean", 
                geojson_out=False, 
                nodata=-9999
            )
            
            grid_wgs84['ntl_mean'] = [round(s['mean'], 2) if s['mean'] is not None else 0 for s in stats]
            os.remove(tmp_tif_path)

        # Route C: Cloud Computing (Google Earth Engine)
        elif source == "Google Earth Engine (Cloud API)":
            if not init_gee():
                st.stop()
                
            features = []
            for _, row in grid_wgs84.iterrows():
                geom_dict = row.geometry.__geo_interface__
                geom = ee.Geometry(geom_dict)
                features.append(ee.Feature(geom))
            ee_fc = ee.FeatureCollection(features)
            
            viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG") \
                        .filterDate('2022-01-01', '2022-12-31') \
                        .select('avg_rad') \
                        .median()
                        
            reduced = viirs.reduceRegions(
                collection=ee_fc,
                reducer=ee.Reducer.mean(),
                scale=500
            )
            
            gee_results = reduced.getInfo()
            mean_values = [feat['properties'].get('mean', 0) for feat in gee_results['features']]
            grid_wgs84['ntl_mean'] = [round(v, 2) if v is not None else 0 for v in mean_values]

        st.success(f"Pipeline Completed: Processed {len(grid_wgs84)} spatial grid cells.")

        # ==========================================
        # 5. VISUALIZATION & EXPORT
        # ==========================================
        
        # Dynamic Colormap scaling based on extracted data
        vmax_val = grid_wgs84['ntl_mean'].max()
        vmax_val = vmax_val if vmax_val > 0 else 1 
        
        center_y = boundary.geometry.centroid.y.iloc[0]
        center_x = boundary.geometry.centroid.x.iloc[0]
        
        m = folium.Map(location=[center_y, center_x], zoom_start=10, tiles='OpenStreetMap')
        
        colormap = cm.LinearColormap(
            colors=['#0d0887', '#7a0403', '#cb4621', '#f89441', '#f0f921'], 
            vmin=0, vmax=vmax_val,
            caption='NTL Intensity (Mean)'
        )
        m.add_child(colormap)
        
        folium.GeoJson(
            grid_wgs84,
            style_function=lambda feature: {
                'fillColor': colormap(feature['properties']['ntl_mean']),
                'color': '#ffffff' if feature['properties']['cell_type'] == 'Standard (Core)' else '#ff0000',
                'weight': 0.5,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['ntl_mean', 'area_km2', 'cell_type'], 
                aliases=['NTL Intensity (Mean):', 'Actual Area (km2):', 'Grid Type:'],
                labels=True
            )
        ).add_to(m)
        
        st_folium(m, width=1000, height=600, returned_objects=[])

        # Data Export Module
        st.markdown("### 📥 Data Export Engine")
        
        col1, col2 = st.columns(2)
        
        geojson_data = grid_wgs84.to_json()
        with col1:
            st.download_button(
                label="Download Spatial Data (GeoJSON)",
                data=geojson_data,
                file_name=f"{prov}_Grid_{size}m.geojson",
                mime="application/geo+json"
            )
        
        df_export = grid_wgs84.copy()
        df_export['centroid_lon'] = df_export.geometry.centroid.x
        df_export['centroid_lat'] = df_export.geometry.centroid.y
        df_csv = df_export.drop(columns=['geometry']).to_csv(index=False).encode('utf-8')
        
        with col2:
            st.download_button(
                label="Download Tabular Data (CSV)",
                data=df_csv,
                file_name=f"{prov}_Data_{size}m.csv",
                mime="text/csv"
            )
