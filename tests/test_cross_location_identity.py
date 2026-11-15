"""Reject same-area ID swaps before independent raster comparison."""
import importlib.util
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

SCRIPT = Path(__file__).parents[1] / 'validation/cross_location/compare_raster_cells.py'
spec = importlib.util.spec_from_file_location('compare_raster_cells', SCRIPT)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def test_centroid_identity_rejects_same_area_swaps():
    grid = gpd.GeoDataFrame(
        {'grid_id': [10, 11], 'area_km2': [0.25, 0.25]},
        geometry=[box(500000, 4000000, 500500, 4000500),
                  box(500500, 4000000, 501000, 4000500)], crs='EPSG:32650',
    )
    centers = grid.geometry.centroid
    geographic = gpd.GeoSeries(centers, crs=grid.crs).to_crs(4326)
    app = pd.DataFrame({
        'grid_id': grid.grid_id,
        'centroid_lon': np.round(geographic.x, 6),
        'centroid_lat': np.round(geographic.y, 6),
        'centroid_x_epsg32650': np.round(centers.x, 1),
        'centroid_y_epsg32650': np.round(centers.y, 1),
    })
    errors = compare.verify_grid_identity(grid, app, 32650)
    assert max(errors.values()) <= 0.051

    swapped = app.copy()
    swapped.loc[:, 'centroid_x_epsg32650'] = swapped['centroid_x_epsg32650'].iloc[::-1].to_numpy()
    with pytest.raises(ValueError, match='Grid identity mismatch at grid_id='):
        compare.verify_grid_identity(grid, swapped, 32650)

    with pytest.raises(ValueError, match='lacks centroid identity columns'):
        compare.verify_grid_identity(grid, app.drop(columns='centroid_lon'), 32650)
