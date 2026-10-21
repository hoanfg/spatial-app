import streamlit as st
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
import os
import branca.colormap as cm

# 1. Streamlit UI Configuration
st.set_page_config(page_title="Spatial Grid System", layout="wide")
st.title("Spatial Grid Cutter Tool")

# 2. Load Static Shapefile Data
file_path = "data/gadm41_VNM_1.shp"

# Check data existence
if not os.path.exists(file_path):
    st.error(f"Data file not found at {file_path}. Please check the directory.")
    st.stop()

@st.cache_data # Cache data to prevent reloading during user interaction
def load_data():
    return gpd.read_file(file_path)

with st.spinner("Loading boundaries data..."):
    df_vietnam = load_data()

# 3. Sidebar Configuration
with st.sidebar:
    st.header("Input parameters")
    list_provinces = df_vietnam['NAME_1'].sort_values().unique()
    selected_province = st.selectbox("Please choose City/Province", list_provinces)
    
    cell_size = st.slider("Grid size (meters)", min_value=1000, max_value=5000, value=2000, step=1000)
    run_btn = st.button("Generate grid")

# --- SESSION STATE MANAGEMENT ---
# Store state to prevent rerun data loss when interacting with Folium
if run_btn:
    st.session_state['is_generated'] = True
    st.session_state['selected_prov'] = selected_province
    st.session_state['current_size'] = cell_size

# 4. Grid Cutting and Mock Data Generation
if st.session_state.get('is_generated', False):
    
    prov = st.session_state['selected_prov']
    size = st.session_state['current_size']
    
    with st.spinner(f"Processing mathematical operations and generating simulated data of {size}m for {prov}..."):
        # Filter boundary and reproject to UTM (meters) EPSG:32648 for Northern/Vietnam regional accuracy
        boundary = df_vietnam[df_vietnam['NAME_1'] == prov]
        boundary_utm = boundary.to_crs(epsg=32648)
        
        # Generate raw grid based on bounding box
        minx, miny, maxx, maxy = boundary_utm.total_bounds
        x_coords = np.arange(minx, maxx, size)
        y_coords = np.arange(miny, maxy, size)
        
        grid_cells = []
        for x in x_coords:
            for y in y_coords:
                poly = Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)])
                grid_cells.append(poly)
                
        raw_grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs=boundary_utm.crs)
        
        # Clip grid to administrative boundary and calculate actual area
        clipped_grid = gpd.clip(raw_grid, boundary_utm)
        clipped_grid['area_km2'] = clipped_grid.geometry.area / 1e6
        
        # --- MOCK ECONOMIC DATA GENERATION ---
        # 1. Identify Border Cells vs Core Cells
        standard_area = (size / 1000) ** 2
        clipped_grid['cell_type'] = np.where(clipped_grid['area_km2'] < (standard_area * 0.95), 'Border', 'Standard (Core)')
        
        # 2. Find Provincial Centroid (CBD proxy)
        prov_centroid = boundary_utm.geometry.centroid.iloc[0]
        
        # 3. Calculate distance from each cell to centroid (in meters)
        clipped_grid['dist_to_center'] = clipped_grid.geometry.centroid.distance(prov_centroid)
        
        # 4. Convert distance to Mock NTL Score (0-100) using normal distribution noise
        max_dist = clipped_grid['dist_to_center'].max()
        np.random.seed(42) # Fix seed for consistent map rendering
        noise = np.random.normal(0, 5, len(clipped_grid)) 
        
        clipped_grid['mock_ntl_score'] = 100 * (1 - (clipped_grid['dist_to_center'] / max_dist)) + noise
        clipped_grid['mock_ntl_score'] = clipped_grid['mock_ntl_score'].clip(0, 100).round(2)
        
        # Reproject back to WGS84 for web map visualization
        clipped_grid_wgs84 = clipped_grid.to_crs(epsg=4326)
        
        st.success(f"Complete! Generated {len(clipped_grid)} spatial grid cells with simulated economic data.")

        # 5. Render Heatmap Visualization
        # Use iloc[0] to prevent Pandas future warnings
        center_y = boundary.geometry.centroid.y.iloc[0]
        center_x = boundary.geometry.centroid.x.iloc[0]
        
        m = folium.Map(location=[center_y, center_x], zoom_start=10, tiles='OpenStreetMap')
        
        # Initialize Colormap (Dark Blue to Yellow)
        colormap = cm.LinearColormap(
            colors=['#0d0887', '#7a0403', '#cb4621', '#f89441', '#f0f921'], 
            vmin=0, vmax=100,
            caption='Light intensity / Economic simulation (0-100)'
        )
        m.add_child(colormap)
        
        # Map GeoJSON layer with conditional styling
        folium.GeoJson(
            clipped_grid_wgs84,
            style_function=lambda feature: {
                'fillColor': colormap(feature['properties']['mock_ntl_score']),
                'color': '#ffffff' if feature['properties']['cell_type'] == 'Standard (Core)' else '#ff0000',
                'weight': 0.5,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['mock_ntl_score', 'area_km2', 'cell_type'], 
                aliases=['Economic score (Mock NTL):', 'Actual area (km2):', 'Grid classification:'],
                labels=True
            )
        ).add_to(m)
        
        # Prevent silent reruns from Folium callbacks
        st_folium(m, width=1000, height=600, returned_objects=[])

        # 6. Data Export Module
        st.markdown("### 📥 Data export")
        st.info("This spatial grid infrastructure is ready for download and integration into econometric models (Stata, R, QGIS) or merging with satellite data.")
        
        col1, col2 = st.columns(2)
        
        # GeoJSON Export (For Spatial Analysis/QGIS)
        geojson_data = clipped_grid_wgs84.to_json()
        with col1:
            st.download_button(
                label="Download grid map (GeoJSON)",
                data=geojson_data,
                file_name=f"{prov}_Grid_{size}m.geojson",
                mime="application/geo+json"
            )
        
        # CSV Export (For Stata/Statistical Analysis)
        df_export = clipped_grid_wgs84.copy()
        df_export['centroid_lon'] = df_export.geometry.centroid.x
        df_export['centroid_lat'] = df_export.geometry.centroid.y
        df_csv = df_export.drop(columns=['geometry']).to_csv(index=False).encode('utf-8')
        
        with col2:
            st.download_button(
                label="Download data table (CSV)",
                data=df_csv,
                file_name=f"{prov}_Data_{size}m.csv",
                mime="text/csv"
            )
